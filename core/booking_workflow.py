"""Booking edits and reviews share the same complete before/after record."""
from datetime import date, time
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
from .models import Appointment, Notifications, User
from .permissions import user_is_admin

BOOKING_FIELDS = ('date', 'time', 'end_time', 'price', 'service', 'notes',
                  'employee', 'client_id', 'deposit_required', 'deposit_paid',
                  'deposit_amount', 'status', 'requires_approval')


def snapshot(appointment):
    return {
        'date': appointment.date.isoformat(), 'time': appointment.time.isoformat(),
        'end_time': appointment.end_time.isoformat(), 'price': str(appointment.price),
        'service': appointment.service.name, 'notes': appointment.notes or '',
        'employee': appointment.employee_id, 'client_id': appointment.client_id,
        'deposit_required': appointment.deposit_required,
        'deposit_paid': appointment.deposit_paid,
        'deposit_amount': str(appointment.deposit_amount) if appointment.deposit_amount is not None else None,
        'status': appointment.status, 'requires_approval': appointment.requires_approval,
        'client': str(appointment.client),
        'artist': appointment.employee.get_full_name() or appointment.employee.username,
    }


def lock_artists(*ids):
    valid = set()
    for value in ids:
        try:
            valid.add(int(value))
        except (TypeError, ValueError):
            continue  # The serializer reports malformed selections.
    list(User.objects.select_for_update().filter(pk__in=valid).order_by('pk'))


def check_conflicts(data, instance=None):
    """Current bookings and the original slot of an unreviewed move reserve time."""
    employee = data.get('employee', getattr(instance, 'employee', None))
    day = data.get('date', getattr(instance, 'date', None))
    start = data.get('time', getattr(instance, 'time', None))
    end = data.get('end_time', getattr(instance, 'end_time', None))
    state = data.get('status', getattr(instance, 'status', 'confirmed'))
    if not all((employee, day, start, end)) or state in ('canceled', 'no_show'):
        return
    own_id = getattr(instance, 'pk', None)
    current = Appointment.objects.filter(employee=employee, date=day, time__lt=end,
                                         end_time__gt=start).exclude(status__in=('canceled', 'no_show'))
    if own_id:
        current = current.exclude(pk=own_id)
    if current.exists():
        raise ValidationError({'time': 'This artist already has an appointment during that time.'})
    pending = Notifications.objects.filter(status='pending', action='updated').exclude(appointment_id=own_id)
    for notice in pending.select_related('appointment'):
        previous = notice.previous_details or {}
        artist_id = previous.get('employee', getattr(notice.appointment, 'employee_id', None))
        if artist_id != employee.pk or previous.get('date') != day.isoformat():
            continue
        try:
            old_start = time.fromisoformat(previous['time'])
            old_end = time.fromisoformat(previous['end_time'])
        except (KeyError, TypeError, ValueError):
            continue
        if old_start < end and old_end > start:
            raise ValidationError({'time': 'That time is reserved while an earlier appointment change awaits review.'})


@transaction.atomic
def update_booking(request, pk):
    from .serializers import AppointmentSerializer
    queryset = Appointment.objects.all()
    is_admin = user_is_admin(request.user)
    if not is_admin:
        queryset = queryset.filter(employee=request.user)
    appointment = get_object_or_404(queryset, pk=pk)
    data = request.data.copy()
    lock_artists(appointment.employee_id, data.get('employee') if is_admin else request.user.pk)
    appointment = queryset.select_for_update().get(pk=pk)
    previous = snapshot(appointment)
    notice = Notifications.objects.filter(appointment=appointment, status='pending',
                                           action__in=('created', 'updated')).order_by('pk').first()
    status_only = set(data) == {'status'}
    direct_status = status_only and data.get('status') in ('completed', 'no_show', 'canceled')
    if is_admin:
        data.setdefault('status', appointment.status)
        data.setdefault('requires_approval', appointment.requires_approval)
        if status_only:
            data['requires_approval'] = False
    elif direct_status:
        if appointment.requires_approval or appointment.status == 'pending':
            raise ValidationError({'status': 'The booking must be approved before its outcome can be recorded.'})
        data['requires_approval'] = False
    else:
        data.update(employee=request.user.pk, status='pending', requires_approval=True)
    serializer = AppointmentSerializer(appointment, data=data, partial=True, context={'request':request})
    serializer.is_valid(raise_exception=True)
    appointment = serializer.save()
    current = snapshot(appointment)
    if not is_admin and not direct_status:
        original = (notice.previous_details if notice else None) or previous
        diff = {key:{'old':original.get(key), 'new':value} for key,value in current.items()
                if key not in ('status', 'requires_approval') and original.get(key) != value}
        if notice:
            notice.changes = diff
            notice.timestamp = now()
            notice.save(update_fields=['changes', 'timestamp'])
        else:
            Notifications.objects.create(employee=request.user, appointment=appointment,
                action='updated', changes=diff, previous_details=original, status='pending')
    elif direct_status and notice:
        Notifications.objects.filter(appointment=appointment, status='pending').update(status='approved')
    elif direct_status and data.get('status') == 'no_show' and previous['status'] != 'no_show':
        Notifications.objects.create(employee=request.user, appointment=appointment, action='no_show',
            changes={'status':{'old':previous['status'], 'new':'no_show'}}, status='approved')
    return AppointmentSerializer(appointment, context={'request':request}).data


@transaction.atomic
def review_booking(request, pk, approve):
    from .serializers import AppointmentSerializer
    notice = get_object_or_404(Notifications, pk=pk)
    desired = 'approved' if approve else 'denied'
    if notice.status != 'pending':
        if notice.status == desired:
            return  # A repeated click must not alter an already-reviewed booking.
        raise ValidationError({'error':'This request has already been reviewed.'})
    appointment = notice.appointment
    if appointment:
        previous = notice.previous_details or {}
        lock_artists(appointment.employee_id, previous.get('employee'))
        notice = Notifications.objects.select_for_update().get(pk=pk)
        if notice.status != 'pending':
            if notice.status == desired:
                return
            raise ValidationError({'error':'This request has already been reviewed.'})
        appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
        if approve:
            prior_status = previous.get('status')
            state = prior_status if prior_status in ('completed','canceled','no_show') else 'confirmed'
            if notice.action == 'no_show':
                state = appointment.status  # Compatibility with old outcome notifications.
            values = {'status':state, 'requires_approval':False}
        elif previous:
            values = {key:previous[key] for key in BOOKING_FIELDS if key in previous}
            values.setdefault('status', 'confirmed')
            values.setdefault('requires_approval', False)
        else:
            values = {'status':'canceled', 'requires_approval':False}
        serializer = AppointmentSerializer(appointment, data=values, partial=True, context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
    notice.status = desired
    notice.save(update_fields=['status'])
