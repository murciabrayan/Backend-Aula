from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_profile_photo"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("category", models.CharField(blank=True, max_length=120)),
                ("file", models.FileField(upload_to="user_documents/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-uploaded_at", "title"],
            },
        ),
    ]
