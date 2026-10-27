# Bus Portoviejo

Prototipo para ver **en tiempo real dónde vienen los buses urbanos de Portoviejo** (Manabí, Ecuador) y saber si te da tiempo de salir de casa o si tienes que correr a la parada.

La idea es mostrarle al municipio y a las cooperativas que esto funciona: primero con una ruta de ejemplo, después con celulares que hacen de GPS y, más adelante, con rastreadores instalados en los buses.

## Qué hay hoy

- **Una demo simulada** ([`demo/index.html`](demo/index.html)): el mapa real de Portoviejo con una línea de ejemplo, *Circular San Gregorio – UTM*, que tiene 10 paradas y 3 buses simulados. La página calcula cuándo llega el bus a tu parada, te dice **Tranquilo / Sal ya / No llegas** según lo que tardas caminando y a qué hora llegas a tu destino. El mapa tiene dos vistas: **isométrica**, con los 7.600 edificios del centro levantados en 3D, y **cenital**, plana y vista desde arriba. Se abre con doble clic, sin instalar nada.
- **Un modo en vivo** ([`app/`](app/)): un servidor en Python que recibe la ubicación de celulares con **Traccar Client** y la muestra en el mapa al instante. Guarda cada recorrido en un CSV.
- **Un generador** ([`generador/`](generador/)): los scripts que arman el mapa y la ruta a partir de OpenStreetMap.

> La línea, sus paradas y sus horarios **son de ejemplo**. Las calles sí son reales. OpenStreetMap todavía no tiene ninguna ruta de bus de Portoviejo mapeada, así que hay que levantarlas a mano.

## Probarlo

**Demo:** abre `demo/index.html` en el navegador.

**Modo en vivo** (necesita Python 3):

```bash
python app/servidor.py
```

Abre `http://localhost:5055`. Para mover un "bus" sin salir de casa, ejecuta en otra terminal:

```bash
python app/simular_celular.py
```

Cómo conectar un celular de verdad, cómo probar en la calle con datos móviles y qué hacer si algo falla: [`app/LEEME.md`](app/LEEME.md).

## Estructura

```
app/
  servidor.py          recibe a Traccar Client, guarda recorridos y alimenta el mapa
  simular_celular.py   hace de celular para pruebas
  web/index.html       el mapa en modo en vivo (generado)
  web/ruta.json        la ruta en coordenadas (generado)
  LEEME.md             guía de pruebas paso a paso
demo/
  index.html           la demo simulada (generada)
generador/
  template.html        el código de la página (HTML, CSS y JavaScript): aquí se edita la interfaz
  targets.json         las paradas: nombre, ubicación aproximada y calle donde va
  descargar.py         baja calles, edificios y rutas de OpenStreetMap/OSRM
  snap.py              coloca cada parada sobre su calle
  build.py             arma data.json (ruta, paradas y mapa base comprimidos)
  inject.py            produce demo/index.html y app/web/
```

**Importante:** `demo/index.html` y `app/web/*` se generan. Para cambiar la interfaz, edita `generador/template.html` y ejecuta `python generador/inject.py`.

## Cambiar la ruta o las paradas

1. Edita `generador/targets.json`. Cada parada es `["Nombre", lat, lon, ["Calle donde va"]]` y deben ir en el orden en que pasa el bus.
2. Ejecuta, en este orden:

   ```bash
   python generador/snap.py
   python generador/descargar.py ruta
   python generador/build.py
   python generador/inject.py
   ```

3. Si la ruta sale de la zona del mapa, amplía `ZONA` en `descargar.py` y ejecuta antes `python generador/descargar.py mapa` y `python generador/descargar.py edificios`.

La altura de los edificios sale de OpenStreetMap cuando tiene pisos o altura (unos 200 de 7.600). Para el resto se estima en `build.py`: casas de 1 a 3 pisos y alturas típicas según el tipo de edificio. Cada piso que alguien cargue en OpenStreetMap hace el mapa más real.

Las velocidades promedio por tramo, que se usan para estimar la llegada, están en `LEG_SPEED` dentro de `template.html`. Hay un valor por cada tramo entre paradas. Hoy son inventadas; la idea es reemplazarlas por las de recorridos reales grabados con Traccar.

## Cómo colaborar

- Trabaja en una **rama** con un nombre que diga qué haces (`ruta-linea-5`, `mejor-eta`…) y abre un **pull request** a `main`.
- Si cambias `template.html` o los datos, ejecuta `python generador/inject.py` y sube también los archivos generados, para que la demo siempre funcione con doble clic.
- **No subas recorridos GPS.** La carpeta `app/recorridos/` está ignorada a propósito porque dice dónde estuvo una persona. Si hace falta compartir uno, quítale primero los tramos cerca de casas.
- Las ideas y los errores van en *Issues*.

## Próximos pasos

- [ ] Levantar el recorrido real de una línea con Traccar y reemplazar la ruta de ejemplo.
- [ ] Medir en la calle la diferencia entre la llegada estimada y la real.
- [ ] Calcular las velocidades de cada tramo a partir de los recorridos guardados.
- [ ] Varias líneas a la vez y elegir la mejor para ir de A a B.
- [ ] Contraseña o token para que solo los celulares autorizados puedan enviar posiciones.

## Créditos

- Calles, edificios, río y parques: © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), bajo licencia ODbL.
- Trazado de rutas: [OSRM](https://project-osrm.org/).
- Mapa interactivo y 3D: [MapLibre GL JS](https://maplibre.org/) (BSD-3-Clause).
- Envío de ubicación: [Traccar Client](https://www.traccar.org/client/).

## Licencia

Por ahora **no tiene licencia**: el código es de sus autores y nadie más tiene permiso de reutilizarlo. Antes de abrir el repositorio al público, conviene elegir una licencia (por ejemplo MIT).
