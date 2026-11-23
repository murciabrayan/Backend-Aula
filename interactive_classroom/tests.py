import hashlib
import secrets
from datetime import timedelta
from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .content import ACTIVITY, DESKTOP_ACTIVITY, DESKTOP_VERSION, published_activity
from .models import ActivitySession, Participation, StationCompletion


class SessionTests(APITestCase):
    @override_settings(
        AULA_DEMO_EXPIRES_AT='2999-01-01T00:00:00Z',
        ROOT_URLCONF='backend_project.urls',
    )
    def test_demo_teacher_is_limited_to_aula_endpoints(self):
        demo = get_user_model().objects.create_user(
            email='aula-demo@test.invalid', cedula='aula-demo-test',
            role='AULA_DEMO', password='Demo-Test-Only9!',
        )
        self.auth(demo)
        self.assertEqual(self.client.get('/api/aula/me/').status_code, 200)
        self.assertEqual(self.client.get('/api/profile/').status_code, 401)

    @override_settings(AULA_DEMO_EXPIRES_AT='2000-01-01T00:00:00Z')
    def test_expired_demo_teacher_cannot_use_aula(self):
        demo = get_user_model().objects.create_user(
            email='aula-expired@test.invalid', cedula='aula-expired-test',
            role='AULA_DEMO', password='Demo-Test-Only9!',
        )
        self.auth(demo)
        self.assertEqual(self.client.get('/api/aula/me/').status_code, 403)

    @override_settings(AULA_RELEASED_GRADES=['Primero'])
    def test_public_release_gate_allows_first_and_blocks_other_grades(self):
        self.assertEqual(published_activity('partes-del-computador')['grade'], 'Primero')
        with self.assertRaises(ValidationError):
            published_activity('entorno-trabajo')

    def test_first_grade_programming_activities_publish_and_validate_execution_evidence(self):
        from .programming_activities import PROGRAMMING_ACTIVITIES, PROGRAMMING_RULES
        for lesson, expected in PROGRAMMING_ACTIVITIES.items():
            with self.subTest(lesson=lesson):
                self.auth(self.teacher)
                created = self.client.post('/api/aula/sessions/', {'lesson': lesson, 'group_name': 'Primero programación'}, format='json')
                self.assertEqual(created.status_code, 201)
                self.assertEqual(created.data['activity'], expected)
                if lesson != 'programacion-flechas':
                    self.assertEqual(expected['scope'], 'part')
                    self.assertEqual(expected['parent_lesson'], 'programacion-flechas')
                credential = secrets.token_hex(32)
                self.auth()
                self.assertEqual(self.client.post(f"/api/aula/public/{created.data['join_token']}/join/", {'name': 'Equipo programación', 'credential': credential}, format='json').status_code, 201)
                self.participant_auth(credential)
                endpoint = f"/api/aula/participations/{created.data['id']}/"
                rules = PROGRAMMING_RULES[expected['version']]
                for index, station in enumerate(expected['stations']):
                    evidence = rules[station['id']]
                    invalid = dict(evidence)
                    proof = next((key for key in evidence if key != 'completed'), 'completed')
                    invalid[proof] = False if type(evidence[proof]) is bool else 0
                    self.assertEqual(self.client.post(endpoint, {'action': 'complete_station', 'station': station['id'], 'evidence': invalid}, format='json').status_code, 400)
                    response = self.client.post(endpoint, {'action': 'complete_station', 'station': station['id'], 'evidence': {**evidence, 'commands': ['not retained']}}, format='json')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data['percentage'], round((index + 1) / len(rules) * 100))
                    self.assertEqual(StationCompletion.objects.get(participant__session_id=created.data['id'], station=station['id']).evidence, evidence)
                self.auth(self.teacher)
                self.assertEqual(self.client.get(f"/api/aula/sessions/{created.data['id']}/").data['summary']['completed'], 1)

    def test_fifth_grade_project_activities_publish_and_validate_engineering_evidence(self):
        from .project_activities import PROJECT_ACTIVITIES, PROJECT_RULES
        for lesson, expected in PROJECT_ACTIVITIES.items():
            with self.subTest(lesson=lesson):
                self.auth(self.teacher)
                created = self.client.post('/api/aula/sessions/', {'lesson': lesson, 'group_name': 'Quinto proyecto'}, format='json')
                self.assertEqual(created.status_code, 201)
                self.assertEqual(created.data['activity'], expected)
                if lesson != 'proyecto':
                    self.assertEqual(expected['scope'], 'part')
                    self.assertEqual(expected['parent_lesson'], 'proyecto')
                credential = secrets.token_hex(32)
                self.auth()
                self.assertEqual(self.client.post(f"/api/aula/public/{created.data['join_token']}/join/", {'name': 'Equipo quinto', 'credential': credential}, format='json').status_code, 201)
                self.participant_auth(credential)
                endpoint = f"/api/aula/participations/{created.data['id']}/"
                rules = PROJECT_RULES[expected['version']]
                for index, station in enumerate(expected['stations']):
                    evidence = rules[station['id']]
                    for key, value in evidence.items():
                        invalid = {**evidence, key: False if type(value) is bool else 0}
                        self.assertEqual(self.client.post(endpoint, {'action': 'complete_station', 'station': station['id'], 'evidence': invalid}, format='json').status_code, 400)
                    response = self.client.post(endpoint, {'action': 'complete_station', 'station': station['id'], 'evidence': {**evidence, 'program': [['untrusted']] }}, format='json')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data['percentage'], round((index+1)/len(rules)*100))
                    self.assertEqual(StationCompletion.objects.get(participant__session_id=created.data['id'], station=station['id']).evidence, evidence)
                self.auth(self.teacher)
                self.assertEqual(self.client.get(f"/api/aula/sessions/{created.data['id']}/").data['summary']['completed'], 1)

    def test_technology_activities_publish_scopes_and_require_completed_work(self):
        from .technology_activities import TECHNOLOGY_ACTIVITIES, TECHNOLOGY_RULES
        for lesson, expected in TECHNOLOGY_ACTIVITIES.items():
            with self.subTest(lesson=lesson):
                self.auth(self.teacher)
                created = self.client.post('/api/aula/sessions/', {'lesson': lesson, 'group_name': 'Primero tecnología'}, format='json')
                self.assertEqual(created.status_code, 201)
                self.assertEqual(created.data['activity'], expected)
                snapshot = published_activity(lesson)
                snapshot['stations'][0]['title'] = 'Changed locally'
                self.assertEqual(published_activity(lesson), expected)
                credential = secrets.token_hex(32)
                self.auth()
                self.assertEqual(self.client.post(f"/api/aula/public/{created.data['join_token']}/join/", {'name': 'Equipo', 'credential': credential}, format='json').status_code, 201)
                self.participant_auth(credential)
                endpoint = f"/api/aula/participations/{created.data['id']}/"
                rules = TECHNOLOGY_RULES[expected['version']]
                for index, station in enumerate(expected['stations']):
                    evidence = rules[station['id']]
                    for key, value in evidence.items():
                        invalid = {**evidence, key: False if type(value) is bool else 0}
                        self.assertEqual(self.client.post(endpoint, {'action': 'complete_station', 'station': station['id'], 'evidence': invalid}, format='json').status_code, 400)
                    response = self.client.post(endpoint, {'action': 'complete_station', 'station': station['id'], 'evidence': {**evidence, 'strokes': 'not retained'}}, format='json')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data['percentage'], round((index+1)/len(rules)*100))
                    self.assertEqual(StationCompletion.objects.get(participant__session_id=created.data['id'], station=station['id']).evidence, evidence)
                self.auth(self.teacher)
                self.assertEqual(self.client.get(f"/api/aula/sessions/{created.data['id']}/").data['summary']['completed'], 1)

    def test_instruction_v2_keeps_v1_snapshot_rules(self):
        from .content import validated_evidence
        from rest_framework.exceptions import ValidationError
        self.assertEqual(published_activity('instrucciones')['version'], 'INF-1-C03-final-v2')
        old = {'completed': True, 'solved': 1, 'tested': True}
        self.assertEqual(validated_evidence('secuencia-3', old, 'INF-1-C03-final-v1'), old)
        with self.assertRaises(ValidationError):
            validated_evidence('secuencia-3', old, 'INF-1-C03-final-v2')
        self.assertTrue(validated_evidence('secuencia-3', {**old, 'collected': True}, 'INF-1-C03-final-v2')['collected'])

    def test_instruction_class_and_parts_preserve_scope_and_require_executed_solutions(self):
        from .sequence_activities import SEQUENCE_ACTIVITIES
        fixtures = {
            'instrucciones': [{'solved': 1}, {'solved': 3}, {'solved': 1, 'tested': True, 'collected': True}, {'solved': 1, 'tested': True, 'repaired': True}],
            'instrucciones-orden': [{'solved': 2}, {'solved': 3}],
            'instrucciones-claridad': [{'solved': 3}, {'solved': 3}],
            'instrucciones-prueba': [{'solved': 2, 'tested': True, 'collected': True}, {'solved': 3, 'tested': True, 'repaired': True}],
        }
        for lesson, evidence in fixtures.items():
            with self.subTest(lesson=lesson):
                self.auth(self.teacher)
                created = self.client.post('/api/aula/sessions/', {'lesson': lesson, 'group_name': 'Primero instrucciones'}, format='json')
                self.assertEqual(created.status_code, 201)
                activity = created.data['activity']
                self.assertEqual(activity['version'], SEQUENCE_ACTIVITIES[lesson]['version'])
                if lesson != 'instrucciones':
                    self.assertEqual(activity['scope'], 'part')
                    self.assertEqual(activity['parent_lesson'], 'instrucciones')
                self.auth()
                credential = secrets.token_hex(32)
                joined = self.client.post(f"/api/aula/public/{created.data['join_token']}/join/", {'name': 'Equipo instrucciones', 'credential': credential}, format='json')
                self.assertEqual(joined.status_code, 201)
                self.participant_auth(credential)
                endpoint = f"/api/aula/participations/{created.data['id']}/"
                for index, result in enumerate(evidence):
                    station = activity['stations'][index]['id']
                    invalid = {'completed': True, **result}
                    invalid['tested' if 'tested' in result else 'solved'] = False if 'tested' in result else 0
                    self.assertEqual(self.client.post(endpoint, {'action': 'complete_station', 'station': station, 'evidence': invalid}, format='json').status_code, 400)
                    if 'collected' in result:
                        self.assertEqual(self.client.post(endpoint, {'action': 'complete_station', 'station': station, 'evidence': {'completed': True, **result, 'collected': False}}, format='json').status_code, 400)
                    if 'repaired' in result:
                        self.assertEqual(self.client.post(endpoint, {'action': 'complete_station', 'station': station, 'evidence': {'completed': True, **result, 'repaired': False}}, format='json').status_code, 400)
                    response = self.client.post(endpoint, {'action': 'complete_station', 'station': station, 'evidence': {'completed': True, **result}}, format='json')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data['percentage'], round((index+1)/len(evidence)*100))
                self.auth(self.teacher)
                self.assertEqual(self.client.get(f"/api/aula/sessions/{created.data['id']}/").data['summary']['completed'], 1)

    def test_part_sessions_publish_their_own_exercises_and_calculate_progress(self):
        cases = [
            ('partes-del-computador-monitor', [{'zones': 12}]),
            ('partes-del-computador-mouse', [{'drawings': 2, 'points': 10}, {'actions': 3}, {'levels': 2, 'pieces': 6}]),
            ('partes-del-computador-keyboard', [{'models': 6}]),
            ('escritorio-escritorio', [{'found': 4}, {'actions': 4}]),
            ('escritorio-programas', [{'opened': 2}, {'drawn': True, 'stamps': 2}, {'placed': 4}]),
            ('escritorio-ventanas', [{'actions': 5}, {'found': 2}]),
        ]
        for lesson, results in cases:
            with self.subTest(lesson=lesson):
                self.auth(self.teacher)
                response = self.client.post('/api/aula/sessions/', {'group_name': 'Práctica por parte', 'lesson': lesson}, format='json')
                self.assertEqual(response.status_code, 201)
                item = response.data
                self.assertEqual(item['activity']['scope'], 'part')
                self.assertEqual(len(item['activity']['stations']), len(results))
                self.assertEqual(item['activity']['lesson'], lesson)
                self.auth()
                credential = secrets.token_hex(32)
                joined = self.client.post(f"/api/aula/public/{item['join_token']}/join/", {'name': 'Equipo', 'credential': credential}, format='json')
                self.assertEqual(joined.status_code, 201)
                self.participant_auth(credential)
                endpoint = f"/api/aula/participations/{item['id']}/"
                last_station = item['activity']['stations'][-1]['id']
                if len(results) > 1:
                    invalid = self.client.post(endpoint, {'action': 'complete_station', 'station': last_station, 'evidence': {'completed': True, **results[-1]}}, format='json')
                    self.assertEqual(invalid.status_code, 400)
                for index, evidence in enumerate(results):
                    station = item['activity']['stations'][index]['id']
                    rejected = self.client.post(endpoint, {'action': 'complete_station', 'station': station, 'evidence': {'completed': False, **evidence}}, format='json')
                    self.assertEqual(rejected.status_code, 400)
                    accepted = self.client.post(endpoint, {'action': 'complete_station', 'station': station, 'evidence': {'completed': True, **evidence}}, format='json')
                    self.assertEqual(accepted.status_code, 200)
                    self.assertEqual(accepted.data['percentage'], round((index+1)/len(results)*100))
                self.auth(self.teacher)
                detail = self.client.get(f"/api/aula/sessions/{item['id']}/")
                self.assertEqual(detail.data['participants'][0]['percentage'], 100)
                self.assertEqual(detail.data['summary']['completed'], 1)

    def test_part_sessions_reject_other_parts_and_keep_final_versions(self):
        from .content import validated_evidence
        from rest_framework.exceptions import ValidationError
        activity = published_activity('partes-del-computador-mouse')
        self.assertEqual([x['id'] for x in activity['stations']], ['mouse-1', 'mouse-2', 'mouse-3'])
        with self.assertRaises(ValidationError):
            validated_evidence('mouse-1', {'completed': True, 'zones': 12}, 'INF-1-C01-monitor-v1')
        with self.assertRaises(ValidationError):
            validated_evidence('mouse-1', {'completed': True, 'zones': True}, activity['version'])
        activity['stations'].clear()
        self.assertEqual(len(published_activity('partes-del-computador-mouse')['stations']), 3)
        self.assertEqual(published_activity('partes-del-computador')['version'], 'INF-1-C01-final-v3')
        self.assertEqual(published_activity('escritorio')['version'], 'INF-1-C02-final-v1')

    def setUp(self):
        User = get_user_model()
        self.teacher = User.objects.create_user(email='teacher@test.invalid', cedula='101', role='TEACHER', password='Example-Test-Only9!')
        self.other = User.objects.create_user(email='other@test.invalid', cedula='102', role='TEACHER')
        self.student = User.objects.create_user(email='student@test.invalid', cedula='103', role='STUDENT')
        self.admin = User.objects.create_user(email='admin@test.invalid', cedula='104', role='ADMIN')
        self.auth(self.teacher)
        result = self.client.post('/api/aula/sessions/', {'group_name': 'Primero A', 'lesson': 'partes-del-computador'}, format='json')
        self.assertEqual(result.status_code, 201)
        self.session = ActivitySession.objects.get(pk=result.data['id'])
        self.detail = f'/api/aula/sessions/{self.session.pk}/'
        self.join_url = f'/api/aula/public/{self.session.join_token}/join/'
        self.state_url = f'/api/aula/participations/{self.session.pk}/'

    def auth(self, user=None):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}' if user else '')

    def join(self, name='Ana', credential=None):
        credential = credential or secrets.token_hex(32)
        self.auth()
        result = self.client.post(self.join_url, {'name': name, 'credential': credential}, format='json')
        self.assertIn(result.status_code, [200, 201])
        return credential, result.data

    def participant_auth(self, credential):
        self.client.credentials(HTTP_AUTHORIZATION=f'Participation {credential}')

    def test_only_teachers_and_admin_own_sessions(self):
        for user, code in [(None, 401), (self.student, 403)]:
            self.auth(user)
            self.assertEqual(self.client.get('/api/aula/sessions/').status_code, code)
        self.auth(self.other)
        self.assertEqual(self.client.get(self.detail).status_code, 404)
        self.assertEqual(self.client.post(self.detail+'close/').status_code, 404)
        self.assertEqual(self.client.delete(self.detail).status_code, 404)
        self.assertEqual(self.client.get('/api/aula/sessions/').data, [])
        self.auth(self.admin)
        self.assertEqual(self.client.get(self.detail).status_code, 200)

    def test_public_metadata_has_no_names_or_teacher_credentials(self):
        self.join()
        self.auth()
        result = self.client.get(f'/api/aula/public/{self.session.join_token}/')
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('join_token', result.data)
        self.assertNotIn('participants', result.data)
        self.assertNotIn('owner', result.data)
        self.assertEqual(result.data['activity']['version'], ACTIVITY['version'])
        self.assertEqual(result['Cache-Control'], 'no-store')
        self.assertIn(self.client.get(self.state_url).status_code, [401, 403])

    def test_repeated_names_are_separate_and_join_retry_is_idempotent(self):
        first, one = self.join()
        second, two = self.join()
        self.assertNotEqual(one['id'], two['id'])
        self.assertNotEqual(one['number'], two['number'])
        _, repeat = self.join(credential=first)
        self.assertEqual(repeat['id'], one['id'])
        self.assertEqual(Participation.objects.count(), 2)
        stored = Participation.objects.get(pk=one['id'])
        self.assertEqual(stored.credential_hash, hashlib.sha256(first.encode()).hexdigest())
        self.assertNotEqual(stored.credential_hash, first)
        self.participant_auth(second)
        self.assertEqual(self.client.get(self.state_url).data['participant']['id'], two['id'])
        self.assertIn(self.client.get(self.detail).status_code, [401, 403])

    def test_order_evidence_percentages_retry_and_readback(self):
        token, _ = self.join()
        self.participant_auth(token)
        post = lambda value: self.client.post(self.state_url, value, format='json')
        self.assertEqual(post({'action': 'start'}).data['state'], 'in_progress')
        self.assertEqual(post({'action': 'complete_station', 'station': 'creation', 'evidence': {'stickers':3, 'edited':True, 'title_confirmed':True}}).status_code, 400)
        self.assertEqual(post({'action': 'complete_station', 'station': 'puzzle', 'percentage':100, 'evidence': {'pieces': True}}).status_code, 400)
        payloads = [('puzzle', {'pieces': 9}), ('drawing', {'points':11}), ('maze', {'goal':True,'key':True,'star':True}), ('creation', {'stickers':3,'edited':True,'title_confirmed':True})]
        for index, (station, evidence) in enumerate(payloads):
            value = {'action':'complete_station','station':station,'evidence':evidence}
            first = post(value)
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.data['percentage'], (index+1)*25)
            self.assertEqual(post(value).data['percentage'], (index+1)*25)
        self.assertEqual(StationCompletion.objects.count(), 4)
        self.assertEqual(self.client.get(self.state_url).data['participant']['state'], 'completed')
        self.auth(self.teacher)
        result = self.client.get(self.detail)
        self.assertEqual(result.data['summary'], {'joined':1,'completed':1})
        self.assertEqual(result.data['participants'][0]['percentage'], 100)
        self.assertNotIn('credential_hash', result.data['participants'][0])

    def test_close_blocks_joins_and_progress_but_keeps_results_readable(self):
        token, _ = self.join()
        self.auth(self.teacher)
        self.assertEqual(self.client.post(self.detail+'close/').data['state'], 'closed')
        self.auth()
        self.assertEqual(self.client.post(self.join_url, {'name':'Luis','credential':secrets.token_hex(32)}, format='json').status_code, 410)
        self.participant_auth(token)
        self.assertEqual(self.client.post(self.state_url, {'action':'heartbeat'}, format='json').status_code, 410)
        self.assertEqual(self.client.get(self.state_url).data['session']['state'], 'closed')

    def test_expiration_is_checked_by_server(self):
        token, _ = self.join()
        self.session.expires_at = timezone.now()-timedelta(seconds=1)
        self.session.save()
        self.participant_auth(token)
        self.assertEqual(self.client.post(self.state_url, {'action':'start'}, format='json').status_code, 410)
        self.assertEqual(self.client.get(self.state_url).data['session']['state'], 'expired')

    def test_participant_cannot_access_another_session(self):
        token, _ = self.join()
        other = ActivitySession.objects.create(owner=self.other,group_name='Segundo',activity=ACTIVITY,expires_at=timezone.now()+timedelta(hours=1))
        self.participant_auth(token)
        self.assertIn(self.client.get(f'/api/aula/participations/{other.pk}/').status_code, [401,403])

    def test_only_published_activity_and_input_validation(self):
        self.auth(self.teacher)
        self.assertEqual(self.client.post('/api/aula/sessions/', {'group_name':'A', 'lesson':'unpublished'},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/aula/sessions/', {'group_name':'A', 'lesson':'partes-del-computador','duration_hours':9},format='json').status_code,400)
        self.auth()
        for name in ['', 'a'*61, '\u0000']:
            self.assertEqual(self.client.post(self.join_url, {'name':name,'credential':secrets.token_hex(32)},format='json').status_code,400)

    def test_retention_preview_and_owner_delete_cascade(self):
        self.join()
        self.session.closed_at = timezone.now()-timedelta(days=31)
        self.session.save()
        output = StringIO()
        call_command('purge_activity_sessions', stdout=output)
        self.assertTrue(ActivitySession.objects.exists())
        call_command('purge_activity_sessions', apply=True, stdout=output)
        self.assertFalse(ActivitySession.objects.exists())
        self.assertFalse(Participation.objects.exists())

    def test_preview_teacher_cannot_be_created_in_other_settings(self):
        with self.assertRaises(CommandError):
            call_command('prepare_aula_preview')

    def test_owner_delete_removes_only_its_session_and_all_results(self):
        token, _ = self.join()
        self.participant_auth(token)
        result = self.client.post(self.state_url, {'action':'complete_station','station':'puzzle','evidence':{'pieces':9}},format='json')
        self.assertEqual(result.status_code,200)
        other = ActivitySession.objects.create(owner=self.other,group_name='Otro grupo',activity=ACTIVITY,expires_at=timezone.now()+timedelta(hours=1))
        self.auth(self.teacher)
        self.assertEqual(self.client.delete(self.detail).status_code,204)
        self.assertFalse(Participation.objects.exists())
        self.assertFalse(StationCompletion.objects.exists())
        self.assertTrue(ActivitySession.objects.filter(pk=other.pk).exists())

    def test_second_lesson_is_published_without_changing_first_activity(self):
        self.auth(self.teacher)
        result = self.client.post('/api/aula/sessions/', {'group_name':'Primero escritorio','lesson':'escritorio'},format='json')
        self.assertEqual(result.status_code,201)
        self.assertEqual(result.data['activity'],DESKTOP_ACTIVITY)
        self.session.refresh_from_db()
        self.assertEqual(self.session.activity,ACTIVITY)
        snapshot = published_activity('escritorio')
        snapshot['stations'][0]['title'] = 'Changed locally'
        self.assertEqual(published_activity('escritorio'),DESKTOP_ACTIVITY)

    def test_desktop_activity_validates_its_own_stations_and_evidence(self):
        self.auth(self.teacher)
        result = self.client.post('/api/aula/sessions/', {'group_name':'Primero escritorio','lesson':'escritorio'},format='json')
        session = ActivitySession.objects.get(pk=result.data['id'])
        credential = secrets.token_hex(32)
        self.auth()
        joined = self.client.post(f'/api/aula/public/{session.join_token}/join/',{'name':'Ana','credential':credential},format='json')
        self.assertEqual(joined.status_code,201)
        self.participant_auth(credential)
        url = f'/api/aula/participations/{session.pk}/'
        self.assertEqual(self.client.post(url,{'action':'complete_station','station':'puzzle','evidence':{'pieces':9}},format='json').status_code,400)
        self.assertEqual(self.client.post(url,{'action':'complete_station','station':'desktop-find','evidence':{'found':True}},format='json').status_code,400)
        payloads = [('desktop-find',{'found':4}),('desktop-open',{'opened':3}),('desktop-windows',{'actions':5}),('desktop-project',{'drawn':True,'stamps':2,'titled':True,'saved':True,'recovered':True})]
        for index,(station,evidence) in enumerate(payloads):
            value = {'action':'complete_station','station':station,'evidence':evidence}
            response = self.client.post(url,value,format='json')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data['percentage'],(index+1)*25)
            self.assertEqual(self.client.post(url,value,format='json').data['percentage'],(index+1)*25)
        self.assertEqual(self.client.get(url).data['participant']['state'],'completed')
        self.assertEqual(self.client.get(url).data['session']['activity']['version'],DESKTOP_VERSION)
        self.assertIn(self.client.get(self.state_url).status_code,[401,403])

    def test_recovering_a_desktop_project_is_required_for_completion(self):
        self.auth(self.teacher)
        result = self.client.post('/api/aula/sessions/', {'group_name':'Primero escritorio','lesson':'escritorio'},format='json')
        session = ActivitySession.objects.get(pk=result.data['id'])
        token=secrets.token_hex(32)
        self.auth()
        self.client.post(f'/api/aula/public/{session.join_token}/join/',{'name':'Equipo','credential':token},format='json')
        self.participant_auth(token)
        url=f'/api/aula/participations/{session.pk}/'
        for station,evidence in [('desktop-find',{'found':4}),('desktop-open',{'opened':3}),('desktop-windows',{'actions':5})]:
            self.assertEqual(self.client.post(url,{'action':'complete_station','station':station,'evidence':evidence},format='json').status_code,200)
        evidence={'drawn':True,'stamps':2,'titled':True,'saved':True,'recovered':False}
        self.assertEqual(self.client.post(url,{'action':'complete_station','station':'desktop-project','evidence':evidence},format='json').status_code,400)
        self.assertEqual(self.client.get(url).data['participant']['percentage'],75)

    def test_remaining_first_grade_classes_publish_parts_and_validated_evidence(self):
        from .first_path_activities import FIRST_PATH_ACTIVITIES, FIRST_PATH_RULES
        from .content import validated_evidence
        from rest_framework.exceptions import ValidationError
        self.assertEqual(len(FIRST_PATH_ACTIVITIES), 20)
        finals = ['patrones-mensajes', 'bucles', 'bucles-practica', 'errores-programas', 'ciudadania-digital']
        for lesson in finals:
            activity = published_activity(lesson)
            self.assertEqual(len(activity['stations']), 4)
            self.assertEqual(activity['grade'], 'Primero')
        for lesson, activity in FIRST_PATH_ACTIVITIES.items():
            snapshot = published_activity(lesson)
            self.assertEqual(snapshot, activity)
            for station in activity['stations']:
                evidence = FIRST_PATH_RULES[activity['version']][station['id']]
                self.assertEqual(validated_evidence(station['id'], evidence, activity['version']), evidence)
                rejected = {**evidence, 'solved': max(0, evidence['solved'] - 1)}
                with self.assertRaises(ValidationError):
                    validated_evidence(station['id'], rejected, activity['version'])
