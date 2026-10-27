"""Ubica cada parada de targets.json sobre la calle indicada más cercana -> stops_snapped.json."""
import json, math, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # rutas relativas a esta carpeta

base = json.load(open('base.json', encoding='utf-8'))
ways = [e for e in base['elements'] if 'highway' in e['tags']]

def snap(lat, lon, names):
    best = None
    k = math.cos(math.radians(lat))
    for w in ways:
        if w['tags'].get('name') not in names:
            continue
        g = w['geometry']
        for a, b in zip(g, g[1:]):
            ax, ay = a['lon'] * k, a['lat']
            bx, by = b['lon'] * k, b['lat']
            px, py = lon * k, lat
            dx, dy = bx - ax, by - ay
            t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            qx, qy = ax + t * dx, ay + t * dy
            d = math.hypot(px - qx, py - qy) * 111320
            if best is None or d < best[0]:
                best = (d, qy, qx / k, w['tags']['name'])
    return best

# (nombre de la parada, lat, lon, calles válidas)
targets = json.load(open('targets.json', encoding='utf-8'))
out = []
for name, lat, lon, streets in targets:
    d, la, lo, st = snap(lat, lon, streets)
    print(f'{name:28s} -> {st:28s} {d:6.0f} m  {la:.6f},{lo:.6f}')
    out.append([name, round(la, 6), round(lo, 6), st])
json.dump(out, open('stops_snapped.json', 'w', encoding='utf-8'), ensure_ascii=False)
