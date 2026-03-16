from django.db import models
from django.conf import settings
from courses.models import Course


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("PRESENT", "Presente"),
        ("ABSENT", "Ausente"),
        ("LATE", "Tarde"),
    ]

    JUSTIFICATION_TYPE_CHOICES = [
        ("NONE", "Sin justificar"),
        ("MEDICAL", "Excusa médica"),
        ("PERMISSION", "Permiso"),
        ("CALAMITY", "Calamidad"),
        ("OTHER", "Otra"),
    ]

    PERIOD_CHOICES = [
        (1, "Periodo 1"),
        (2, "Periodo 2"),
        (3, "Periodo 3"),
        (4, "Periodo 4"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        limit_choices_to={"role": "STUDENT"},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField()
    periodo = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES, default=1)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PRESENT",
    )

    is_justified = models.BooleanField(default=False)
    justification_type = models.CharField(
        max_length=20,
        choices=JUSTIFICATION_TYPE_CHOICES,
        default="NONE",
    )
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(
        upload_to="attendance_supports/",
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_created_records",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_updated_records",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ("student", "date")
        ordering = ["-date", "student__first_name", "student__last_name"]

    def __str__(self):
        return f"{self.student.email} - {self.date} - P{self.periodo} - {self.status}"