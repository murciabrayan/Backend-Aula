from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_studentprofile_acudiente_cedula"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="data_policy_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="data_policy_acceptor_document",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="data_policy_acceptor_name",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="user",
            name="data_policy_version",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
