from django.conf import settings
from django.db import models


class PermissionLetter(models.Model):
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True, default="")
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="permission_letters",
    )
    document = models.FileField(upload_to="permission_letters/originals/")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_permission_letters",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.course.nombre}"


class PermissionLetterRecipient(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_ACCEPTED, "Aceptado"),
        (STATUS_REJECTED, "Rechazado"),
    ]

    permission_letter = models.ForeignKey(
        PermissionLetter,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permission_letter_recipients",
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    responded_at = models.DateTimeField(blank=True, null=True)
    signed_document = models.FileField(
        upload_to="permission_letters/signed/",
        blank=True,
        null=True,
    )
    user_document = models.ForeignKey(
        "accounts.UserDocument",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="permission_letter_records",
    )

    class Meta:
        ordering = ["student__first_name", "student__last_name"]
        unique_together = ("permission_letter", "student")

    def __str__(self):
        return f"{self.permission_letter.title} - {self.student.email} - {self.status}"
