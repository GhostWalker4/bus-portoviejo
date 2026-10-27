"""Prepara los datos del prototipo (ruta, paradas, mapa base) en data.json. Luego se ejecuta inject.py."""
import json, math, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # rutas relativas a esta carpeta

LAT0, LON0 = -1.0528, -80.4600   # origen para cuantizar coordenadas
Q = 1e5                          # 1 unidad = 0.00001° (~1.1 m)

def haversine(a, b):
    R = 6371000
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def dp(pts, tol):
    """Douglas-Peucker sobre (lat, lon)."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[1] - a[1], b[0] - a[0]
    L = math.hypot(dx, dy) or 1e-12
    idx, dmax = 0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = abs(dy * (p[1] - a[1]) - dx * (p[0] - a[0])) / L
        if d > dmax:
            idx, dmax = i, d
    if dmax <= tol:
        return [a, b]
    return dp(pts[:idx + 1], tol)[:-1] + dp(pts[idx:], tol)

def enc(pts):
    out, plat, plon = [], round((LAT0) * Q), round((LON0) * Q)
    for la, lo in pts:
        qa, qo = round(la * Q), round(lo * Q)
        out += [qa - plat, qo - plon]
        plat, plon = qa, qo
    return out

# --- Ruta ---
route = json.load(open('route.json', encoding='utf-8'))['routes'][0]
coords = [(c[1], c[0]) for c in route['geometry']['coordinates']]
dedup = [coords[0]]
for c in coords[1:]:
    if haversine(dedup[-1], c) > 0.5:
        dedup.append(c)
if haversine(dedup[0], dedup[-1]) < 1:
    dedup.pop()
coords = dedup
cum = [0.0]
for a, b in zip(coords, coords[1:]):
    cum.append(cum[-1] + haversine(a, b))
total = cum[-1] + haversine(coords[-1], coords[0])

stops_raw = json.load(open('stops_snapped.json', encoding='utf-8'))
# ubicar cada parada sobre la ruta, avanzando en orden
stops, start = [], 0
for name, la, lo, street in stops_raw:
    best = None
    for i in range(start, len(coords)):
        d = haversine((la, lo), coords[i])
        if best is None or d < best[0]:
            best = (d, i)
        if best[0] < 15 and d > 300:
            break
    d, i = best
    stops.append({'name': name, 'street': street, 'at': round(cum[i], 1), 'lat': coords[i][0], 'lon': coords[i][1]})
    start = i
    print(f'{name:28s} at {cum[i]:7.0f} m (off {d:.0f} m)')

# tramos de calle por los que pasa (para mostrar "va por ...")
legs = route['legs']
streets = []
for k, leg in enumerate(legs):
    a = stops[k]['at']
    b = stops[k + 1]['at'] if k + 1 < len(stops) else total
    osrm_len = sum(s['distance'] for s in leg['steps']) or 1
    acc = 0
    for s in leg['steps']:
        if s['distance'] <= 0:
            continue
        name = s['name'] if s['name'] and 'pero ahí' not in s['name'] and 'Tennis' not in s['name'] else None
        if name:
            pos = a + (b - a) * acc / osrm_len
            if not streets or streets[-1][1] != name:
                streets.append([round(pos, 1), name])
        acc += s['distance']

# --- Mapa base ---
base = json.load(open('base.json', encoding='utf-8'))
cls = {'trunk': 4, 'trunk_link': 3, 'primary': 4, 'primary_link': 3, 'secondary': 3, 'secondary_link': 2,
       'tertiary': 2, 'tertiary_link': 2, 'residential': 1, 'unclassified': 1, 'living_street': 1}
roads, river, parks = [], [], []
named_major = {}
for e in base['elements']:
    t = e['tags']
    g = [(p['lat'], p['lon']) for p in e.get('geometry', [])]
    if len(g) < 2:
        continue
    if 'highway' in t:
        c = cls[t['highway']]
        roads.append([c] + enc(dp(g, 0.000025)))
        nm = t.get('name')
        if nm and c >= 3 and 'Tennis' not in nm:
            # solo la parte visible alrededor de la ruta
            run = []
            for p in g + [None]:
                if p and -1.068 < p[0] < -1.040 and -80.474 < p[1] < -80.444:
                    run.append(p)
                    continue
                if len(run) > 1:
                    L = sum(haversine(a, b) for a, b in zip(run, run[1:]))
                    named_major.setdefault(nm, []).append((L, run))
                run = []
    elif t.get('waterway') == 'river':
        river.append(enc(dp(g, 0.00004)))
    elif t.get('leisure') == 'park':
        if g[0] == g[-1]:
            parks.append(enc(dp(g, 0.00002)))

# etiquetas para avenidas principales: punto medio del tramo más largo
labels = []
for nm, segs in named_major.items():
    L, g = max(segs)
    if L < 350:
        continue
    half, acc = L / 2, 0
    for a, b in zip(g, g[1:]):
        d = haversine(a, b)
        if acc + d >= half:
            ang = math.degrees(math.atan2(-(b[0] - a[0]), (b[1] - a[1]) * math.cos(math.radians(a[0]))))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            labels.append([nm.replace('Avenida', 'Av.'), round((a[0] + b[0]) / 2, 6), round((a[1] + b[1]) / 2, 6), round(ang)])
            break
        acc += d

data = {
    'origin': [LAT0, LON0], 'q': Q,
    'route': enc(coords), 'total': round(total, 1),
    'stops': stops, 'streets': streets,
    'roads': roads, 'river': river, 'parks': parks, 'labels': labels,
}
js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
print('ruta', round(total), 'm,', len(coords), 'puntos; calles', len(roads), '; json', len(js) // 1024, 'KB; etiquetas', len(labels))
open('data.json', 'w', encoding='utf-8').write(js)
