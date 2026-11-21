"""Fixed activities for the fourth first-grade class; drawings stay in the browser."""
TECHNOLOGY_ACTIVITIES = {}
TECHNOLOGY_RULES = {}
for slug, part, title, challenges in [
    ('tecnologia', None, 'Tecnología para resolver y comunicar', [
        ('Organiza el museo', {'solved': 6}),
        ('Crea una señal', {'drawn': True, 'tool': True}),
        ('Comparte tu señal', {'solved': 1}),
        ('Prepara el rincón de lectura', {'tools': 2, 'energy': True, 'tested': True}),
    ]),
    ('tecnologia-objetos', 'objetos', 'Naturaleza y objetos creados', [
        ('Clasificamos por su origen', {'solved': 8}),
        ('Reconstruimos dos inventos', {'solved': 2}),
    ]),
    ('tecnologia-necesidades', 'necesidades', 'Inventos y necesidades', [
        ('Usamos las herramientas', {'solved': 3}),
        ('Probamos fuentes de luz', {'solved': 3}),
    ]),
    ('tecnologia-informacion', 'informacion', 'Compartimos información', [
        ('Hacemos llegar los mensajes', {'solved': 3}),
        ('Reparamos la información', {'solved': 3}),
    ]),
]:
    version = f'INF-1-C04-{part or "final"}-v1'
    stations = [{'id': f'{part or "tecnologia"}-{i+1}', 'title': name} for i, (name, _) in enumerate(challenges)]
    data = {'lesson': slug, 'version': version, 'title': f'La tecnología en nuestra vida · {title}' if part else 'La tecnología en nuestra vida', 'grade': 'Primero', 'activity_title': f'Actividad: {title}' if part else title, 'stations': stations}
    if part:
        data.update(scope='part', parent_lesson='tecnologia', part=part, part_title=title)
    TECHNOLOGY_ACTIVITIES[slug] = data
    TECHNOLOGY_RULES[version] = {station['id']: {'completed': True, **evidence} for station, (_, evidence) in zip(stations, challenges)}
