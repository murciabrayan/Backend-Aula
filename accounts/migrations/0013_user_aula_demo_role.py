from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0012_studentprofile_acudiente2_cedula_and_more')]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Administrador'),
                    ('TEACHER', 'Docente'),
                    ('STUDENT', 'Estudiante'),
                    ('AULA_DEMO', 'Docente de demostracion del aula'),
                ],
                max_length=10,
            ),
        ),
    ]
