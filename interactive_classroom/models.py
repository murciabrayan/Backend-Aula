import secrets
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def join_token():
    return secrets.token_urlsafe(32)


class ActivitySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_sessions')
    group_name = models.CharField(max_length=80)
    activity = models.JSONField()
    join_token = models.CharField(max_length=64, unique=True, default=join_token, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-created_at']

    @property
    def state(self):
        if self.closed_at:
            return 'closed'
        return 'expired' if self.expires_at <= timezone.now() else 'open'


class Participation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ActivitySession, on_delete=models.CASCADE, related_name='participants')
    name = models.CharField(max_length=60)
    number = models.PositiveIntegerField()
    credential_hash = models.CharField(max_length=64, unique=True, editable=False)
    joined_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['number']
        constraints = [models.UniqueConstraint(fields=['session', 'number'], name='aula_unique_participant_number')]


class StationCompletion(models.Model):
    participant = models.ForeignKey(Participation, on_delete=models.CASCADE, related_name='completions')
    station = models.CharField(max_length=30)
    evidence = models.JSONField()
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['participant', 'station'], name='aula_unique_station_completion')]
