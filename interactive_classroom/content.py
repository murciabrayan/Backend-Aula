"""Published final activities. Sessions keep a snapshot, never a teacher-chosen game."""
from copy import deepcopy
from django.conf import settings
from rest_framework.exceptions import ValidationError
from .part_activities import PART_ACTIVITIES, PART_RULES
from .sequence_activities import SEQUENCE_ACTIVITIES, SEQUENCE_RULES
from .technology_activities import TECHNOLOGY_ACTIVITIES, TECHNOLOGY_RULES
from .project_activities import PROJECT_ACTIVITIES, PROJECT_RULES
from .programming_activities import PROGRAMMING_ACTIVITIES, PROGRAMMING_RULES
from .first_path_activities import FIRST_PATH_ACTIVITIES, FIRST_PATH_RULES
from .second_grade_activities import SECOND_GRADE_ACTIVITIES, SECOND_GRADE_RULES
from .third_grade_activities import THIRD_GRADE_ACTIVITIES, THIRD_GRADE_RULES


LESSON = 'partes-del-computador'
VERSION = 'INF-1-C01-final-v3'
ACTIVITY = {
    'lesson': LESSON,
    'version': VERSION,
    'title': 'Partes del computador',
    'grade': 'Primero',
    'activity_title': 'Practiquemos con el computador',
    'stations': [
        {'id': 'puzzle', 'title': 'El rincón del computador'},
        {'id': 'drawing', 'title': 'Dibuja un ave'},
        {'id': 'maze', 'title': 'Encuentra la llave y la salida'},
        {'id': 'creation', 'title': 'Crea y presenta tu escena'},
    ],
}

DESKTOP_VERSION = 'INF-1-C02-final-v1'
DESKTOP_ACTIVITY = {
    'lesson': 'escritorio', 'version': DESKTOP_VERSION,
    'title': 'El escritorio y sus iconos', 'grade': 'Primero',
    'activity_title': 'Mi primer escritorio de trabajo',
    'stations': [
        {'id': 'desktop-find', 'title': 'Encuentra lo que necesitas'},
        {'id': 'desktop-open', 'title': 'Abre el programa adecuado'},
        {'id': 'desktop-windows', 'title': 'Organiza tus ventanas'},
        {'id': 'desktop-project', 'title': 'Crea, guarda y recupera'},
    ],
}
PUBLISHED = {LESSON: ACTIVITY, 'escritorio': DESKTOP_ACTIVITY, **PART_ACTIVITIES, **SEQUENCE_ACTIVITIES, **TECHNOLOGY_ACTIVITIES, **PROJECT_ACTIVITIES, **PROGRAMMING_ACTIVITIES, **FIRST_PATH_ACTIVITIES, **SECOND_GRADE_ACTIVITIES, **THIRD_GRADE_ACTIVITIES}


def published_activity(lesson):
    activity = PUBLISHED.get(lesson)
    released_grades = getattr(settings, 'AULA_RELEASED_GRADES', ['*'])
    if activity is None or ('*' not in released_grades and activity.get('grade') not in released_grades):
        raise ValidationError({'lesson': 'Esta clase todavía no tiene una actividad final publicada.'})
    return deepcopy(activity)


def validated_evidence(station, value, version=VERSION):
    """Validate structured completion, never accept a browser-supplied percentage.

    This is formative, client-reported evidence, not a tamper-proof examination.
    Keep only the fields needed for this activity, no free-form student content.
    """
    if not isinstance(value, dict):
        raise ValidationError({'evidence': 'Falta el resultado del desafío.'})
    rules = {VERSION: {
        'puzzle': {'pieces': 9},
        'drawing': {'points': 11},
        'maze': {'goal': True, 'key': True, 'star': True},
        'creation': {'stickers': 3, 'edited': True, 'title_confirmed': True},
    }, DESKTOP_VERSION: {
        'desktop-find': {'found': 4},
        'desktop-open': {'opened': 3},
        'desktop-windows': {'actions': 5},
        'desktop-project': {'drawn': True, 'stamps': 2, 'titled': True, 'saved': True, 'recovered': True},
    }}
    expected = {**rules, **PART_RULES, **SEQUENCE_RULES, **TECHNOLOGY_RULES, **PROJECT_RULES, **PROGRAMMING_RULES, **FIRST_PATH_RULES, **SECOND_GRADE_RULES, **THIRD_GRADE_RULES}.get(version, {}).get(station)
    if not expected or any(type(value.get(k)) is not type(v) or value.get(k) != v for k, v in expected.items()):
        raise ValidationError({'evidence': 'El desafío todavía no tiene todos sus objetivos completos.'})
    return expected.copy()
