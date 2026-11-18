import urllib.request
import json
import time

def get_name(lat, lon):
    url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18'
    req = urllib.request.Request(url, headers={'User-Agent': 'bus-portoviejo/1.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            addr = data.get('address', {})
            road = addr.get('road') or addr.get('pedestrian') or ''
            poi = addr.get('amenity') or addr.get('shop') or addr.get('tourism') or addr.get('building') or ''
            sub = addr.get('suburb') or addr.get('neighbourhood') or ''
            res = poi if poi else road
            if sub:
                res += f' - {sub}'
            return res.strip() or 'Portoviejo'
    except Exception as e:
        return 'Parada ' + str(e)

coords_ida = [
    (-1.070139, -80.473872),
    (-1.063437, -80.467866),
    (-1.062174, -80.464221),
    (-1.061284, -80.458275),
    (-1.061582, -80.459251),
    (-1.059348, -80.463824),
    (-1.056157, -80.461418),
]

coords_vuelta = [
    (-1.056154, -80.461421),
    (-1.052992, -80.458161),
    (-1.043756, -80.456966),
    (-1.048717, -80.447452),
    (-1.045038, -80.434985),
    (-1.039417, -80.428784),
    (-1.035019, -80.420598),
    (-1.034643, -80.399044),
    (-1.035620, -80.414793),
    (-1.040887, -80.431026),
    (-1.051131, -80.445725),
    (-1.054124, -80.458138),
    (-1.060823, -80.458288),
    (-1.068240, -80.478137),
    (-1.070145, -80.473856),
]

print('--- IDA ---')
for i, (lat, lon) in enumerate(coords_ida):
    name = get_name(lat, lon)
    print(f'Ida {i+1:02d}: {name} ({lat}, {lon})')
    time.sleep(0.5)

print('\n--- VUELTA ---')
for i, (lat, lon) in enumerate(coords_vuelta):
    name = get_name(lat, lon)
    print(f'Vuelta {i+1:02d}: {name} ({lat}, {lon})')
    time.sleep(0.5)
