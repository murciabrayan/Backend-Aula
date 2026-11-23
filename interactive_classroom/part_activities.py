"""Fixed, versioned exercise bundles for the end of each explanation."""


def part(parent, part_id, version, title, stations):
    parent_title = 'Uso del teclado y del mouse' if parent == 'partes-del-computador' else 'El escritorio y sus iconos'
    activity = {
        'lesson': f'{parent}-{part_id}', 'version': version, 'scope': 'part',
        'parent_lesson': parent, 'part': part_id, 'part_title': title,
        'title': f'{parent_title} · {title}', 'grade': 'Primero',
        'activity_title': f'Actividad: {title}',
        'stations': [{'id': f'{part_id}-{i+1}', 'title': name} for i, (name, _) in enumerate(stations)],
    }
    rules = {f'{part_id}-{i+1}': {'completed': True, **evidence} for i, (_, evidence) in enumerate(stations)}
    return activity, rules


PART_ACTIVITIES = {}
PART_RULES = {}
for args in [
    ('partes-del-computador', 'monitor', 'INF-1-C01-monitor-v1', 'La pantalla', [
        ('¿Qué muestra la pantalla?', {'rounds': 6}), ('¿Qué cambió en la escena?', {'scenes': 4}), ('Encuentra las parejas', {'levels': 2, 'pairs': 6}),
    ]),
    ('partes-del-computador', 'mouse', 'INF-1-C01-mouse-v1', 'El mouse', [
        ('Descubre el dibujo', {'zones': 12}), ('Dibujamos punto por punto', {'drawings': 2, 'points': 10}), ('Cuidemos el jardín', {'actions': 3}), ('Reconstruimos la ilustración', {'levels': 2, 'pieces': 6}),
    ]),
    ('partes-del-computador', 'keyboard', 'INF-1-C01-keyboard-v1', 'El teclado', [
        ('Encuentra la tecla', {'models': 6}), ('Escribimos y corregimos', {'models': 3}), ('Caminos con objetivos', {'levels': 2, 'goal': True, 'key': True}),
    ]),
    ('escritorio', 'escritorio', 'INF-1-C02-escritorio-v1', 'El escritorio', [
        ('Encuentra el icono', {'found': 4}), ('Un escritorio diferente', {'actions': 4}),
    ]),
    ('escritorio', 'programas', 'INF-1-C02-programas-v1', 'Iconos y programas', [
        ('La herramienta adecuada', {'opened': 2}), ('Creamos dentro de un programa', {'drawn': True, 'stamps': 2}), ('Herramientas, carpetas y trabajos', {'placed': 4}),
    ]),
    ('escritorio', 'ventanas', 'INF-1-C02-ventanas-v1', 'Ventanas y trabajos', [
        ('Cada control tiene una función', {'actions': 5}), ('Encuentra el archivo', {'found': 2}),
    ]),
    ('partes-del-computador', 'monitor', 'INF-1-MK-mouse-v2', 'Mouse', [
        ('Descubre el dibujo', {'zones': 12}),
    ]),
    ('partes-del-computador', 'mouse', 'INF-1-MK-mouse2-v2', 'Mouse: segunda parte', [
        ('Dibujamos punto por punto', {'drawings': 2, 'points': 10}),
        ('Cuidemos el jardín', {'actions': 3}),
        ('Reconstruimos la ilustración', {'levels': 2, 'pieces': 6}),
    ]),
    ('partes-del-computador', 'keyboard', 'INF-1-MK-keyboard-v2', 'Teclado', [
        ('Encuentra la tecla', {'models': 6}),
    ]),
]:
    activity, rules = part(*args)
    PART_ACTIVITIES[activity['lesson']] = activity
    PART_RULES[activity['version']] = rules
