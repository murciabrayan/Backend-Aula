from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_alerts(apps, schema_editor):
    AcademicAlert = apps.get_model("academic_alerts", "AcademicAlert")
    AcademicAlertEvent = apps.get_model("academic_alerts", "AcademicAlertEvent")

    for alert in AcademicAlert.objects.all():
        original_status = alert.status
        if original_status == "ACTIVE":
            alert.status = "TEACHER_INITIAL_PENDING"
        elif original_status == "RESOLVED":
            alert.status = "RESOLVED_POSITIVE"
        alert.save(update_fields=["status", "updated_at"])

        if not AcademicAlertEvent.objects.filter(alert=alert).exists():
            AcademicAlertEvent.objects.create(
                alert=alert,
                event_type="ALERT_CREATED",
                title="Alerta inicial generada",
                notes=alert.message_student or "",
                visible_to_student=True,
                metadata={"migrated": True},
                actor=None,
            )

        if original_status == "RESOLVED" and not AcademicAlertEvent.objects.filter(
            alert=alert,
            event_type="ADMIN_CLOSED_POSITIVE",
        ).exists():
            AcademicAlertEvent.objects.create(
                alert=alert,
                event_type="ADMIN_CLOSED_POSITIVE",
                title="Cierre final satisfactorio",
                notes=alert.resolution_notes or "",
                visible_to_student=True,
                metadata={"migrated": True},
                actor=alert.resolved_by,
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("academic_alerts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="academicalert",
            name="next_follow_up_due_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="academicalert",
            name="status",
            field=models.CharField(
                choices=[
                    ("TEACHER_INITIAL_PENDING", "Pendiente de seguimiento docente"),
                    ("ADMIN_INITIAL_REVIEW", "Pendiente de revisión administrativa"),
                    ("MONITORING", "En seguimiento"),
                    ("TEACHER_FINAL_PENDING", "Pendiente de confirmación docente"),
                    ("ADMIN_FINAL_REVIEW", "Pendiente de cierre administrativo"),
                    ("RESOLVED_POSITIVE", "Cierre satisfactorio"),
                    ("RESOLVED_NEGATIVE", "Cierre no satisfactorio"),
                ],
                default="TEACHER_INITIAL_PENDING",
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="AcademicAlertEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("ALERT_CREATED", "Alerta creada"),
                            ("ALERT_REOPENED", "Alerta reabierta"),
                            ("TEACHER_INITIAL_SUBMITTED", "Primer seguimiento docente enviado"),
                            ("ADMIN_REVIEW_APPROVED", "Seguimiento inicial aprobado"),
                            ("ADMIN_REVIEW_REJECTED", "Seguimiento inicial rechazado"),
                            ("SECOND_FOLLOW_UP_REQUESTED", "Segunda revisión solicitada"),
                            ("TEACHER_FINAL_SUBMITTED", "Segundo seguimiento docente enviado"),
                            ("ADMIN_CLOSED_POSITIVE", "Cierre satisfactorio"),
                            ("ADMIN_CLOSED_NEGATIVE", "Cierre no satisfactorio"),
                        ],
                        max_length=40,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("notes", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("visible_to_student", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="academic_alert_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "alert",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="academic_alerts.academicalert",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evento de alerta académica",
                "verbose_name_plural": "Eventos de alertas académicas",
                "ordering": ["created_at", "id"],
            },
        ),
        migrations.RunPython(migrate_existing_alerts, migrations.RunPython.noop),
    ]
