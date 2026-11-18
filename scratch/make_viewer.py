import json

with open('datos/vista_previa.geojson', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Bus Portoviejo - Ruta 6 (Bus Rojo)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body, html {{ margin: 0; padding: 0; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    #map {{ width: 100%; height: 100%; }}
    .header {{
      position: absolute; top: 16px; left: 60px; z-index: 1000;
      background: rgba(255, 255, 255, 0.95); padding: 12px 20px;
      border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);
      border-left: 6px solid #E63946; max-width: 420px;
    }}
    .badge {{
      display: inline-block; background: #E63946; color: white;
      font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px;
      letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px;
    }}
    h1 {{ margin: 0 0 4px 0; font-size: 20px; color: #15201A; }}
    p {{ margin: 0; font-size: 13px; color: #5A6960; line-height: 1.4; }}
    .stats {{ margin-top: 8px; font-size: 12px; font-weight: 600; color: #0E3B3A; }}
  </style>
</head>
<body>
  <div class="header">
    <span class="badge">GTFS Fase 1 Generado</span>
    <h1>Ruta 6 · Bus Rojo</h1>
    <p>Portoviejo (Manabí, Ecuador) · Trazado oficial generado a partir de tu mapa.</p>
    <div class="stats">
      📍 Ida: 3.8 km (7 paradas) · ⏱️ ~16 min<br>
      🔄 Vuelta: 27.8 km (15 paradas) · ⏱️ ~109 min
    </div>
  </div>
  <div id="map"></div>
  <script>
    const map = L.map('map').setView([-1.055, -80.455], 13);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '© Colaboradores de OpenStreetMap'
    }}).addTo(map);

    const data = {json.dumps(geojson_data)};

    const geoLayer = L.geoJSON(data, {{
      style: function (feature) {{
        const isVuelta = feature.properties && feature.properties.name && feature.properties.name.includes('vuelta');
        return {{
          color: isVuelta ? '#C1121F' : '#E63946',
          weight: isVuelta ? 4 : 5,
          opacity: 0.85,
          dashArray: isVuelta ? '6, 6' : null
        }};
      }},
      pointToLayer: function (feature, latlng) {{
        return L.circleMarker(latlng, {{
          radius: 7,
          fillColor: '#FFFFFF',
          color: '#E63946',
          weight: 3,
          opacity: 1,
          fillOpacity: 1
        }});
      }},
      onEachFeature: function (feature, layer) {{
        if (feature.properties && feature.properties.name) {{
          layer.bindPopup('<b>' + feature.properties.name + '</b>');
        }}
      }}
    }}).addTo(map);

    map.fitBounds(geoLayer.getBounds(), {{ padding: [40, 40] }});
  </script>
</body>
</html>
"""

with open('visor_ruta6.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Generated visor_ruta6.html successfully.')
