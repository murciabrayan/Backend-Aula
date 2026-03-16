from django.db import models
from django.conf import settings
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
        ("ACTIVE", "Activa"),
        ("RESOLVED", "Resuelta"),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    title = models.CharField(max_length=255)
    message_student = models.TextField()
    message_teacher = models.TextField()
    message_admin = models.TextField()

    metric_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)

    details = models.JSONField(default=dict, blank=True)

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