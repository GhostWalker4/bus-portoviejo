# Datos de las líneas

Aquí van los datos reales que se levantan en la **fase 1** del roadmap.

```
datos/
  recorridos/   archivos .gpx grabados con GPSLogger, YA RECORTADOS
  paradas/      la lista de paradas de cada línea (nombre, lado de la calle, foto)
  gtfs/         el resultado final en formato GTFS
```

## Cómo grabar una línea

1. Instala **GPSLogger** en tu Android (es gratis y de código abierto). Configúralo para guardar en GPX cada 5 segundos.
2. Súbete al bus en el inicio de la línea y empieza a grabar. Haz ida y vuelta.
3. En cada parada, anota en el celular la hora, el nombre de la parada y el lado de la calle, y toma una foto.
4. Repite en otro horario (mañana, mediodía, hora pico).

## Antes de subir un recorrido

- **Recorta los tramos cercanos a casas**: el principio y el final, si empezaste o terminaste cerca de donde vives. Puedes hacerlo en <https://gpx.studio>.
- Nómbralo así: `linea-<número>_<ida|vuelta>_<AAAA-MM-DD>_<HHMM>.gpx`.
- Los `.gpx` están ignorados por Git en todo el repositorio, menos dentro de `datos/`. Ese es el único lugar donde se suben.

## Prohibido

Copiar paradas, recorridos u horarios de Google Maps. Sus términos lo prohíben. Puedes mirarlo para orientarte, pero los datos tienen que salir de la grabación o de la libreta.
