"""Arma las dos versiones de la página a partir de template.html:
   - ../demo/index.html     demo simulada (la que se publica)
   - ../app/web/index.html  modo en vivo, la sirve servidor.py
"""
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # rutas relativas a esta carpeta
t = open('template.html', encoding='utf-8').read()
t = t.replace('/*__LEAFLET_CSS__*/', open('leaflet.css', encoding='utf-8').read())
data = open('data.json', encoding='utf-8').read()
t = t.replace('/*__DATA__*/null', data)

demo = t.replace("/*__MODE__*/'demo'", "'demo'")
os.makedirs('../demo', exist_ok=True)
open('../demo/index.html', 'w', encoding='utf-8').write(demo)

real = t.replace("/*__MODE__*/'demo'", "'real'")
head = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
# lo que va antes del primer <div class="app"> es cabecera (title, meta, estilos)
i = real.index('<div class="app">')
real = head + real[:i] + '</head>\n<body>\n' + real[i:] + '\n</body>\n</html>\n'
os.makedirs('../app/web', exist_ok=True)
open('../app/web/index.html', 'w', encoding='utf-8').write(real)

# la ruta en coordenadas normales, para simular_celular.py
d = json.loads(data)
la, lo = round(d['origin'][0] * d['q']), round(d['origin'][1] * d['q'])
pts = []
for k in range(0, len(d['route']), 2):
    la += d['route'][k]; lo += d['route'][k + 1]
    pts.append([la / d['q'], lo / d['q']])
json.dump({'nombre': 'Circular San Gregorio - UTM (ejemplo)', 'puntos': pts,
           'paradas': [{'nombre': s['name'], 'lat': s['lat'], 'lon': s['lon']} for s in d['stops']]},
          open('../app/web/ruta.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('demo', len(demo) // 1024, 'KB · en vivo', len(real) // 1024, 'KB')
