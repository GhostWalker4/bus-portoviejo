# Roadmap: Bus Portoviejo

**Objetivo:** una app nativa para Android que muestre los buses urbanos de Portoviejo en tiempo real, diga cuánto falta para que llegue el bus, ayude a planificar viajes y avise cuando el bus está cerca. Primero, como **prototipo para presentárselo a las autoridades**, con buses simulados sobre recorridos reales. Después, si hay financiamiento, con GPS físicos instalados en los buses.

**Tecnología:** React Native con Expo para la app, Django + Django Channels (WebSockets) para el servidor y MapLibre para el mapa. Solo Android al principio y solo servicios gratuitos durante la demo.

---

## Cómo se ve el final del camino

```
FASE 0      FASE 1         FASE 2       FASE 3          FASE 4       FASE 5-7               FASE 8          FASE 9
Preparar ─► Datos reales ─► Servidor ─► Simulación  ─► App con   ─► Llegada, viaje A→B ─► Presentar ─► GPS reales
            (en la calle)  Django      en tiempo real  el mapa      y avisos              a las          (si financian)
                                                                                          autoridades
            ◄──── la fase 1 avanza en paralelo con las fases 2 a 4 ────►
```

**Meta de la demo (fin de la fase 8):** un APK instalable con 2 o 3 líneas reales de Portoviejo, buses simulados moviéndose en vivo, tiempo de llegada a cada parada, planificador A→B con transbordo y avisos. Además, un panel web donde se administran líneas y paradas, y una presentación con un plan piloto y costos.

---

## Fase 0: Preparar el terreno

- [x] Antes de borrar el prototipo web, marcarlo con una etiqueta (`git tag prototipo-web`) para poder volver a él cuando haga falta. Su lógica de tiempos de llegada y sus scripts de OpenStreetMap sirven como referencia.
- [x] Reorganizar el repositorio en dos carpetas: `movil/` (Expo) y `servidor/` (Django).
- [ ] Instalar Node.js LTS, Python 3, Git y Android Studio (para el emulador y para compilar).
- [ ] Elegir una licencia, por ejemplo MIT, o dejarlo privado si se piensa vender o licenciar al municipio.
- [ ] En GitHub, crear un tablero (*Projects*) y pasar cada tarea de este roadmap a un *Issue*. Así un colega que vuelva puede tomar una tarea sin preguntar por dónde empezar.

**Listo cuando:** `npx create-expo-app` y `django-admin startproject` corren en tu computadora y el repositorio tiene la nueva estructura.

## Fase 1: Datos reales de 2 o 3 líneas (trabajo de campo)

Es la base de todo: sin recorridos reales, la demo no convence. Se hace **en paralelo** con las fases 2 a 4 y es la tarea ideal para los colegas.

- [ ] Elegir 2 o 3 líneas que **se crucen** entre sí (para que el planificador A→B tenga transbordos) y que una de ellas pase por la UTM.
- [ ] Viajar en cada línea, ida y vuelta, con el celular grabando el recorrido. Como el servidor del prototipo se va a borrar, conviene usar **GPSLogger** (Android, gratis y de código abierto), que guarda el recorrido en el celular como archivo GPX sin necesitar servidor.
- [ ] Anotar cada parada: nombre, lado de la calle y una foto. Google Maps sirve para orientarse, pero **sus datos no se pueden copiar** porque sus términos lo prohíben. Los puntos tienen que salir de la grabación o de la libreta.
- [ ] Repetir cada línea en 2 o 3 horarios (mañana, mediodía, hora pico) para tener tiempos reales por tramo.
- [ ] Anotar la frecuencia aproximada (cada cuántos minutos pasa un bus) y el horario de servicio.
- [ ] Pasar todo a formato **GTFS**, el estándar mundial de transporte público. A las autoridades les da una buena impresión y, más adelante, permite que la ciudad aparezca en Google Maps o en Moovit por las vías oficiales.

**Privacidad:** los archivos GPX dicen dónde estuvo una persona. Antes de subirlos, recorta los tramos cercanos a casas.

**Listo cuando:** existen el trazado, las paradas y los tiempos por tramo de 2 o 3 líneas, en GTFS dentro de `datos/`.

## Fase 2: Servidor Django (la base)

- [ ] Modelos: `Linea`, `Parada`, `Trazado` (la forma del recorrido), `ParadaEnLinea` (orden y tiempo por tramo) y `Bus`.
- [ ] Activar el **panel de administración de Django**: desde ahí se crean y editan líneas y paradas sin programar. Conviene mostrárselo a las autoridades.
- [ ] Un comando `python manage.py importar_gtfs` que cargue los datos de la fase 1.
- [ ] Una API con Django REST Framework: `/api/lineas`, `/api/lineas/<id>/paradas` y `/api/lineas/<id>/trazado`.
- [ ] Publicarlo en un servicio gratuito, como Render, Koyeb o PythonAnywhere. Revisa sus condiciones en ese momento, porque los planes gratuitos cambian seguido. En la mayoría el servidor "se duerme" cuando nadie lo usa: hay que despertarlo unos minutos antes de cada presentación.

**Listo cuando:** abres la API desde el celular y devuelve las líneas reales.

## Fase 3: Simulación en tiempo real (Django Channels)

- [ ] Un simulador dentro de Django que haga salir buses según la frecuencia de cada línea y los mueva por el trazado real, con las velocidades por tramo de la fase 1.
- [ ] Variaciones realistas: cada bus algo más rápido o más lento, esperas distintas en cada parada y algo de "tráfico" en hora pico.
- [ ] Un canal WebSocket por línea (`/ws/lineas/<id>/`) que envíe la posición de cada bus cada 2 a 5 segundos.
- [ ] Para la demo basta la capa en memoria de Channels (`InMemoryChannelLayer`), que funciona con un solo proceso y no necesita Redis. Redis llega en la fase 9, cuando haya muchos usuarios y buses reales.
- [ ] Diseñar el mensaje de posición igual a como llegará del GPS real (`bus`, `lat`, `lon`, `velocidad`, `rumbo`, `hora`). Así, el día que haya GPS físicos, solo cambia de dónde vienen los datos y la app no se toca.

**Listo cuando:** un cliente WebSocket de prueba recibe los buses simulados moviéndose.

## Fase 4: La app con el mapa (Expo)

- [ ] Crear la app con Expo y TypeScript.
- [ ] Agregar `@maplibre/maplibre-react-native`. Este paquete **no corre en Expo Go**: hay que hacer un *development build* (`npx expo run:android`). Es la primera traba que vas a encontrar; no es un error tuyo.
- [ ] Mapa base: usar teselas vectoriales gratuitas, por ejemplo OpenFreeMap, que no pide clave y trae edificios. Así no hay que generar el mapa a mano como en el prototipo. La vista isométrica 3D se puede recuperar con `fill-extrusion`.
- [ ] Pantallas: lista de líneas → mapa de la línea con su trazado y paradas → buses moviéndose en vivo por WebSocket.
- [ ] Mostrar "Sin conexión" cuando se cae el WebSocket y reconectar solo.

**Listo cuando:** en un Android real ves los buses simulados moverse sobre las líneas reales.

## Fase 5: Tiempo de llegada

- [ ] El servidor calcula, para cada bus, cuánto le falta para llegar a cada parada siguiente: distancia sobre el trazado ÷ velocidad por tramo, más las esperas en las paradas.
- [ ] En la app: tocas una parada y ves "llega en X min", además del aviso **Tranquilo / Sal ya / No llegas** según lo que tardas caminando (la ubicación del usuario sale de `expo-location`).
- [ ] Guardar paradas favoritas en el celular.

## Fase 6: Planificar viaje A → B

- [ ] El usuario elige origen y destino, tocando el mapa o con su ubicación actual.
- [ ] Con 2 o 3 líneas basta un método simple: buscar paradas a menos de unos 500 m caminando del origen y del destino, y probar primero las líneas directas y después las combinaciones con **un transbordo**.
- [ ] Ordenar las opciones por hora de llegada usando los tiempos de llegada en vivo.
- [ ] Más adelante, con muchas líneas, se puede pasar a OpenTripPlanner, que lee GTFS directamente.

## Fase 7: Avisos

- [ ] Primero avisos **locales** con la app abierta o en segundo plano reciente (`expo-notifications`): "Tu bus está a 3 minutos de la parada".
- [ ] Después, avisos **push** enviados por el servidor aunque la app esté cerrada. Es lo más difícil: requiere Firebase Cloud Messaging y que el servidor esté siempre despierto, algo que los planes gratuitos no garantizan. Para la demo alcanza con los locales.

## Fase 8: Presentación a las autoridades

Ideal para los colegas que prefieren la parte no técnica.

- [ ] Generar el APK con EAS Build (tiene un plan gratuito) e instalarlo en 2 o 3 celulares para la reunión.
- [ ] Grabar un video corto de la app funcionando, por si falla el internet en la sala.
- [ ] Documento y diapositivas con el problema (cuánto espera hoy un pasajero), la solución, la demo y un **plan piloto**: una línea, cuántos buses, el costo de cada GPS con su chip de datos y el costo mensual del servidor.
- [ ] Llevar algo que solo ustedes tienen: los datos GTFS de las líneas levantadas. Es un valor real para el municipio aunque no compren la app.
- [ ] Usar el contacto informal para conseguir la reunión con la dirección de movilidad o la ATM, y averiguar antes si las cooperativas ya tienen rastreadores.

**Listo cuando:** se hizo la presentación y hay una respuesta (sí, no o "vuelvan con X").

## Fase 9: Después de la presentación (GPS reales)

Solo si hay financiamiento o un piloto aprobado.

- [ ] Poner **Traccar Server** como puerta de entrada de los GPS físicos. Los rastreadores comerciales (Teltonika, Concox, etc.) hablan protocolos distintos y Traccar entiende más de 200. Django lee de Traccar y reemplaza al simulador sin cambiar la app.
- [ ] Seguridad: autenticación de los dispositivos, HTTPS y límites de uso.
- [ ] Redis como capa de Channels y un servidor que no se duerma (en este punto ya habría presupuesto).
- [ ] Medir en la calle la diferencia entre la llegada estimada y la real, y ajustar.
- [ ] Publicar en Play Store (pago único de 25 USD) y después en iPhone (Apple Developer, 99 USD al año).
- [ ] Ampliar a todas las líneas de la ciudad.

---

## Para sumarse al proyecto

| Si te interesa… | Empieza por |
|---|---|
| **Trabajo de campo** | Fase 1: elige una línea, viaja con GPSLogger y anota las paradas. No hace falta programar. |
| **Presentación y contactos** | Fase 8: arma el documento del problema y del plan piloto, e investiga quién decide en movilidad. |
| **Programar** | Toma un *Issue* del tablero de GitHub con la etiqueta de su fase. |

Reglas de trabajo: cada tarea en su propia rama y un *pull request* a `main`. No se suben recorridos GPS sin recortar.

## Riesgos que conviene tener presentes

- **Alcance:** cuatro funciones para la primera versión es bastante para una persona. Si se alarga, el orden de prioridad es buses en vivo → tiempo de llegada → A→B → avisos. Una demo con las dos primeras ya se puede presentar.
- **Curva de aprendizaje:** Expo, Django y Channels son tres cosas nuevas a la vez. Conviene ir en el orden del roadmap y no empezar una fase sin terminar la anterior.
- **Dependencia de las autoridades:** si dicen que no, los datos GTFS y la app siguen sirviendo. Se pueden ofrecer a una cooperativa directamente o volver a la idea de que los pasajeros compartan su ubicación.
- **Servicios gratuitos:** se duermen, cambian sus condiciones o cierran. Hay que tener el video de respaldo y saber volver a desplegar.
