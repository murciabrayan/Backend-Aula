from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0006_assignment_periodo"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="requires_submission",
            field=models.BooleanField(default=True),
        ),
    ]
