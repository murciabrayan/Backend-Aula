from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from interactive_classroom.models import ActivitySession


class Command(BaseCommand):
    help = 'Preview or delete closed/expired aula sessions and their participants after the retention period.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        if options['days'] < 1:
            raise CommandError('--days must be at least 1')
        cutoff = timezone.now() - timedelta(days=options['days'])
        qs = ActivitySession.objects.filter(Q(closed_at__lt=cutoff) | Q(expires_at__lt=cutoff))
        count = qs.count()
        if options['apply']:
            qs.delete()
        self.stdout.write(f'{count} sessions: {"deleted" if options["apply"] else "preview only; use --apply to delete"}.')
