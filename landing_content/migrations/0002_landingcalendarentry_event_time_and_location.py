from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("landing_content", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="landingcalendarentry",
            name="event_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="landingcalendarentry",
            name="location",
            field=models.CharField(blank=True, max_length=220),
        ),
    ]
