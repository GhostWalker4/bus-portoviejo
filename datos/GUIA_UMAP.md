# Guía: marcar las paradas en uMap

Con esta guía, quien conoce las rutas marca las paradas en un mapa digital, y un script las convierte en **GTFS**, el formato estándar de transporte público que usa la app.

> **¿Por qué no en papel ni sobre Google Maps?** Una X en papel hay que pasarla después a coordenadas a ojo, lo que lleva mucho tiempo y da errores de varios metros. Además, sacar posiciones de un mapa de Google va contra sus términos de uso. En uMap cada marcador ya tiene su coordenada exacta, y el mapa de fondo es de OpenStreetMap, que se puede usar libremente.

**Tiempo estimado:** de 20 a 40 minutos por ruta, ida y vuelta.

---

## 1. Crear el mapa (lo hace una sola persona, una sola vez)

1. Entra a <https://umap.openstreetmap.fr/es/>.
2. Inicia sesión con una cuenta de **OpenStreetMap**. Es gratis: se crea en <https://www.openstreetmap.org/user/new>. Con cuenta, el mapa queda guardado a tu nombre y puedes elegir quién lo edita.
3. Crea un mapa nuevo y llámalo **Bus Portoviejo – paradas**. Centra la vista en Portoviejo y guarda.
4. Invita a los demás como **editores** desde los permisos del mapa. Ellos también necesitan cuenta de OpenStreetMap.

   Si alguien no quiere crear cuenta, también se puede crear el mapa sin iniciar sesión. En ese caso uMap da un **enlace secreto de edición**: guárdalo bien, porque sin él nadie puede volver a editar el mapa.

5. Pega el enlace del mapa en el Issue de la fase 1 para que todos lo encuentren.

> Los nombres de los botones de uMap pueden cambiar un poco entre versiones. Si no encuentras uno, busca el ícono del lápiz (editar), el de las capas o el de compartir.

## 2. Una capa por ruta y por sentido

Cada ruta lleva **dos capas**: una para la ida y otra para la vuelta. El nombre tiene que ser **exactamente** así, porque el script lo lee:

| Bien ✅ | Mal ❌ |
|---|---|
| `Ruta 2 - ida` | `Línea dos` |
| `Ruta 2 - vuelta` | `Ruta 2` (falta el sentido) |
| `Ruta 14 - ida` | `R2 ida` |

- La **ida** es el sentido en que la ruta empieza su recorrido (por ejemplo, de San Gregorio a la UTM). La **vuelta** es el camino de regreso.
- Dale el mismo color a las dos capas de una ruta, para distinguirla de las otras.
- Si una ruta es circular (sale y vuelve al mismo lugar sin regresar por el mismo camino), haz solo la capa de **ida**.

## 3. Un marcador por parada

1. Elige la capa de la ruta y el sentido que vas a marcar.
2. Con la herramienta de **marcador**, haz clic **en el lugar exacto donde el bus se detiene**, en el **lado de la calle** que corresponde a ese sentido. Acerca bastante el mapa para ubicarlo bien.
3. Ponle de nombre **el número de orden, un espacio y el nombre de la parada**:

   ```
   01 Terminal Terrestre
   02 Paseo Shopping
   03 Parque Central
   ```

   - Los números van en el orden en que pasa el bus, empezando en `01`.
   - Que no se repitan ni falten números. El script avisa si pasa.
   - El nombre es lo que verá la gente en la app: que sea reconocible ("UTM – puerta principal", "Frente al Hospital del IESS").

4. **Si dos rutas paran en el mismo lugar**, cada una marca su parada en **su propia capa**, aunque quede encima de la otra. El script se da cuenta de que es la misma parada (si están a menos de 15 m) y la cuenta una sola vez. Así sabemos qué rutas pasan por cada parada.

## 4. (Opcional) Dibujar el recorrido

No hace falta dibujar por dónde va el bus: el script lo calcula por las calles reales entre una parada y la siguiente.

Pero ese cálculo piensa como un auto, y a veces da una vuelta rara (por ejemplo, por una calle de un solo sentido que el bus no usa). Si en la vista previa (paso 7) ves un recorrido equivocado, **dibuja una línea** en esa capa siguiendo el camino real del bus, desde la primera parada hasta la última. Si la capa tiene una línea, el script usa esa en lugar de calcularla.

## 5. Frecuencia y horario

El mapa dice **dónde** para el bus. Para la app también hace falta saber **cuándo**. Completa una fila por ruta en [`rutas.csv`](rutas.csv) (se abre con Excel o Google Sheets):

| Columna | Qué poner | Ejemplo |
|---|---|---|
| `ruta` | el número, igual que en la capa | `2` |
| `nombre` | de dónde a dónde va | `San Gregorio – UTM` |
| `cooperativa` | la que opera la ruta | `Cooperativa Portoviejo` |
| `color` | color de la ruta en la app (hexadecimal) | `E4573D` |
| `frecuencia_min` | cada cuántos minutos pasa, aproximado | `12` |
| `desde` / `hasta` | primera y última salida | `05:30` / `20:00` |
| `dias` | `todos`, `lunes-viernes`, `lunes-sabado` o `fines-de-semana` | `todos` |
| `velocidad_kmh` | velocidad promedio del bus; si no sabes, deja `16` | `16` |

Si una ruta no está en `rutas.csv`, el script usa valores por defecto (cada 15 minutos, de 06:00 a 19:00) y lo avisa.

## 6. Exportar el mapa

1. Abre el panel de **compartir y descargar** del mapa.
2. Descarga la **copia de seguridad completa** (un archivo `.umap`). Es la única descarga que conserva los nombres de las capas; el GeoJSON común los pierde.
3. Guárdalo como `datos/mapas/bus-portoviejo.umap`, reemplazando el anterior.

## 7. Convertir a GTFS y revisar

Desde la raíz del repositorio:

```bash
python datos/convertir_a_gtfs.py
```

Necesita internet para calcular los recorridos por las calles. Sin internet, usa `--sin-osrm` y une las paradas con líneas rectas.

El script muestra:

- **✓** cuántas rutas y paradas encontró, y cuáles paradas comparten varias rutas.
- **Revisar:** avisos que hay que mirar, como nombres distintos para la misma parada, números que faltan o una ruta sin datos en `rutas.csv`.
- **✗** errores que impiden generar el GTFS, como una parada sin número. Corrígelos en uMap, exporta de nuevo y vuelve a correrlo.

Para **ver el resultado en un mapa**, abre <https://geojson.io> y arrastra el archivo `datos/vista_previa.geojson`. Revisa que cada recorrido vaya por donde realmente va el bus.

El resultado queda en `datos/gtfs/`. Para una validación completa, comprime los archivos `.txt` de esa carpeta en un `.zip` y súbelo al validador oficial: <https://gtfs-validator.mobilitydata.org/>.

## 8. Subirlo al repositorio

Sube en una rama y con pull request, como siempre (ver [`CONTRIBUTING.md`](../CONTRIBUTING.md)):

- `datos/mapas/bus-portoviejo.umap`
- `datos/rutas.csv`
- `datos/gtfs/`

---

## Importante

- **No copies nada de Google Maps.** Puedes usarlo para acordarte de por dónde pasa una ruta, pero los marcadores tienen que salir de lo que ustedes saben y vieron.
- **Los tiempos entre paradas son estimados** a partir de la distancia y de la velocidad promedio. Se van a corregir viajando una vez en cada ruta (Issue de calibración).
- **Si no estás seguro de una parada, márcala igual** y escribe `(dudosa)` en el nombre, por ejemplo `07 Mercado Central (dudosa)`. Se confirma después.
