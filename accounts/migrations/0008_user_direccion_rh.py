from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_user_must_change_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="direccion",
            field=models.CharField(blank=True, default="", max_length=220),
        ),
        migrations.AddField(
            model_name="user",
            name="rh",
            field=models.CharField(blank=True, default="", max_length=5),
        ),
    ]
