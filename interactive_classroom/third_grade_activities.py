"""Published classroom activities for third-grade Informatics."""

THIRD_GRADE_ACTIVITIES = {}
THIRD_GRADE_RULES = {}

CLASSES = [
    ('proyecto-archivos', 'C01', 'Organizamos un proyecto digital', [
        ('estructura', 'Diseñamos la estructura del proyecto', [('Carpetas que responden al encargo', 'g3-project-criteria'), ('Arquitectura del proyecto', 'g3-project-structure')]),
        ('versiones', 'Controlamos cambios y versiones', [('Mesa de versiones', 'g3-version-sort'), ('Plan de cambios seguros', 'g3-version-plan')]),
        ('recuperacion', 'Buscamos, recuperamos y explicamos', [('Investigación de archivos', 'g3-recovery-clues'), ('Ruta de recuperación', 'g3-recovery-route')]),
    ], [('Estructura del encargo', 'g3-project-criteria'), ('Versiones seguras', 'g3-version-plan'), ('Pistas de recuperación', 'g3-recovery-clues'), ('Ruta explicada', 'g3-recovery-route')]),
    ('sistema-computador', 'C02', 'Diseñamos un sistema para una tarea', [
        ('necesidades', 'De la necesidad a los componentes', [('Componentes con propósito', 'g3-system-needs'), ('Diseñador de sistemas', 'g3-system-design')]),
        ('flujo', 'Seguimos el flujo de información', [('Ruta de los datos', 'g3-data-route'), ('Diagnóstico del sistema', 'g3-flow-debug')]),
        ('elecciones', 'Comparamos soluciones digitales', [('Comparador de soluciones', 'g3-solution-compare'), ('Mesa de revisión de IA', 'g3-ai-review')]),
    ], [('Componentes con propósito', 'g3-system-needs'), ('Diseño del sistema', 'g3-system-design'), ('Flujo de datos', 'g3-data-route'), ('Elección responsable', 'g3-ai-review')]),
    ('eventos-soluciones', 'C03', 'Diseñamos respuestas a eventos', [
        ('encargo', 'Leemos el encargo y definimos la respuesta', [('Del encargo al programa', 'g3-event-brief'), ('Constructor de respuestas', 'g3-event-build')]),
        ('coordinacion', 'Coordinamos varios eventos', [('Mapa de coordinación', 'g3-event-coordination'), ('Orquesta de eventos', 'g3-event-orchestra')]),
        ('alternativas', 'Comparamos y depuramos soluciones', [('Inspector de ejecuciones', 'g3-event-trace'), ('Dos programas, una meta', 'g3-event-alternative')]),
    ], [('Interpretar el encargo', 'g3-event-brief'), ('Construir respuesta', 'g3-event-build'), ('Coordinar eventos', 'g3-event-orchestra'), ('Comparar soluciones', 'g3-event-alternative')]),
    ('bucles-eficientes', 'C04', 'Programas más cortos, mismas metas', [
        ('estrategias', 'Comparamos estrategias de repetición', [('¿Lista o bucle?', 'g3-loop-strategy'), ('Taller de simplificación', 'g3-loop-rewrite')]),
        ('construccion', 'Construimos bucles eficientes', [('Tramos del programa', 'g3-loop-segments'), ('Constructor de bucles', 'g3-loop-builder')]),
        ('depuracion', 'Probamos y corregimos cantidades', [('Lupa de repeticiones', 'g3-loop-diagnosis'), ('Reparación con prueba', 'g3-loop-repair')]),
    ], [('Elegir estrategia', 'g3-loop-strategy'), ('Simplificar', 'g3-loop-rewrite'), ('Diagnosticar', 'g3-loop-diagnosis'), ('Reparar con prueba', 'g3-loop-repair')]),
    ('patrones-programados', 'C05', 'Diseñamos patrones con bucles', [
        ('diseno', 'Descomponemos una figura', [('Laboratorio de unidades', 'g3-pattern-unit'), ('Plano del patrón', 'g3-pattern-plan')]),
        ('anidamiento', 'Programamos dos niveles', [('Rayos X del patrón', 'g3-nested-read'), ('Arquitectos de anidamiento', 'g3-nested-build')]),
        ('transformacion', 'Predecimos y transformamos patrones', [('Simulador de cambios', 'g3-pattern-predict'), ('Editor de patrones', 'g3-pattern-transform')]),
    ], [('Descomponer figura', 'g3-pattern-unit'), ('Diseñar patrón', 'g3-pattern-plan'), ('Programar niveles', 'g3-nested-build'), ('Transformar', 'g3-pattern-transform')]),
    ('decisiones-casos', 'C06', 'Programas que deciden y explican', [
        ('reglas', 'Escribimos reglas precisas', [('Clínica de reglas', 'g3-rule-precision'), ('Constructor de decisiones', 'g3-rule-builder')]),
        ('casos', 'Probamos casos y casos límite', [('Mesa de casos', 'g3-case-table'), ('Detectives del límite', 'g3-edge-cases')]),
        ('correccion', 'Corregimos decisiones del programa', [('Traza de decisiones', 'g3-condition-trace'), ('Taller de condiciones', 'g3-condition-repair')]),
    ], [('Precisar regla', 'g3-rule-precision'), ('Construir decisión', 'g3-rule-builder'), ('Probar límites', 'g3-edge-cases'), ('Corregir condición', 'g3-condition-repair')]),
    ('proyecto-interactivo', 'C07', 'Creamos un juego interactivo', [
        ('plan', 'Planeamos el juego', [('Requisitos del juego', 'g3-game-requirements'), ('Mesa de diseño', 'g3-game-plan')]),
        ('programacion', 'Programamos personajes y mensajes', [('Equipo de personajes', 'g3-game-roles'), ('Programador de escenas', 'g3-game-program')]),
        ('pruebas', 'Probamos, depuramos y mejoramos', [('Laboratorio de pruebas', 'g3-game-test'), ('Sala de depuración', 'g3-game-debug')]),
    ], [('Definir requisitos', 'g3-game-requirements'), ('Planear prototipo', 'g3-game-plan'), ('Programar interacción', 'g3-game-program'), ('Depurar juego', 'g3-game-debug')]),
    ('investigacion-digital', 'C08', 'Investigamos antes de confiar', [
        ('pistas', 'Reunimos pistas de confianza', [('Tablero de pistas', 'g3-trust-clues'), ('Afirmación o evidencia', 'g3-trust-claim')]),
        ('verificacion', 'Verificamos por otro canal', [('Rutas de verificación', 'g3-verify-channel'), ('Comparador de mensajes', 'g3-verify-message')]),
        ('respuesta', 'Decidimos y pedimos ayuda', [('Decisiones según el riesgo', 'g3-response-risk'), ('Plan de acompañamiento', 'g3-help-plan')]),
    ], [('Reunir pistas', 'g3-trust-clues'), ('Distinguir evidencia', 'g3-trust-claim'), ('Verificar canal', 'g3-verify-channel'), ('Actuar con ayuda', 'g3-help-plan')]),
]

FLAGS = {
    'project-criteria':'organized','project-structure':'organized','version-sort':'classified','version-plan':'decided','recovery-clues':'tested','recovery-route':'organized',
    'system-needs':'classified','system-design':'created','data-route':'organized','flow-debug':'tested','solution-compare':'decided','ai-review':'decided',
    'event-brief':'classified','event-build':'programmed','event-coordination':'classified','event-orchestra':'created','event-trace':'tested','event-alternative':'decided',
    'loop-strategy':'decided','loop-rewrite':'programmed','loop-segments':'classified','loop-builder':'programmed','loop-diagnosis':'tested','loop-repair':'programmed',
    'pattern-unit':'classified','pattern-plan':'created','nested-read':'tested','nested-build':'programmed','pattern-predict':'tested','pattern-transform':'created',
    'rule-precision':'classified','rule-builder':'created','case-table':'tested','edge-cases':'tested','condition-trace':'tested','condition-repair':'programmed',
    'game-requirements':'classified','game-plan':'created','game-roles':'classified','game-program':'programmed','game-test':'tested','game-debug':'programmed',
    'trust-clues':'decided','trust-claim':'classified','verify-channel':'decided','verify-message':'decided','response-risk':'decided','help-plan':'decided',
}

def expected_for(game, final=False):
    flag = FLAGS[game.removeprefix('g3-')]
    return {'completed': True, 'solved': 1 if final else 2, flag: True}

for parent, code, title, parts, final_games in CLASSES:
    final_version = f'INF-3-{code}-final-v1'
    final_stations = [{'id': f'{parent}-{index + 1}', 'title': challenge} for index, (challenge, _game) in enumerate(final_games)]
    THIRD_GRADE_ACTIVITIES[parent] = {'lesson': parent, 'version': final_version, 'title': title, 'grade': 'Tercero', 'activity_title': title, 'stations': final_stations}
    THIRD_GRADE_RULES[final_version] = {station['id']: expected_for(game, final=True) for station, (_challenge, game) in zip(final_stations, final_games)}
    for part, part_title, games in parts:
        lesson = f'{parent}-{part}'
        version = f'INF-3-{code}-{part}-v1'
        stations = [{'id': f'{part}-{index + 1}', 'title': challenge} for index, (challenge, _game) in enumerate(games)]
        THIRD_GRADE_ACTIVITIES[lesson] = {'lesson': lesson, 'version': version, 'title': title, 'grade': 'Tercero', 'activity_title': f'Actividad: {part_title}', 'stations': stations, 'scope': 'part', 'parent_lesson': parent, 'part': part, 'part_title': part_title}
        THIRD_GRADE_RULES[version] = {station['id']: expected_for(game) for station, (_challenge, game) in zip(stations, games)}
