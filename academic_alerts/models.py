from django.conf import settings
from django.db import models

from courses.models import Course


class AcademicAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ("LOW_GRADE", "Bajo rendimiento"),
        ("ABSENCE_RISK", "Riesgo por inasistencia"),
        ("MISSING_ASSIGNMENTS", "Incumplimiento de tareas"),
    ]

    LEVEL_CHOICES = [
        ("WARNING", "Advertencia"),
        ("CRITICAL", "Crítica"),
    ]

    STATUS_CHOICES = [
        ("TEACHER_INITIAL_PENDING", "Pendiente de seguimiento docente"),
        ("ADMIN_INITIAL_REVIEW", "Pendiente de revisión administrativa"),
        ("MONITORING", "En seguimiento"),
        ("TEACHER_FINAL_PENDING", "Pendiente de confirmación docente"),
        ("ADMIN_FINAL_REVIEW", "Pendiente de cierre administrativo"),
        ("RESOLVED_POSITIVE", "Cierre satisfactorio"),
        ("RESOLVED_NEGATIVE", "Cierre no satisfactorio"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_alerts",
        limit_choices_to={"role": "STUDENT"},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="academic_alerts",
    )

    period = models.PositiveSmallIntegerField()
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="WARNING")
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="TEACHER_INITIAL_PENDING",
    )

    title = models.CharField(max_length=255)
    message_student = models.TextField()
    message_teacher = models.TextField()
    message_admin = models.TextField()

    metric_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)

    details = models.JSONField(default=dict, blank=True)

    next_follow_up_due_at = models.DateTimeField(null=True, blank=True)

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_academic_alerts",
    )
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Alerta académica"
        verbose_name_plural = "Alertas académicas"
        ordering = ["-created_at"]
        unique_together = ("student", "course", "period", "alert_type")

    def __str__(self):
        return f"{self.student.email} - P{self.period} - {self.alert_type}"


class AcademicAlertEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("ALERT_CREATED", "Alerta creada"),
        ("ALERT_REOPENED", "Alerta reabierta"),
        ("TEACHER_INITIAL_SUBMITTED", "Primer seguimiento docente enviado"),
        ("ADMIN_REVIEW_APPROVED", "Seguimiento inicial aprobado"),
        ("ADMIN_REVIEW_REJECTED", "Seguimiento inicial rechazado"),
        ("SECOND_FOLLOW_UP_REQUESTED", "Segunda revisión solicitada"),
        ("TEACHER_FINAL_SUBMITTED", "Segundo seguimiento docente enviado"),
        ("ADMIN_CLOSED_POSITIVE", "Cierre satisfactorio"),
        ("ADMIN_CLOSED_NEGATIVE", "Cierre no satisfactorio"),
    ]

    alert = models.ForeignKey(
        AcademicAlert,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=40, choices=EVENT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    visible_to_student = models.BooleanField(default=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academic_alert_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evento de alerta académica"
        verbose_name_plural = "Eventos de alertas académicas"
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.alert_id} - {self.event_type}"
