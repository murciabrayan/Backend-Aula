from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0003_attendanceevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="teacher_notes",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attendance",
            name="admin_notes",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunSQL(
            sql=(
                "UPDATE attendance_attendance "
                "SET teacher_notes = COALESCE(teacher_notes, CASE WHEN created_by_id IS NOT NULL THEN notes ELSE NULL END), "
                "admin_notes = COALESCE(admin_notes, CASE WHEN updated_by_id IS NOT NULL AND created_by_id IS NOT NULL AND updated_by_id <> created_by_id THEN notes ELSE NULL END) "
                "WHERE notes IS NOT NULL;"
            ),
            reverse_sql=(
                "UPDATE attendance_attendance "
                "SET teacher_notes = NULL, admin_notes = NULL;"
            ),
        ),
    ]
