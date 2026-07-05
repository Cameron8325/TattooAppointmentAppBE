"""
Reconcile the remaining drifted deposit columns: deposit_required
(boolean NOT NULL) and deposit_amount (numeric NULL). Like 0017, this is
drift-tolerant — the live schema is introspected and columns are only
added where missing, so it applies cleanly to both the drifted local
Postgres (columns pre-exist) and fresh databases.
"""
from django.db import migrations, models


def _existing_columns(schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        return {
            col.name
            for col in connection.introspection.get_table_description(
                cursor, "core_appointment"
            )
        }


def add_columns_if_missing(apps, schema_editor):
    Appointment = apps.get_model("core", "Appointment")
    existing = _existing_columns(schema_editor)

    if "deposit_required" not in existing:
        field = models.BooleanField(default=False)
        field.set_attributes_from_name("deposit_required")
        schema_editor.add_field(Appointment, field)

    if "deposit_amount" not in existing:
        field = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
        field.set_attributes_from_name("deposit_amount")
        schema_editor.add_field(Appointment, field)


def noop(apps, schema_editor):
    # Columns may predate this migration; leave them in place on reverse.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_appointment_deposit_paid"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_columns_if_missing, noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="appointment",
                    name="deposit_required",
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name="appointment",
                    name="deposit_amount",
                    field=models.DecimalField(
                        max_digits=10, decimal_places=2, null=True, blank=True
                    ),
                ),
            ],
        ),
    ]
