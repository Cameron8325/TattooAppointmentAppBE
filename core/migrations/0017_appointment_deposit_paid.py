"""
Add Appointment.deposit_paid.

Drift-tolerant: the column may already exist in some databases (it was
observed in a local Postgres without any corresponding migration). The
RunPython op checks the live schema and only ALTERs if the column is
missing; SeparateDatabaseAndState keeps Django's model state correct
either way.
"""
from django.db import migrations, models


def add_column_if_missing(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = [
            col.name
            for col in connection.introspection.get_table_description(
                cursor, "core_appointment"
            )
        ]
    if "deposit_paid" not in columns:
        schema_editor.execute(
            "ALTER TABLE core_appointment "
            "ADD COLUMN deposit_paid boolean NOT NULL DEFAULT false"
        )


def noop(apps, schema_editor):
    # Leave the column in place on reverse; it may predate this migration.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_alter_appointment_date_alter_appointment_status"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_column_if_missing, noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="appointment",
                    name="deposit_paid",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
