"""
Seed development/demo data.

Usage:
    python manage.py seed_data                      # default password DevSeed123!
    python manage.py seed_data --password <pw>      # custom password
    python manage.py seed_data --flush-seeded       # delete seeded rows first

Idempotent: reruns update-or-skip rather than duplicate.
Creates: 1 admin, 3 artists (employees), 5 clients, 3 services,
10 appointments across statuses, and sample activity-log notifications.
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Appointment, ClientProfile, Notifications, Service, User

ARTISTS = [
    ("mia.torres", "Mia", "Torres"),
    ("leo.nakamura", "Leo", "Nakamura"),
    ("ava.bennett", "Ava", "Bennett"),
]

CLIENTS = [
    ("Jordan", "Reyes", "jordan.reyes@example.com", "5550100001"),
    ("Sam", "Okafor", "sam.okafor@example.com", "5550100002"),
    ("Priya", "Patel", "priya.patel@example.com", "5550100003"),
    ("Casey", "Nguyen", "casey.nguyen@example.com", "5550100004"),
    ("Rowan", "Fitzgerald", "rowan.fitz@example.com", "5550100005"),
]

SERVICES = [
    ("service_1", "Small piece / touch-up (up to 1h)", Decimal("120.00")),
    ("service_2", "Half-day session (custom design)", Decimal("250.00")),
    ("service_3", "Full-day session (large scale)", Decimal("400.00")),
]

# (client_idx, artist_idx, service_name, day_offset, start, end, status,
#  requires_approval, price, notes)
# Deposit fields are derived: larger services (service_2/3) require a
# $50 deposit, which is marked paid once the appointment is confirmed.
APPOINTMENTS = [
    (0, 0, "service_1", -9, time(10, 0), time(11, 0), "completed", False, "120.00", "Wrist linework touch-up."),
    (1, 1, "service_2", -6, time(12, 0), time(16, 0), "completed", False, "250.00", "Forearm koi, session 1 of 2."),
    (2, 2, "service_3", -3, time(9, 0), time(17, 0), "completed", False, "400.00", "Back piece outline."),
    (3, 0, "service_1", 1, time(11, 0), time(12, 0), "confirmed", False, "120.00", "Ankle script."),
    (4, 1, "service_2", 2, time(13, 0), time(17, 0), "confirmed", False, "250.00", "Shoulder mandala."),
    (0, 2, "service_1", 3, time(15, 0), time(16, 0), "confirmed", False, "120.00", "Color refresh."),
    (1, 0, "service_3", 5, time(9, 0), time(17, 0), "confirmed", False, "400.00", "Sleeve session 2."),
    (2, 1, "service_1", 4, time(10, 0), time(11, 0), "pending", True, "120.00", "New client consult + small piece."),
    (3, 2, "service_2", 6, time(12, 0), time(16, 0), "pending", True, "250.00", "Thigh floral, needs approval."),
    (4, 0, "service_2", 7, time(13, 0), time(17, 0), "pending", True, "250.00", "Rework of old tattoo."),
]


class Command(BaseCommand):
    help = "Seed the database with realistic development data."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="DevSeed123!",
                            help="Password applied to all seeded accounts (default: DevSeed123!)")
        parser.add_argument("--flush-seeded", action="store_true",
                            help="Delete previously seeded appointments/notifications first.")

    def handle(self, *args, **opts):
        password = opts["password"]

        if opts["flush_seeded"]:
            Notifications.objects.all().delete()
            Appointment.objects.all().delete()
            self.stdout.write("Flushed appointments and notifications.")

        # --- Admin (is_staff required by DRF IsAdminUser views) ---
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"role": "admin", "email": "admin@example.com",
                      "first_name": "Studio", "last_name": "Manager",
                      "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password(password)
            admin.save()
        self.stdout.write(f"Admin: admin ({'created' if created else 'exists'})")

        # --- Artists ---
        artists = []
        for username, first, last in ARTISTS:
            artist, created = User.objects.get_or_create(
                username=username,
                defaults={"role": "employee", "email": f"{username}@example.com",
                          "first_name": first, "last_name": last},
            )
            if created:
                artist.set_password(password)
                artist.save()
            artists.append(artist)
            self.stdout.write(f"Artist: {username} ({'created' if created else 'exists'})")

        # --- Services ---
        services = {}
        for name, desc, price in SERVICES:
            svc, _ = Service.objects.update_or_create(
                name=name, defaults={"description": desc, "price": price},
            )
            services[name] = svc

        # --- Clients (assigned round-robin to artists) ---
        clients = []
        for i, (first, last, email, phone) in enumerate(CLIENTS):
            client, _ = ClientProfile.objects.get_or_create(
                email=email,
                defaults={"first_name": first, "last_name": last,
                          "phone": phone, "employee": artists[i % len(artists)]},
            )
            clients.append(client)
        self.stdout.write(f"Clients: {len(clients)}")

        # --- Appointments ---
        today = date.today()
        appts = []
        for (ci, ai, svc, offset, start, end, status,
             requires_approval, price, notes) in APPOINTMENTS:
            deposit_required = svc in ("service_2", "service_3")
            deposit_paid = deposit_required and status in ("confirmed", "completed")
            deposit_amount = Decimal("50.00") if deposit_required else None
            appt, _ = Appointment.objects.get_or_create(
                client=clients[ci],
                employee=artists[ai],
                date=today + timedelta(days=offset),
                time=start,
                defaults={
                    "service": services[svc],
                    "end_time": end,
                    "price": Decimal(price),
                    "status": status,
                    "requires_approval": requires_approval,
                    "deposit_required": deposit_required,
                    "deposit_paid": deposit_paid,
                    "deposit_amount": deposit_amount,
                    "notes": notes,
                },
            )
            appts.append(appt)
        self.stdout.write(f"Appointments: {Appointment.objects.count()} total")

        # --- Activity log (notifications) ---
        # Pending approvals for the three pending appointments…
        for appt in appts[7:10]:
            Notifications.objects.get_or_create(
                employee=appt.employee, appointment=appt,
                action="created", status="pending",
                defaults={"changes": {
                    "date": str(appt.date), "time": str(appt.time),
                    "end_time": str(appt.end_time), "price": str(appt.price),
                    "service": appt.service.name, "notes": appt.notes,
                }},
            )
        # …plus historical approved/denied entries for realism.
        Notifications.objects.get_or_create(
            employee=artists[0], appointment=appts[3],
            action="updated", status="approved",
            defaults={"changes": {"time": {"old": "10:00:00", "new": "11:00:00"}}},
        )
        Notifications.objects.get_or_create(
            employee=artists[1], appointment=appts[4],
            action="updated", status="denied",
            defaults={"changes": {"price": {"old": "200.00", "new": "250.00"}}},
        )
        self.stdout.write(f"Notifications: {Notifications.objects.count()} total")

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Log in with admin / {password} "
            f"or any artist username / {password}."
        ))
