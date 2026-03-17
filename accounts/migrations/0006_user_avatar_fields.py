from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_userdocument"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar_seed",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar_style",
            field=models.CharField(blank=True, default="adventurer-neutral", max_length=60),
        ),
    ]
