"""Published classroom activities for second-grade Informatics."""

SECOND_GRADE_ACTIVITIES = {}
SECOND_GRADE_RULES = {}

GAME_RULES = {
    'g2-access-order': ('organized', 2), 'g2-credential-check': ('decided', 3),
    'g2-tool-match': ('classified', 1), 'g2-drawing-plan': ('created', 2),
    'g2-folder-sort': ('organized', 2), 'g2-file-route': ('organized', 2),
    'g2-external-match': ('classified', 1), 'g2-port-choice': ('classified', 3),
    'g2-internal-match': ('classified', 1), 'g2-build-computer': ('organized', 2),
    'g2-hardware-software': ('classified', 1), 'g2-ai-decisions': ('decided', 3),
    'g2-event-match': ('classified', 1), 'g2-event-predict': ('tested', 3),
    'g2-event-program': ('programmed', 3), 'g2-multiple-events': ('classified', 1),
    'g2-event-trace': ('tested', 2), 'g2-event-repair': ('programmed', 2),
    'g2-loop-equivalence': ('programmed', 3), 'g2-loop-count': ('programmed', 3),
    'g2-loop-draw': ('created', 3), 'g2-loop-pattern': ('tested', 3),
    'g2-loop-trace': ('tested', 2), 'g2-loop-repair': ('programmed', 3),
    'g2-pattern-unit': ('classified', 3), 'g2-nested-read': ('tested', 3),
    'g2-nested-build': ('programmed', 3), 'g2-nested-draw': ('created', 3),
    'g2-nested-predict': ('tested', 3), 'g2-nested-repair': ('programmed', 3),
    'g2-condition-sort': ('classified', 2), 'g2-if-predict': ('tested', 3),
    'g2-sensor-match': ('classified', 1), 'g2-condition-cases': ('tested', 3),
    'g2-condition-program': ('programmed', 3), 'g2-condition-debug': ('programmed', 2),
    'g2-scene-place': ('created', 2), 'g2-character-route': ('programmed', 3),
    'g2-message-chain': ('programmed', 2), 'g2-sync-story': ('programmed', 2),
    'g2-game-rules': ('classified', 1), 'g2-project-builder': ('created', 2),
    'g2-known-unknown': ('decided', 3), 'g2-profile-clues': ('decided', 2),
    'g2-pressure-signs': ('decided', 2), 'g2-message-evidence': ('decided', 3),
    'g2-safety-order': ('decided', 2), 'g2-trusted-response': ('decided', 3),
}

CLASSES = [
    ('entorno-trabajo', 'C01', 'Nuestro espacio de trabajo digital', [
        ('acceso', 'Ingresamos y cuidamos una sesión', [('La ruta de ingreso', 'g2-access-order'), ('Decisiones con credenciales', 'g2-credential-check')]),
        ('produccion', 'Creamos y corregimos una producción', [('Herramientas con intención', 'g2-tool-match'), ('Del boceto al archivo', 'g2-drawing-plan')]),
        ('organizacion', 'Organizamos y recuperamos archivos', [('El archivador de la clase', 'g2-folder-sort'), ('Encontramos y renombramos', 'g2-file-route')]),
    ], [('Ingreso seguro', 'g2-access-order'), ('Producción digital', 'g2-drawing-plan'), ('Organización de archivos', 'g2-folder-sort'), ('Recuperar un trabajo', 'g2-file-route')]),
    ('componentes-programas', 'C02', 'Dentro y fuera del computador', [
        ('externos', 'Componentes que podemos ver y tocar', [('Función de cada periférico', 'g2-external-match'), ('El puerto adecuado', 'g2-port-choice')]),
        ('internos', 'Piezas que colaboran por dentro', [('El laboratorio interno', 'g2-internal-match'), ('La ruta de los datos', 'g2-build-computer')]),
        ('sistemas', 'Hardware, software e inteligencia artificial', [('¿Físico o programa?', 'g2-hardware-software'), ('Revisamos una propuesta de IA', 'g2-ai-decisions')]),
    ], [('Componentes externos', 'g2-external-match'), ('Componentes internos', 'g2-internal-match'), ('Hardware y software', 'g2-hardware-software'), ('Uso responsable de IA', 'g2-ai-decisions')]),
    ('eventos', 'C03', 'Programas que despiertan', [
        ('eventos', 'Qué hace comenzar un programa', [('Señal y respuesta', 'g2-event-match'), ('¿Qué ocurrirá?', 'g2-event-predict')]),
        ('secuencias', 'Construimos respuestas a eventos', [('Construye la respuesta', 'g2-event-program'), ('Tres señales, tres tareas', 'g2-multiple-events')]),
        ('pruebas', 'Seguimos y reparamos la ejecución', [('Mesa de trazas', 'g2-event-trace'), ('Taller de eventos', 'g2-event-repair')]),
    ], [('Evento y respuesta', 'g2-event-match'), ('Predicción', 'g2-event-predict'), ('Programa con evento', 'g2-event-program'), ('Traza y reparación', 'g2-event-repair')]),
    ('bucles-dibujan', 'C04', 'Bucles que dibujan', [
        ('repeticion', 'Comprimimos sin cambiar el resultado', [('¿Lista o bucle?', 'g2-loop-equivalence'), ('Ajustamos las vueltas', 'g2-loop-count')]),
        ('dibujos', 'Dibujamos con repeticiones', [('El telar de repeticiones', 'g2-loop-draw'), ('Predice el dibujo', 'g2-loop-pattern')]),
        ('depuracion', 'Seguimos y corregimos bucles', [('La lupa de las vueltas', 'g2-loop-trace'), ('Reparamos la repetición', 'g2-loop-repair')]),
    ], [('Equivalencia', 'g2-loop-equivalence'), ('Cantidad', 'g2-loop-count'), ('Dibujo repetido', 'g2-loop-draw'), ('Reparación', 'g2-loop-repair')]),
    ('bucles-anidados', 'C05', 'Patrones dentro de patrones', [
        ('patrones', 'Encontramos unidades y grupos', [('Encuentra la unidad', 'g2-pattern-unit'), ('Leemos dos niveles', 'g2-nested-read')]),
        ('anidados', 'Construimos bucles de dos niveles', [('Arquitectos de bucles', 'g2-nested-build'), ('El tapiz programado', 'g2-nested-draw')]),
        ('comprobacion', 'Predecimos y reparamos niveles', [('¿Qué cambia?', 'g2-nested-predict'), ('El taller de dos niveles', 'g2-nested-repair')]),
    ], [('Unidad del patrón', 'g2-pattern-unit'), ('Leer dos niveles', 'g2-nested-read'), ('Construir anidamiento', 'g2-nested-build'), ('Reparar niveles', 'g2-nested-repair')]),
    ('condicionales', 'C06', 'Decisiones en el programa', [
        ('condiciones', 'Si se cumple, entonces actuamos', [('Verdadero o falso', 'g2-condition-sort'), ('Predice la decisión', 'g2-if-predict')]),
        ('sensores', 'Leemos señales del entorno', [('Señal y respuesta', 'g2-sensor-match'), ('Dos casos para una regla', 'g2-condition-cases')]),
        ('combinacion', 'Construimos y depuramos reglas', [('El constructor de reglas', 'g2-condition-program'), ('El inspector del huerto', 'g2-condition-debug')]),
    ], [('Verdadero o falso', 'g2-condition-sort'), ('Predecir decisiones', 'g2-if-predict'), ('Programar regla', 'g2-condition-program'), ('Depurar regla', 'g2-condition-debug')]),
    ('historias-bloques', 'C07', 'Creamos historias con bloques', [
        ('escenario', 'Preparamos escena y movimiento', [('Directores de escena', 'g2-scene-place'), ('Movimiento con propósito', 'g2-character-route')]),
        ('mensajes', 'Coordinamos personajes con mensajes', [('La ruta del mensaje', 'g2-message-chain'), ('Personajes coordinados', 'g2-sync-story')]),
        ('proyecto', 'Diseñamos un juego o historia breve', [('Reglas y bloques', 'g2-game-rules'), ('Mesa de diseño', 'g2-project-builder')]),
    ], [('Preparar escena', 'g2-scene-place'), ('Mover personaje', 'g2-character-route'), ('Coordinar mensajes', 'g2-sync-story'), ('Diseñar proyecto', 'g2-project-builder')]),
    ('confianza-digital', 'C08', 'Detectives de confianza digital', [
        ('identidad', 'Conocidos, desconocidos y verificación', [('¿Conocido o verificado?', 'g2-known-unknown'), ('Mesa de pistas', 'g2-profile-clues')]),
        ('senales', 'Reconocemos presión y engaño', [('Radar de señales', 'g2-pressure-signs'), ('Comparamos mensajes', 'g2-message-evidence')]),
        ('decisiones', 'Actuamos con acompañamiento', [('El plan en orden', 'g2-safety-order'), ('Acompañamos y pedimos ayuda', 'g2-trusted-response')]),
    ], [('Verificar identidad', 'g2-known-unknown'), ('Reunir pistas', 'g2-profile-clues'), ('Reconocer presión', 'g2-pressure-signs'), ('Actuar con ayuda', 'g2-trusted-response')]),
]


def expected_for(game, final=False):
    flag, solved = GAME_RULES[game]
    return {'completed': True, 'solved': 1 if final else solved, flag: True}


for parent, code, title, parts, final_games in CLASSES:
    final_version = f'INF-2-{code}-final-v1'
    final_stations = [
        {'id': f'{parent}-{index + 1}', 'title': challenge}
        for index, (challenge, _game) in enumerate(final_games)
    ]
    SECOND_GRADE_ACTIVITIES[parent] = {
        'lesson': parent, 'version': final_version, 'title': title, 'grade': 'Segundo',
        'activity_title': title, 'stations': final_stations,
    }
    SECOND_GRADE_RULES[final_version] = {
        station['id']: expected_for(game, final=True)
        for station, (_challenge, game) in zip(final_stations, final_games)
    }

    for part, part_title, games in parts:
        lesson = f'{parent}-{part}'
        version = f'INF-2-{code}-{part}-v1'
        stations = [
            {'id': f'{part}-{index + 1}', 'title': challenge}
            for index, (challenge, _game) in enumerate(games)
        ]
        SECOND_GRADE_ACTIVITIES[lesson] = {
            'lesson': lesson, 'version': version, 'title': title, 'grade': 'Segundo',
            'activity_title': f'Actividad: {part_title}', 'stations': stations,
            'scope': 'part', 'parent_lesson': parent, 'part': part, 'part_title': part_title,
        }
        SECOND_GRADE_RULES[version] = {
            station['id']: expected_for(game)
            for station, (_challenge, game) in zip(stations, games)
        }
