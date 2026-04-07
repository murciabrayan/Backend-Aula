from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0011_user_signature_fields"),
        ("courses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PermissionLetter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True, default="")),
                ("document", models.FileField(upload_to="permission_letters/originals/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="permission_letters", to="courses.course")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_permission_letters", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PermissionLetterRecipient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDING", "Pendiente"), ("ACCEPTED", "Aceptado"), ("REJECTED", "Rechazado")], default="PENDING", max_length=12)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("signed_document", models.FileField(blank=True, null=True, upload_to="permission_letters/signed/")),
                ("permission_letter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipients", to="permission_letters.permissionletter")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="permission_letter_recipients", to=settings.AUTH_USER_MODEL)),
                ("user_document", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="permission_letter_records", to="accounts.userdocument")),
            ],
            options={"ordering": ["student__first_name", "student__last_name"], "unique_together": {("permission_letter", "student")}},
        ),
    ]
