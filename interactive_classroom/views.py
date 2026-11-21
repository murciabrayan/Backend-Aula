import hashlib
import re
import unicodedata
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers
from rest_framework.exceptions import APIException, AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from .content import published_activity, validated_evidence
from .models import ActivitySession, Participation, StationCompletion


def admin(user):
    return user.is_superuser or user.is_staff or user.role == 'ADMIN'


class IsTeacher(permissions.BasePermission):
    message = 'El aula docente requiere una cuenta de profesor o administrador.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.is_active and (admin(user) or user.role == 'TEACHER'))


class NoCacheView(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        return response


class TeacherView(NoCacheView):
    permission_classes = [IsTeacher]


class JoinThrottle(SimpleRateThrottle):
    scope = 'aula_join'
    rate = '180/min'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class ProgressThrottle(JoinThrottle):
    scope = 'aula_progress'
    rate = '120/min'

    def get_cache_key(self, request, view):
        # Shared classroom IPs do not share a progress quota.
        value = request.headers.get('Authorization', '')[:160]
        return self.cache_format % {'scope': self.scope, 'ident': hashlib.sha256(value.encode()).hexdigest()}


class PublicView(NoCacheView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [JoinThrottle]


class SessionInput(serializers.Serializer):
    group_name = serializers.CharField(max_length=80)
    lesson = serializers.CharField(max_length=80)
    duration_hours = serializers.IntegerField(min_value=1, max_value=8, default=4)

    def validate_group_name(self, value):
        return clean_name(value)


def clean_name(value):
    value = ' '.join(value.split())
    if not value or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValidationError('Escribe un nombre legible.')
    return value


class JoinInput(serializers.Serializer):
    name = serializers.CharField(max_length=60)
    credential = serializers.RegexField(r'^[a-f0-9]{64}$')

    def validate_name(self, value):
        return clean_name(value)


class ProgressInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=['start', 'heartbeat', 'complete_station'])
    station = serializers.CharField(max_length=30, required=False)
    evidence = serializers.DictField(required=False)


class Unavailable(APIException):
    status_code = 410
    default_detail = 'Esta sesión terminó. Pide al profesor un nuevo enlace.'


def require_open(session):
    if session.state != 'open':
        raise Unavailable()


def owned_sessions(user):
    qs = ActivitySession.objects.all()
    return qs if admin(user) else qs.filter(owner=user)


def session_data(session, public=False):
    data = {
        'id': str(session.pk), 'group_name': session.group_name,
        'activity': session.activity, 'state': session.state,
        'created_at': session.created_at, 'expires_at': session.expires_at, 'closed_at': session.closed_at,
    }
    if not public:
        data['join_token'] = session.join_token
    return data


def participant_data(participant):
    stations = participant.session.activity['stations']
    completed = {item.station for item in participant.completions.all()}
    done = [item['id'] for item in stations if item['id'] in completed]
    current = next((item for item in stations if item['id'] not in completed), None)
    return {
        'id': str(participant.pk), 'name': participant.name, 'number': participant.number,
        'completed_stations': done, 'total_stations': len(stations),
        'percentage': round(len(done) / len(stations) * 100),
        'state': 'completed' if len(done) == len(stations) else 'in_progress' if participant.started_at else 'not_started',
        'current_station': current, 'joined_at': participant.joined_at,
        'last_seen_at': participant.last_seen_at, 'completed_at': participant.completed_at,
    }


class TeacherMe(TeacherView):
    def get(self, request):
        user = request.user
        return Response({'name': f'{user.first_name} {user.last_name}'.strip() or 'Docente', 'role': user.role})


class Sessions(TeacherView):
    def get(self, request):
        return Response([session_data(item) for item in owned_sessions(request.user)[:100]])

    def post(self, request):
        form = SessionInput(data=request.data)
        form.is_valid(raise_exception=True)
        value = form.validated_data
        activity = published_activity(value['lesson'])
        session = ActivitySession.objects.create(
            owner=request.user, group_name=value['group_name'], activity=activity,
            expires_at=timezone.now() + timedelta(hours=value['duration_hours']),
        )
        return Response(session_data(session), status=201)


class SessionDetail(TeacherView):
    def get(self, request, session_id):
        session = get_object_or_404(owned_sessions(request.user), pk=session_id)
        participants = list(session.participants.prefetch_related('completions'))
        data = session_data(session)
        data['participants'] = [participant_data(p) for p in participants]
        data['summary'] = {
            'joined': len(participants),
            'completed': sum(p.completed_at is not None for p in participants),
        }
        data['server_time'] = timezone.now()
        return Response(data)

    def delete(self, request, session_id):
        session = get_object_or_404(owned_sessions(request.user), pk=session_id)
        session.delete()
        return Response(status=204)


class CloseSession(TeacherView):
    @transaction.atomic
    def post(self, request, session_id):
        session = get_object_or_404(owned_sessions(request.user).select_for_update(), pk=session_id)
        if not session.closed_at:
            session.closed_at = timezone.now()
            session.save(update_fields=['closed_at'])
        return Response(session_data(session))


class PublicSession(PublicView):
    def get(self, request, token):
        session = get_object_or_404(ActivitySession, join_token=token)
        return Response(session_data(session, public=True))


class JoinSession(PublicView):
    @transaction.atomic
    def post(self, request, token):
        form = JoinInput(data=request.data)
        form.is_valid(raise_exception=True)
        session = get_object_or_404(ActivitySession.objects.select_for_update(), join_token=token)
        require_open(session)
        value = form.validated_data
        digest = hashlib.sha256(value['credential'].encode()).hexdigest()
        existing = Participation.objects.filter(credential_hash=digest).first()
        if existing:
            if existing.session_id != session.pk:
                raise ValidationError('Usa el acceso correspondiente a esta sesión.')
            return Response(participant_data(existing))
        if session.next_number > 200:
            raise ValidationError('La sesión alcanzó su límite de 200 participantes.')
        participant = Participation.objects.create(
            session=session, name=value['name'], number=session.next_number, credential_hash=digest,
        )
        session.next_number += 1
        session.save(update_fields=['next_number'])
        return Response(participant_data(participant), status=201)


def participant_for(request, session_id):
    match = re.fullmatch(r'Participation ([a-f0-9]{64})', request.headers.get('Authorization', ''))
    if not match:
        raise AuthenticationFailed('Abre el enlace y escribe tu nombre para participar.')
    digest = hashlib.sha256(match[1].encode()).hexdigest()
    participant = Participation.objects.select_related('session').filter(session_id=session_id, credential_hash=digest).first()
    if not participant:
        raise AuthenticationFailed('No encontramos esta participación. Vuelve a abrir tu enlace.')
    return participant


class ParticipantState(PublicView):
    throttle_classes = [ProgressThrottle]

    def get(self, request, session_id):
        participant = participant_for(request, session_id)
        return Response({'participant': participant_data(participant), 'session': session_data(participant.session, public=True)})

    @transaction.atomic
    def post(self, request, session_id):
        participant = participant_for(request, session_id)
        # Same lock order as closing/joining; closing and completing cannot race.
        session = ActivitySession.objects.select_for_update().get(pk=session_id)
        participant = Participation.objects.select_for_update().get(pk=participant.pk)
        participant.session = session
        require_open(session)
        form = ProgressInput(data=request.data)
        form.is_valid(raise_exception=True)
        value = form.validated_data
        action = value['action']
        if action in ('start', 'complete_station') and not participant.started_at:
            participant.started_at = timezone.now()
        if action == 'complete_station':
            station = value.get('station')
            required = [item['id'] for item in session.activity['stations']]
            if station not in required:
                raise ValidationError({'station': 'El desafío no pertenece a esta actividad.'})
            evidence = validated_evidence(station, value.get('evidence'), session.activity['version'])
            done = set(participant.completions.values_list('station', flat=True))
            if any(item not in done for item in required[:required.index(station)]):
                raise ValidationError({'station': 'Completa primero el desafío anterior.'})
            StationCompletion.objects.get_or_create(participant=participant, station=station, defaults={'evidence': evidence})
            if len(done | {station}) == len(required) and not participant.completed_at:
                participant.completed_at = timezone.now()
        participant.last_seen_at = timezone.now()
        participant.save(update_fields=['started_at', 'completed_at', 'last_seen_at'])
        return Response(participant_data(participant))
