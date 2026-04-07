from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_user_direccion_rh"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="acudiente_cedula",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
