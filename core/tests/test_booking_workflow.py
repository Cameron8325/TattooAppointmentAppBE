from datetime import timedelta
from decimal import Decimal
from django.urls import reverse
from django.test import override_settings
from django.utils.timezone import localdate, now
from core.models import Appointment, ClientProfile, Notifications
from core.tests.test_views import ViewTestBase


class BookingWorkflowTests(ViewTestBase):
    def setUp(self):
        super().setUp()
        self.appointment.status = 'confirmed'
        self.appointment.deposit_required = True
        self.appointment.deposit_paid = True
        self.appointment.deposit_amount = Decimal('50.00')
        self.appointment.save()
        self.url = reverse('reschedule-appointment', kwargs={'pk':self.appointment.pk})
        self.api.force_authenticate(user=self.admin)

    def test_notes_on_completed_visit_preserve_completed_work(self):
        self.appointment.status = 'completed'
        self.appointment.save()
        result = self.api.patch(self.url, {'notes':'Corrected notes'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'completed')
        self.assertEqual(self.appointment.notes, 'Corrected notes')
        self.assertEqual(self.appointment.price, Decimal('150.00'))

    def test_manager_artist_reassignment_is_saved(self):
        result = self.api.patch(self.url, {'employee':self.other_employee.pk}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.employee_id, self.other_employee.pk)

    def test_artist_overlap_rejected_but_touching_slots_allowed(self):
        payload = self.appointment_payload(date=self.appointment.date.isoformat(), time='14:30:00', end_time='15:30:00')
        result = self.api.post(reverse('appointment-list'), payload, format='json')
        self.assertEqual(result.status_code, 400, result.data)
        result = self.api.post(reverse('appointment-list'), {**payload, 'time':'15:00:00'}, format='json')
        self.assertEqual(result.status_code, 201, result.data)

    def test_direct_detail_endpoint_cannot_bypass_employee_review(self):
        self.api.force_authenticate(user=self.employee)
        result = self.api.patch(reverse('appointment-detail', kwargs={'pk':self.appointment.pk}), {'notes':'Artist edit'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.appointment.refresh_from_db()
        self.assertTrue(self.appointment.requires_approval)
        self.assertTrue(Notifications.objects.filter(appointment=self.appointment, status='pending').exists())

    def test_decline_restores_client_deposit_price_and_original_status_after_repeated_edits(self):
        other_client = ClientProfile.objects.create(first_name='Other',last_name='Client',email='other@example.com',phone='2025550101',employee=self.employee)
        self.api.force_authenticate(user=self.employee)
        result = self.api.patch(self.url, {'client_id':other_client.pk,'price':'250.00','deposit_paid':False,'deposit_amount':'25.00'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        result = self.api.patch(self.url, {'price':'200.00','notes':'Second edit'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        notice = Notifications.objects.get(appointment=self.appointment, status='pending')
        self.assertEqual(notice.changes['price']['old'], '150.00')
        self.assertEqual(notice.changes['price']['new'], '200.00')
        self.api.force_authenticate(user=self.admin)
        result = self.api.post(reverse('decline-notification', kwargs={'pk':notice.pk}))
        self.assertEqual(result.status_code, 200, result.data)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.client_id, self.client_profile.pk)
        self.assertEqual(self.appointment.price, Decimal('150.00'))
        self.assertEqual(self.appointment.deposit_amount, Decimal('50.00'))
        self.assertTrue(self.appointment.deposit_paid)
        self.assertEqual(self.appointment.status, 'confirmed')
        self.assertEqual(self.appointment.notes, 'Forearm tattoo.')

    def test_original_time_remains_reserved_until_move_is_approved(self):
        self.api.force_authenticate(user=self.employee)
        result = self.api.patch(self.url, {'time':'16:00:00','end_time':'17:00:00'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        notice = Notifications.objects.get(appointment=self.appointment, status='pending')
        payload = self.appointment_payload(date=self.appointment.date.isoformat(), time='14:00:00', end_time='15:00:00')
        self.api.force_authenticate(user=self.admin)
        result = self.api.post(reverse('appointment-list'), payload, format='json')
        self.assertEqual(result.status_code, 400, result.data)
        self.assertIn('awaits review', str(result.data))
        result = self.api.post(reverse('approve-notification', kwargs={'pk':notice.pk}))
        self.assertEqual(result.status_code, 200, result.data)
        result = self.api.post(reverse('appointment-list'), payload, format='json')
        self.assertEqual(result.status_code, 201, result.data)

    def test_repeated_approval_does_not_reopen_a_completed_visit(self):
        notice = Notifications.objects.create(employee=self.employee,appointment=self.appointment,action='created')
        url = reverse('approve-notification', kwargs={'pk':notice.pk})
        self.api.post(url)
        self.api.patch(self.url, {'status':'completed'}, format='json')
        self.assertEqual(self.api.post(url).status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'completed')

    def test_no_show_activity_is_not_a_request_to_reconfirm(self):
        self.api.force_authenticate(user=self.employee)
        result = self.api.patch(self.url, {'status':'no_show'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        notice = Notifications.objects.get(appointment=self.appointment, action='no_show')
        self.assertEqual(notice.status, 'approved')

    def test_full_edit_cannot_bypass_validation_by_including_completed_status(self):
        result = self.api.patch(self.url, {'status':'completed','price':'-1.00'}, format='json')
        self.assertEqual(result.status_code, 400, result.data)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'confirmed')

    def test_calendar_date_range_includes_history_with_owner_scope(self):
        self.appointment.date = localdate() - timedelta(days=2)
        self.appointment.save()
        self.api.force_authenticate(user=self.employee)
        url = reverse('appointment-list')
        response = self.api.get(url, {'start_date':(localdate()-timedelta(days=7)).isoformat(), 'end_date':localdate().isoformat()})
        self.assertEqual([a['id'] for a in response.data], [self.appointment.pk])

    def test_reading_queue_does_not_delete_old_pending_reviews(self):
        notice = Notifications.objects.create(employee=self.employee,appointment=self.appointment,action='updated',previous_details={'notes':'Keep this'})
        Notifications.objects.filter(pk=notice.pk).update(timestamp=now()-timedelta(days=40))
        self.api.get(reverse('recent-activity'))
        self.assertTrue(Notifications.objects.filter(pk=notice.pk).exists())

    def test_employee_cannot_promote_own_account(self):
        self.api.force_authenticate(user=self.employee)
        result = self.api.patch(reverse('user-detail', kwargs={'pk':self.employee.pk}), {'role':'admin'}, format='json')
        self.assertEqual(result.status_code, 400, result.data)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.role, 'employee')

    def test_deleting_reviewed_activity_does_not_revert_a_booking(self):
        notice = Notifications.objects.create(employee=self.employee, appointment=self.appointment,
            action='updated', status='approved', previous_details={'notes':'Old notes'})
        result = self.api.delete(reverse('delete-notification', kwargs={'pk':notice.pk}))
        self.assertEqual(result.status_code, 204)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.notes, 'Forearm tattoo.')

    def test_pending_review_cannot_be_deleted_and_strand_its_booking(self):
        notice = Notifications.objects.create(employee=self.employee, appointment=self.appointment, action='created')
        result = self.api.delete(reverse('delete-notification', kwargs={'pk':notice.pk}))
        self.assertEqual(result.status_code, 400)
        self.assertTrue(Notifications.objects.filter(pk=notice.pk).exists())

    def test_billing_rejects_invalid_fees(self):
        for kind,value in [('flat','-20'),('percentage','101'),('flat','NaN'),('anything','20')]:
            with self.subTest(kind=kind,value=value):
                result = self.api.post(reverse('billing-summary'), {'fee_type':kind,'fee_value':value}, format='json')
                self.assertEqual(result.status_code, 400, result.data)

    def test_billing_session_rounding_reconciles_rows_to_totals(self):
        self.appointment.status = 'completed'
        self.appointment.price = Decimal('0.01')
        self.appointment.deposit_required = False
        self.appointment.deposit_paid = False
        self.appointment.deposit_amount = None
        self.appointment.save()
        for offset in (1,2):
            Appointment.objects.create(client=self.client_profile,employee=self.employee,service=self.service,
                date=self.appointment.date+timedelta(days=offset), time='14:00:00', end_time='15:00:00', price='0.01',status='completed')
        result = self.api.post(reverse('billing-summary'), {'start_date':self.appointment.date.isoformat(),
            'end_date':(self.appointment.date+timedelta(days=2)).isoformat(), 'fee_type':'percentage','fee_value':'50'}, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['shop_total_earnings'], 0.03)
        self.assertEqual(result.data['report'][0]['net_payout'], 0.0)
        self.assertEqual(sum(row['shop_cut'] for row in result.data['report'][0]['appointments']), 0.03)

    @override_settings(DEMO_MODE=True, DEMO_LOGIN_NAMES=('admin',))
    def test_shared_demo_login_cannot_be_changed_or_deleted(self):
        url = reverse('user-detail', kwargs={'pk':self.admin.pk})
        self.assertTrue(self.api.get(url).data['is_demo_account'])
        self.assertEqual(self.api.patch(url, {'username':'renamed'}, format='json').status_code, 400)
        self.assertEqual(self.api.delete(url).status_code, 400)
