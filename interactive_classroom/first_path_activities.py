"""Published activities for the remaining first-grade Informatics classes."""

FIRST_PATH_ACTIVITIES = {}
FIRST_PATH_RULES = {}

BASE_SOLVED = {
    'pattern-complete': 4, 'pattern-group': 3, 'pattern-rule': 3, 'pattern-repair': 3,
    'cipher-decode': 3, 'cipher-encode': 3,
    'loop-compress': 3, 'loop-count': 3, 'loop-expand': 3, 'loop-build': 3,
    'loop-route': 2, 'loop-fix-count': 3, 'loop-predict': 3, 'loop-safe-count': 3,
    'loop-recycle': 3, 'loop-contexts': 2, 'loop-bear': 2, 'loop-adapt': 3,
    'debug-compare': 3, 'debug-first-error': 3, 'debug-trace': 3, 'debug-classify': 3,
    'debug-repair': 2, 'debug-loop': 3,
    'safe-data-sort': 6, 'safe-profile': 1, 'safe-trusted': 2, 'safe-ask-help': 1,
    'safe-story': 3, 'safe-stop-close-tell': 3,
}


def expected_for(game, final=False):
    expected = {'completed': True, 'solved': 1 if final else BASE_SOLVED[game]}
    if game.startswith('pattern-'):
        expected['repaired' if game == 'pattern-repair' else 'patterned'] = True
    elif game == 'cipher-decode':
        expected['decoded'] = True
    elif game == 'cipher-encode':
        expected['encoded'] = True
    elif game.startswith('loop-'):
        expected['looped'] = True
        if game in {'loop-route', 'loop-fix-count', 'loop-predict', 'loop-recycle', 'loop-contexts', 'loop-bear', 'loop-adapt'}:
            expected['executed'] = True
    elif game.startswith('debug-'):
        if game in {'debug-compare', 'debug-first-error', 'debug-trace', 'debug-classify'}:
            expected['inspected'] = True
        if game in {'debug-first-error', 'debug-trace', 'debug-repair'}:
            expected['tested'] = True
        if game == 'debug-repair':
            expected['repaired'] = True
        if game == 'debug-loop':
            expected.update(looped=True, executed=True)
    elif game.startswith('safe-'):
        expected['decided'] = True
    return expected


SPECS = [
    ('patrones-mensajes', 'C06', 'final', None, 'Patrones y mensajes secretos',
     ['Continúa la secuencia', 'Encuentra la unidad', 'Repara la regla', 'Descifra el mensaje'],
     ['pattern-complete', 'pattern-group', 'pattern-repair', 'cipher-decode']),
    ('patrones-mensajes-patrones', 'C06', 'patrones', 'patrones', 'Descubrimos patrones',
     ['La pieza que continúa', 'Encuentra la unidad'], ['pattern-complete', 'pattern-group']),
    ('patrones-mensajes-reglas', 'C06', 'reglas', 'reglas', 'Continuamos y reparamos reglas',
     ['Completa varios lugares', 'Taller de patrones'], ['pattern-rule', 'pattern-repair']),
    ('patrones-mensajes-codigos', 'C06', 'codigos', 'codigos', 'Representamos mensajes con una clave',
     ['Detectives de símbolos', 'Construimos un mensaje'], ['cipher-decode', 'cipher-encode']),
    ('bucles', 'C07', 'final', None, 'Acciones que se repiten',
     ['Comprime acciones', 'Construye el bucle', 'Programa el recorrido', 'Repara la cantidad'],
     ['loop-compress', 'loop-build', 'loop-route', 'loop-fix-count']),
    ('bucles-repeticion', 'C07', 'repeticion', 'repeticion', 'Descubrimos la repetición',
     ['La lista más clara', '¿Cuántas veces?'], ['loop-compress', 'loop-count']),
    ('bucles-bloque-repetir', 'C07', 'bloque-repetir', 'bloque-repetir', 'Conocemos el bloque Repetir',
     ['Desplegamos el bucle', 'Construimos un bloque'], ['loop-expand', 'loop-build']),
    ('bucles-programas', 'C07', 'programas', 'programas', 'Programamos recorridos con bucles',
     ['Recorridos compactos', 'Reparamos la cantidad'], ['loop-route', 'loop-fix-count']),
    ('bucles-practica', 'C08', 'final', None, 'Bucles en nuevas misiones',
     ['Predice el resultado', 'Calcula una ruta', 'Protege el sendero', 'Adapta el programa'],
     ['loop-predict', 'loop-recycle', 'loop-bear', 'loop-adapt']),
    ('bucles-practica-predecimos', 'C08', 'predecimos', 'predecimos', 'Predecimos repeticiones',
     ['¿Dónde terminará?', '¿Cabe la repetición?'], ['loop-predict', 'loop-safe-count']),
    ('bucles-practica-contextos', 'C08', 'contextos', 'contextos', 'Usamos bucles en otros contextos',
     ['La ruta del reciclaje', 'Órbitas y entrenamiento'], ['loop-recycle', 'loop-contexts']),
    ('bucles-practica-adaptamos', 'C08', 'adaptamos', 'adaptamos', 'Adaptamos un programa',
     ['El sendero del oso', 'La meta cambió'], ['loop-bear', 'loop-adapt']),
    ('errores-programas', 'C09', 'final', None, 'Detectives de programas',
     ['Compara resultados', 'Localiza la diferencia', 'Repara un programa', 'Comprueba un bucle'],
     ['debug-compare', 'debug-trace', 'debug-repair', 'debug-loop']),
    ('errores-programas-observamos', 'C09', 'observamos', 'observamos', 'Observamos antes de cambiar',
     ['Meta y resultado', 'La primera pista'], ['debug-compare', 'debug-first-error']),
    ('errores-programas-localizamos', 'C09', 'localizamos', 'localizamos', 'Seguimos la traza',
     ['La mesa de trazas', '¿Qué tipo de error es?'], ['debug-trace', 'debug-classify']),
    ('errores-programas-corregimos', 'C09', 'corregimos', 'corregimos', 'Corregimos y comprobamos',
     ['Reparamos flechas y orden', 'Reparamos repeticiones'], ['debug-repair', 'debug-loop']),
    ('ciudadania-digital', 'C10', 'final', None, 'Nos cuidamos en internet',
     ['Reconoce datos', 'Elige ayuda', 'Decide con calma', 'Aplica el plan'],
     ['safe-data-sort', 'safe-trusted', 'safe-story', 'safe-stop-close-tell']),
    ('ciudadania-digital-datos', 'C10', 'datos', 'datos', 'Protegemos nuestros datos',
     ['La caja de los datos', 'Un perfil para el juego'], ['safe-data-sort', 'safe-profile']),
    ('ciudadania-digital-confianza', 'C10', 'confianza', 'confianza', 'Pedimos ayuda a personas de confianza',
     ['¿A quién pedimos ayuda?', 'Contamos lo necesario'], ['safe-trusted', 'safe-ask-help']),
    ('ciudadania-digital-decisiones', 'C10', 'decisiones', 'decisiones', 'Actuamos ante algo incómodo',
     ['Historias para decidir', 'Detener, cerrar y contar'], ['safe-story', 'safe-stop-close-tell']),
]

PARENTS = {'C06': 'patrones-mensajes', 'C07': 'bucles', 'C08': 'bucles-practica', 'C09': 'errores-programas', 'C10': 'ciudadania-digital'}

for lesson, code, suffix, part, title, challenges, games in SPECS:
    parent = PARENTS[code]
    version = f'INF-1-{code}-{suffix}-v1'
    station_prefix = part or parent
    stations = [{'id': f'{station_prefix}-{index + 1}', 'title': challenge} for index, challenge in enumerate(challenges)]
    activity = {
        'lesson': lesson, 'version': version, 'title': title, 'grade': 'Primero',
        'activity_title': f'Actividad: {title}' if part else title, 'stations': stations,
    }
    if part:
        activity.update(scope='part', parent_lesson=parent, part=part, part_title=title)
    FIRST_PATH_ACTIVITIES[lesson] = activity
    FIRST_PATH_RULES[version] = {
        station['id']: expected_for(game, final=part is None)
        for station, game in zip(stations, games)
    }
