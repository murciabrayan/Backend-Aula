"""Published version snapshots for the third first-grade class."""
SEQUENCE_ACTIVITIES = {}
SEQUENCE_RULES = {}
for slug, version, title, part_id, challenges in [
    ('instrucciones', 'INF-1-C03-final-v1', 'Ordenamos, indicamos y comprobamos', None, [
        ('Ordena una historia', {'solved': 1}), ('Elige la instrucción', {'solved': 3}), ('Programa un camino', {'solved': 1, 'tested': True}), ('Corrige y comprueba', {'solved': 1, 'tested': True, 'repaired': True}),
    ]),
    ('instrucciones-orden', 'INF-1-C03-orden-v1', 'Pasos y orden', 'orden', [
        ('Ordenamos una historia', {'solved': 2}), ('¿Qué paso falta?', {'solved': 3}),
    ]),
    ('instrucciones-claridad', 'INF-1-C03-claridad-v1', 'Instrucciones claras', 'claridad', [
        ('Elige una instrucción precisa', {'solved': 3}), ('Construye la instrucción', {'solved': 3}),
    ]),
    ('instrucciones-prueba', 'INF-1-C03-prueba-v1', 'Probamos y corregimos', 'prueba', [
        ('Programa el recorrido', {'solved': 2, 'tested': True}), ('Reparamos las instrucciones', {'solved': 2, 'tested': True, 'repaired': True}),
    ]),
]:
    stations = [{'id': f'{part_id or "secuencia"}-{i+1}', 'title': name} for i, (name, _) in enumerate(challenges)]
    data = {'lesson': slug, 'version': version, 'title': f'Algoritmos · {title}' if part_id else 'Algoritmos', 'grade': 'Primero', 'activity_title': f'Actividad: {title}' if part_id else title, 'stations': stations}
    if part_id:
        data.update(scope='part', parent_lesson='instrucciones', part=part_id, part_title=title)
    SEQUENCE_ACTIVITIES[slug] = data
    SEQUENCE_RULES[version] = {station['id']: {'completed': True, **evidence} for station, (_, evidence) in zip(stations, challenges)}

# New invitations receive varied scenarios; existing snapshots retain v1 rules.
from copy import deepcopy
for slug, original in list(SEQUENCE_ACTIVITIES.items()):
    updated = deepcopy(original)
    version = original['version'].replace('-v1', '-v2')
    updated['version'] = version
    SEQUENCE_RULES[version] = deepcopy(SEQUENCE_RULES[original['version']])
    for station in updated['stations']:
        if station['id'] == 'prueba-1' or station['id'] == 'secuencia-3':
            SEQUENCE_RULES[version][station['id']]['collected'] = True
    if slug == 'instrucciones':
        updated['stations'][0]['title'] = 'Elige los pasos necesarios'
        updated['stations'][2]['title'] = 'Recoge y entrega'
        updated['stations'][3]['title'] = 'Repara el programa'
    elif slug == 'instrucciones-prueba':
        SEQUENCE_RULES[version]['prueba-2']['solved'] = 3
        updated['stations'][0]['title'] = 'Recogemos y entregamos'
        updated['stations'][1]['title'] = 'Tres formas de reparar'
    SEQUENCE_ACTIVITIES[slug] = updated
