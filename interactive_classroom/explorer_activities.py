"""Versioned activities for the first verified class: Exploradores digitales."""


EXPLORER_VERSION = 'INF-1-EXP-final-v1'
EXPLORER_ACTIVITY = {
    'lesson': 'exploradores-digitales',
    'version': EXPLORER_VERSION,
    'title': 'Exploradores digitales',
    'grade': 'Primero',
    'activity_title': 'Misión de Exploradores digitales',
    'stations': [
        {'id': 'password', 'title': 'Comprueba una contraseña ficticia'},
        {'id': 'login', 'title': 'Ingresa con datos de práctica'},
        {'id': 'desktop-find', 'title': 'Encuentra un programa'},
        {'id': 'desktop-project', 'title': 'Crea, guarda y recupera'},
    ],
}


def part(part_id, version, title, stations):
    activity = {
        'lesson': f'exploradores-digitales-{part_id}',
        'version': version,
        'scope': 'part',
        'parent_lesson': 'exploradores-digitales',
        'part': part_id,
        'part_title': title,
        'title': f'Exploradores digitales · {title}',
        'grade': 'Primero',
        'activity_title': f'Actividad: {title}',
        'stations': [
            {'id': f'{part_id}-{index + 1}', 'title': name}
            for index, (name, _) in enumerate(stations)
        ],
    }
    rules = {
        f'{part_id}-{index + 1}': {'completed': True, **evidence}
        for index, (_, evidence) in enumerate(stations)
    }
    return activity, rules


EXPLORER_ACTIVITIES = {'exploradores-digitales': EXPLORER_ACTIVITY}
EXPLORER_RULES = {
    EXPLORER_VERSION: {
        'password': {'models': 2, 'checked': True},
        'login': {'login': True},
        'desktop-find': {'found': 4},
        'desktop-project': {
            'drawn': True, 'stamps': 2, 'titled': True,
            'saved': True, 'recovered': True,
        },
    },
}

for args in [
    ('inicio-sesion', 'INF-1-EXP-inicio-v1', 'Tutorial: iniciar sesión', [
        ('Comprobar una contraseña ficticia', {'models': 2, 'checked': True}),
        ('Ingresar con datos de práctica', {'login': True}),
    ]),
    ('rincon-digital', 'INF-1-EXP-rincon-v1', 'Mi rincón digital', [
        ('Encontrar un icono', {'found': 4}),
        ('Abrir el programa correcto', {'opened': 2}),
    ]),
    ('artistas-digitales', 'INF-1-EXP-artistas-v1', 'Artistas digitales', [
        ('Elegir herramientas', {'tools': 4}),
        ('Crear una ilustración', {'drawn': True, 'stamps': 2}),
    ]),
    ('guardar-tesoros', 'INF-1-EXP-guardar-v1', 'Guardar tesoros', [
        ('Ordenar los pasos para guardar', {'steps': 6}),
        ('Encontrar el archivo guardado', {'found': 2}),
    ]),
]:
    activity, rules = part(*args)
    EXPLORER_ACTIVITIES[activity['lesson']] = activity
    EXPLORER_RULES[activity['version']] = rules
