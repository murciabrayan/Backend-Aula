"""Fixed activities for the fifth first-grade class: executable arrow programs."""

PROGRAMMING_ACTIVITIES = {}
PROGRAMMING_RULES = {}

for slug, suffix, part, title, challenges in [
    ('programacion-flechas', 'final', None, 'Bloques de dirección', [
        ('Predice la llegada', {'solved': 1, 'executed': True}),
        ('Programa el puente', {'solved': 1, 'delivered': True}),
        ('Recoge y entrega', {'solved': 1, 'collected': True, 'crossed': True}),
        ('Repara la ruta', {'solved': 1, 'repaired': True, 'tested': True}),
    ]),
    ('programacion-flechas-bloques', 'bloques', 'bloques', 'Bloques que dan instrucciones', [
        ('El bloque que falta', {'solved': 4}),
        ('¿Dónde terminará?', {'solved': 2, 'executed': True}),
    ]),
    ('programacion-flechas-construimos', 'construimos', 'construimos', 'Construimos y ejecutamos', [
        ('El correo del bosque', {'solved': 2, 'delivered': True}),
        ('La ruta de las bayas', {'solved': 2, 'collected': True, 'crossed': True}),
    ]),
    ('programacion-flechas-corregimos', 'corregimos', 'corregimos', 'Probamos y corregimos', [
        ('Inspectores del programa', {'solved': 2, 'inspected': True, 'tested': True}),
        ('Taller de reparación', {'solved': 2, 'repaired': True, 'tested': True}),
    ]),
]:
    version = f'INF-1-C05-{suffix}-v1'
    stations = [{'id': f'{part or "programacion"}-{index + 1}', 'title': name} for index, (name, _) in enumerate(challenges)]
    activity = {
        'lesson': slug, 'version': version, 'title': title, 'grade': 'Primero',
        'activity_title': f'Actividad: {title}' if part else title, 'stations': stations,
    }
    if part:
        activity.update(scope='part', parent_lesson='programacion-flechas', part=part, part_title=title)
    PROGRAMMING_ACTIVITIES[slug] = activity
    PROGRAMMING_RULES[version] = {
        station['id']: {'completed': True, **evidence}
        for station, (_, evidence) in zip(stations, challenges)
    }
