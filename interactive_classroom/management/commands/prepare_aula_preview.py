import secrets
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create a teacher only in the isolated local aula preview database.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-password', action='store_true')

    def handle(self, *args, **options):
        if (settings.SETTINGS_MODULE != 'backend_project.aula_local_settings'
                or settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3'
                or Path(settings.DATABASES['default']['NAME']) != settings.BASE_DIR / 'aula-local.sqlite3'):
            raise CommandError('This command only works with backend_project.aula_local_settings and aula-local.sqlite3.')
        user, created = get_user_model().objects.get_or_create(
            email='docente.aula@local.test',
            defaults={'cedula':'aula-local-preview','role':'TEACHER','first_name':'Docente','last_name':'de prueba'},
        )
        if created or options['reset_password']:
            password = 'Aula-' + secrets.token_hex(5) + '!'
            user.set_password(password)
            user.save(update_fields=['password'])
            self.stdout.write(f'Local preview only\nEmail: {user.email}\nPassword: {password}')
        else:
            self.stdout.write('Local preview teacher already exists. Use --reset-password if needed.')
