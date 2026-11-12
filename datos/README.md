# Datos de las rutas

Aquí van los datos de las rutas reales de la **fase 1** del roadmap: dónde para cada bus, por dónde va y cada cuánto pasa.

## Cómo se levantan

Quienes conocen las rutas **marcan las paradas en uMap**, un mapa digital colaborativo sobre OpenStreetMap, y un script las convierte en **GTFS**, el formato estándar de transporte público.

👉 **Paso a paso: [`GUIA_UMAP.md`](GUIA_UMAP.md)**

```
uMap (marcar las paradas) ──► datos/mapas/bus-portoviejo.umap ─┐
                                                                ├─► python datos/convertir_a_gtfs.py ─► datos/gtfs/
datos/rutas.csv (frecuencia, horario, cooperativa) ─────────────┘
```

## Qué hay en esta carpeta

| Archivo o carpeta | Qué es |
|---|---|
| `GUIA_UMAP.md` | cómo marcar las paradas y exportar el mapa |
| `mapas/` | el respaldo `.umap` exportado de uMap |
| `rutas.csv` | una fila por ruta: nombre, cooperativa, color, frecuencia, horario y días |
| `convertir_a_gtfs.py` | el conversor; solo usa Python, sin instalar nada |
| `gtfs/` | el resultado: el GTFS que importa el servidor en la fase 2 |
| `ejemplo/` | un mapa **inventado** para probar el conversor; sus rutas no existen |
| `test_conversor.py` | las pruebas del conversor: `python -m unittest discover -s datos` |

El conversor también genera `vista_previa.geojson` (para ver el resultado en <https://geojson.io>) y `.cache_osrm.json`. No se suben: cada uno los regenera.

Para probarlo con el ejemplo:

```bash
python datos/convertir_a_gtfs.py --mapas datos/ejemplo --rutas datos/ejemplo/rutas.csv --salida datos/ejemplo/gtfs
```

## Más adelante: corregir los tiempos

Los tiempos entre paradas salen estimados de la distancia y de una velocidad promedio. Para afinarlos, alguien viaja una vez en cada ruta grabando con **GPSLogger** (Android, gratis). Si se graba, el archivo va en `datos/recorridos/` con nombre `ruta-<número>_<ida|vuelta>_<AAAA-MM-DD>_<HHMM>.gpx`.

**Antes de subir un recorrido, recorta los tramos cercanos a casas** (por ejemplo, en <https://gpx.studio>). Un GPX dice dónde estuvo una persona. Los `.gpx` están ignorados por Git en todo el repositorio, menos dentro de `datos/`.

## Prohibido

Copiar paradas, recorridos u horarios de Google Maps: sus términos lo prohíben. Se puede usar para orientarse, pero los datos tienen que salir de lo que ustedes saben y vieron, o de OpenStreetMap.
