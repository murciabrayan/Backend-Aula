from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("attendance", "0002_attendance_periodo"),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "actor_role",
                    models.CharField(blank=True, max_length=20),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("TEACHER_CREATED", "Registro inicial docente"),
                            ("TEACHER_UPDATED", "Actualización docente"),
                            ("ADMIN_CREATED", "Registro administrativo"),
                            ("ADMIN_UPDATED", "Corrección administrativa"),
                            ("ADMIN_JUSTIFIED", "Justificación administrativa"),
                            ("ADMIN_SUPPORT_ADDED", "Soporte administrativo agregado"),
                        ],
                        max_length=24,
                    ),
                ),
                ("summary", models.CharField(max_length=255)),
                ("notes", models.TextField(blank=True)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="attendance_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "attendance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="attendance.attendance",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evento de asistencia",
                "verbose_name_plural": "Eventos de asistencia",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
