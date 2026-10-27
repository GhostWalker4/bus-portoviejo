# Bus Portoviejo: prueba con GPS real

Con esto, un celular con **Traccar Client** hace de bus y su ubicación aparece en vivo en el mapa.

```
Celular con Traccar Client ──(Wi-Fi o datos, cada 5 s)──► servidor.py (tu computadora) ──► mapa en el navegador
                                                               │
                                                               └─► recorridos/AAAA-MM-DD.csv
```

| Archivo | Para qué sirve |
|---|---|
| `servidor.py` | Recibe las posiciones del celular, las guarda y las pasa al mapa. Solo necesita Python. |
| `web/index.html` | El mapa en modo en vivo (lo abre el servidor; no hace falta abrirlo a mano). |
| `simular_celular.py` | Hace de celular para probar sin salir de casa. |
| `recorridos/` | Se crea solo. Un archivo CSV por día con cada posición recibida. |

## Lo que necesitas

- **Python 3** en la computadora ([python.org](https://www.python.org/downloads/)). No hay que instalar nada más.
- **Traccar Client** en el celular. Es gratis, está en Play Store y en App Store y lo publica Traccar.
- Para la primera prueba, la computadora y el celular **conectados al mismo Wi-Fi**.

## Paso 1: encender el servidor

Abre una terminal en esta carpeta y ejecuta:

```bash
python servidor.py
```

Verás algo así:

```
Mapa en esta computadora:      http://localhost:5055
Mapa desde otro dispositivo:   http://192.168.100.10:5055
URL para Traccar Client:       http://192.168.100.10:5055
```

La IP (`192.168.100.10`) será la de tu computadora. Si Windows pregunta por el firewall, permite el acceso en **redes privadas**. Si no lo permites, el celular no podrá conectarse.

Abre `http://localhost:5055` en el navegador. Arriba aparecerá **En vivo · esperando celulares**.

## Paso 2: configurar Traccar Client en el celular

Los nombres pueden variar un poco según la versión de la app:

1. **Identificador del dispositivo**: un nombre corto, por ejemplo `14` o `jhon`. Es lo que aparecerá en el mapa.
2. **URL del servidor**: la que imprimió el servidor, por ejemplo `http://192.168.100.10:5055`.
3. **Precisión de ubicación**: alta.
4. **Frecuencia o intervalo**: 5 segundos. **Distancia**: 0.
5. Dale permiso de ubicación **"Permitir siempre"** y quítale la optimización de batería. Si no lo haces, Android corta el envío cuando apagas la pantalla.
6. Activa el servicio (el interruptor o el botón de inicio).

En la terminal del servidor empezarán a aparecer líneas como esta:

```
22:18:41          14  -1.057920, -80.450750  23 km/h
```

En el mapa aparecerá un marcador verde con el nombre del celular y la etiqueta **GPS REAL**.

## Qué vas a ver en el mapa

- **Si el celular está a menos de 80 m de la ruta de ejemplo**, la app lo trata como un bus de la línea: calcula cuándo llega a tu parada, te dice si te da tiempo y a qué hora llegas a tu destino.
- **Si está más lejos** (por ejemplo, en tu casa), aparece en el mapa como **Fuera de la ruta · a X km**, pero sin tiempo de llegada.
- **Si deja de enviar más de 2 minutos**, aparece en gris como **Sin señal**.
- La casilla **Mostrar también los 3 buses simulados** sirve para comparar tu celular con los buses inventados. Quítala para ver solo lo real.

## Probar sin salir de casa

Con el servidor encendido, abre otra terminal y ejecuta:

```bash
python simular_celular.py
```

Hace de celular y recorre la ruta a 25 km/h enviando su posición cada 3 segundos. Algunas variantes:

```bash
python simular_celular.py --id 77 --desde UTM --velocidad 30
```

```bash
python simular_celular.py --formato json
```

`--formato json` imita el formato de las versiones nuevas de Traccar Client. El servidor acepta los dos formatos.

## Probar en la calle, con datos móviles

Cuando el celular sale de tu Wi-Fi ya no ve tu computadora. Hace falta una dirección pública. La forma más fácil y gratis es **Cloudflare Tunnel**:

1. Instala `cloudflared` (en Windows):

   ```bash
   winget install --id Cloudflare.cloudflared
   ```

2. Con el servidor encendido, en otra terminal:

   ```bash
   cloudflared tunnel --url http://localhost:5055
   ```

3. Te dará una dirección como `https://algo-al-azar.trycloudflare.com`. Ponla como **URL del servidor** en Traccar Client.
4. Esa misma dirección sirve para abrir el mapa desde cualquier celular, por ejemplo el de tu amigo en la parada.

La computadora tiene que quedarse encendida y conectada mientras dure la prueba. La dirección cambia cada vez que abres el túnel.

## Un plan de prueba en la calle

1. **Tu amigo se sube al bus** con Traccar Client encendido.
2. **Tú esperas en una parada** con el mapa abierto y anotas a qué hora dijo la app que llegaría y a qué hora llegó de verdad.
3. **Repítanlo varios días y a distintas horas.** La diferencia entre lo estimado y lo real es el dato más valioso para presentar el proyecto.

Como la ruta del mapa todavía es de ejemplo, para que haya tiempos de llegada la prueba tiene que hacerse sobre esas calles. Si no, el celular saldrá "fuera de la ruta". El siguiente paso natural es **cambiar la ruta de ejemplo por la de una línea real**. Para eso sirven los recorridos guardados.

## Los recorridos guardados

Cada posición queda en `recorridos/AAAA-MM-DD.csv`:

```
hora,celular,lat,lon,velocidad_kmh,rumbo,precision_m,bateria
2026-10-27 07:02:15,14,-1.057920,-80.450750,23.0,85,6,81
```

Ábrelo en Excel o Google Sheets. Con un recorrido completo de una línea real ya tienen el trazado exacto, dónde se detiene el bus y cuánto tarda cada tramo. Esos datos reemplazan las velocidades inventadas de la demo.

## Limitaciones de este prototipo

- **La ruta y las paradas son de ejemplo.** Las calles son reales (OpenStreetMap), pero la línea no existe.
- **El mapa base solo dibuja calles alrededor del centro.** Más lejos verás tu marcador, pero sobre fondo vacío.
- **No hay contraseña.** Cualquiera en tu red, o con la dirección del túnel, puede enviar posiciones o ver el mapa. Está bien para pruebas, pero no para algo público.
- **Los tiempos de llegada usan velocidades promedio inventadas.** Mejorarán cuando usen las de recorridos reales.

## Si algo no funciona

| Qué pasa | Qué revisar |
|---|---|
| El celular no aparece y la terminal no muestra nada | ¿Mismo Wi-Fi? ¿La URL tiene `http://`, la IP correcta y `:5055`? ¿Permitiste Python en el firewall (redes privadas)? |
| Aparece y luego se queda en "Sin señal" | Quita la optimización de batería a Traccar Client y dale ubicación "Permitir siempre". |
| El mapa dice "Sin conexión con el servidor" | El servidor se cerró. Vuelve a ejecutar `python servidor.py` y recarga la página. |
| `Address already in use` al iniciar | Ya hay algo usando el puerto 5055. Usa otro, por ejemplo `python servidor.py 5056`, y cámbialo también en Traccar Client. |
| La posición salta mucho | Es la precisión del GPS dentro de casa. Afuera mejora mucho. |
