from django.db import migrations


EMAIL = 'aula.demo.reunion.2026@gimnasioloscerros.com'
CEDULA = 'aula-demo-2026'


def create_demo_teacher(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.get_or_create(
        email=EMAIL,
        defaults={
            'cedula': CEDULA,
            'first_name': 'Docente',
            'last_name': 'de demostracion',
            'role': 'AULA_DEMO',
            'password': 'pbkdf2_sha256$1000000$iOeEEyBdJnKsgbTU$KnAXGp5ue1p3aZeM2Inem16gTSZJoT3SYK02GDoKiI8=',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
            'must_change_password': False,
        },
    )


def disable_demo_teacher(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(email=EMAIL, cedula=CEDULA, role='AULA_DEMO').update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0013_user_aula_demo_role'),
        ('interactive_classroom', '0001_initial'),
    ]

    operations = [migrations.RunPython(create_demo_teacher, disable_demo_teacher)]
