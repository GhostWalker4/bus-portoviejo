import json
import csv
from pathlib import Path

# Load original umap
with open('datos/bus-portoviejo.umap', 'r', encoding='utf-8') as f:
    orig = json.load(f)

lines = [f for f in orig['layers'][0]['features'] if f['geometry']['type'] == 'LineString']
lines = sorted(lines, key=lambda x: len(x['geometry']['coordinates']), reverse=True)
ida_coords = lines[1]['geometry']['coordinates']
vuelta_coords = lines[0]['geometry']['coordinates']

paradas_ida = [
    ("01 San Gregorio", -80.473872, -1.070139),
    ("02 Av. Metropolitana - Shopping", -80.467866, -1.063437),
    ("03 Av. 15 de Abril", -80.464221, -1.062174),
    ("04 Terminal Terrestre", -80.458275, -1.061284),
    ("05 Av. Pedro Gual", -80.459251, -1.061582),
    ("06 Av. del Ejército", -80.463824, -1.059348),
    ("07 Centro - Calle Córdova", -80.461418, -1.056157),
]

paradas_vuelta = [
    ("01 Centro - Calle Córdova", -80.461421, -1.056154),
    ("02 Av. Ramos Iduarte", -80.458161, -1.052992),
    ("03 UTM - Av. Universitaria", -80.456966, -1.043756),
    ("04 Los Tamarindos", -80.447452, -1.048717),
    ("05 Av. Pedro Gual Este", -80.434985, -1.045038),
    ("06 Paso Lateral Este", -80.428784, -1.039417),
    ("07 Vía a Crucita", -80.420598, -1.035019),
    ("08 Retorno Vía Crucita", -80.399044, -1.034643),
    ("09 Vía a Portoviejo", -80.414793, -1.035620),
    ("10 Paso Lateral Norte", -80.431026, -1.040887),
    ("11 Hospital Verdi Cevallos", -80.445725, -1.051131),
    ("12 Av. Manabí", -80.458138, -1.054124),
    ("13 Parque Central", -80.458288, -1.060823),
    ("14 Av. Metropolitana", -80.478137, -1.068240),
    ("15 San Gregorio", -80.473856, -1.070145),
]

features_ida = [
    {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": ida_coords
        },
        "properties": {
            "name": "Ruta 6 - ida"
        }
    }
]
for name, lon, lat in paradas_ida:
    features_ida.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "name": name
        }
    })

features_vuelta = [
    {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": vuelta_coords
        },
        "properties": {
            "name": "Ruta 6 - vuelta"
        }
    }
]
for name, lon, lat in paradas_vuelta:
    features_vuelta.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "name": name
        }
    })

new_umap = {
    "type": "umap",
    "uri": orig.get("uri", "https://umap.openstreetmap.fr/es/map/bus-portoviejo_1486568"),
    "properties": {
        "name": "Bus Portoviejo - Paradas y Trazados",
        "description": "Rutas urbanas de Portoviejo - Fase 1",
        "zoom": 14
    },
    "layers": [
        {
            "type": "FeatureCollection",
            "features": features_ida,
            "properties": {
                "name": "Ruta 6 - ida",
                "color": "#E63946"
            }
        },
        {
            "type": "FeatureCollection",
            "features": features_vuelta,
            "properties": {
                "name": "Ruta 6 - vuelta",
                "color": "#E63946"
            }
        }
    ]
}

Path('datos/mapas').mkdir(parents=True, exist_ok=True)
with open('datos/mapas/bus-portoviejo.umap', 'w', encoding='utf-8') as f:
    json.dump(new_umap, f, indent=2, ensure_ascii=False)
print('Generated datos/mapas/bus-portoviejo.umap successfully.')

# Update rutas.csv
csv_path = Path('datos/rutas.csv')
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ruta', 'nombre', 'cooperativa', 'color', 'frecuencia_min', 'desde', 'hasta', 'dias', 'velocidad_kmh'])
    writer.writerow(['6', 'Ruta 6 (Bus Rojo)', 'Cooperativa Ciudad del Valle', 'E63946', '12', '06:00', '20:00', 'todos', '16'])
print('Generated datos/rutas.csv successfully.')
