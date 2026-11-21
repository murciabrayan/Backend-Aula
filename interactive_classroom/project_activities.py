"""Fixed activities for the first fifth-grade project class."""
PROJECT_ACTIVITIES = {}
PROJECT_RULES = {}
for slug, part, title, challenges in [
    ('proyecto', None, 'Misión de entrega autónoma', [
        ('Analiza el encargo', {'solved': 1}),
        ('Diseña la arquitectura', {'solved': 7}),
        ('Construye el programa', {'solved': 1, 'tested': True}),
        ('Supera la revisión de calidad', {'solved': 1, 'tested': True, 'repaired': True}),
    ]),
    ('proyecto-requisitos', 'requisitos', 'Del reto a los requisitos', [
        ('Analizamos encargos', {'solved': 3}),
        ('Decidimos con restricciones', {'solved': 3}),
    ]),
    ('proyecto-diseno', 'diseno', 'Descomponemos y diseñamos', [
        ('Construimos el plan', {'solved': 7}),
        ('Diseñamos casos de prueba', {'solved': 3}),
    ]),
    ('proyecto-programacion', 'programacion', 'Programamos, probamos y corregimos', [
        ('Laboratorio de coordenadas', {'solved': 3}),
        ('Construimos programas', {'solved': 2, 'tested': True}),
    ]),
]:
    version = f'INF-5-C01-{part or "final"}-v1'
    stations = [{'id': f'{part or "proyecto"}-{i+1}', 'title': name} for i, (name, _) in enumerate(challenges)]
    data = {'lesson': slug, 'version': version, 'title': f'Planeamos un proyecto · {title}' if part else 'Planeamos un proyecto', 'grade': 'Quinto', 'activity_title': f'Actividad: {title}' if part else title, 'stations': stations}
    if part:
        data.update(scope='part', parent_lesson='proyecto', part=part, part_title=title)
    PROJECT_ACTIVITIES[slug] = data
    PROJECT_RULES[version] = {station['id']: {'completed': True, **evidence} for station, (_, evidence) in zip(stations, challenges)}
