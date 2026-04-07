from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0010_user_data_policy_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="signature_image",
            field=models.ImageField(blank=True, null=True, upload_to="signatures/"),
        ),
        migrations.AddField(
            model_name="user",
            name="signature_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
