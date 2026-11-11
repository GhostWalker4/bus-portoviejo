# Bus Portoviejo

App para Android que muestra **en tiempo real dónde vienen los buses urbanos de Portoviejo** (Manabí, Ecuador) y te dice si te da tiempo de llegar a la parada.

Primero se va a presentar a las autoridades como prototipo, con buses simulados sobre recorridos reales. Si el proyecto se financia, se instalan GPS físicos en los buses.

📍 **El plan completo está en [`ROADMAP.md`](ROADMAP.md)** y, en versión para compartir, en [`docs/Roadmap-Bus-Portoviejo.pdf`](docs/Roadmap-Bus-Portoviejo.pdf).
🤝 **Antes de tu primer cambio, lee [`CONTRIBUTING.md`](CONTRIBUTING.md).**

## Estructura

```
movil/       la app (React Native + Expo + TypeScript)
servidor/    el servidor (Django + Django REST Framework + Django Channels)
datos/       recorridos, paradas y GTFS de las líneas reales (fase 1)
docs/        el roadmap en PDF y su fuente
```

El prototipo web anterior (la demo con el mapa 3D y el servidor para Traccar) ya no está en `main`, pero se conserva en la etiqueta [`prototipo-web`](../../tree/prototipo-web). Para verlo: `git checkout prototipo-web`.

## Lo que necesitas instalar

| Programa | Versión | Para qué |
|---|---|---|
| [Git](https://git-scm.com/downloads) | cualquiera reciente | clonar y subir cambios |
| [Python](https://www.python.org/downloads/) | **3.12 o más nuevo** | el servidor (Django 6.1 no funciona con versiones anteriores) |
| [Node.js](https://nodejs.org/) | **LTS** (22 o más nuevo) | la app |
| **Expo Go** en tu Android | la de Play Store | ver la app en tu celular sin compilar nada |
| [Android Studio](https://developer.android.com/studio) + JDK 17 | — | recién en la **fase 4**, cuando entre el mapa |

## Clonar el repositorio

```bash
git clone https://github.com/GhostWalker4/bus-portoviejo.git
cd bus-portoviejo
```

## Correr el servidor

Desde la carpeta `servidor/`. En Windows:

```bash
cd servidor
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

En Mac o Linux, la tercera línea es `source .venv/bin/activate`.

Comprueba que funciona abriendo <http://localhost:8000/api/salud/>. Debe responder `"estado": "ok"`.

- Panel de administración: <http://localhost:8000/admin/>. Antes, crea tu usuario con `python manage.py createsuperuser`.
- Pruebas: `python manage.py test`.
- WebSocket de prueba: `ws://localhost:8000/ws/salud/`. Saluda al conectarse y devuelve cada mensaje que le mandas.

Se usa `0.0.0.0` para que el celular pueda entrar por la IP de tu computadora. Si Windows pregunta por el firewall, permite el acceso en **redes privadas**.

## Correr la app

En otra terminal, desde la carpeta `movil/`:

```bash
cd movil
npm install
npx expo start
```

Escanea el código QR con **Expo Go**. El celular y la computadora tienen que estar **en el mismo Wi-Fi**.

La app busca el servidor sola, en la misma IP de la computadora y el puerto 8000. Si dice "Conectado", la app y el servidor ya se hablan. Si necesitas apuntar a otro servidor, crea `movil/.env.local` con:

```
EXPO_PUBLIC_SERVIDOR_URL=http://192.168.1.50:8000
```

Antes de subir cambios: `npm run typecheck`.

## Estado

| Fase | Estado |
|---|---|
| 0 · Preparar el terreno | ✅ estructura, servidor y app base |
| 1 · Datos reales de 2 o 3 líneas | ⏳ siguiente |
| 2 a 9 | pendientes, ver [`ROADMAP.md`](ROADMAP.md) |

Las tareas están en [Issues](../../issues).

## Créditos

- Mapas: © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), licencia ODbL.
- Mapa interactivo: [MapLibre](https://maplibre.org/).
- Fuentes del roadmap: Bricolage Grotesque e Inter, licencia SIL Open Font License.

## Licencia

Por ahora **no tiene licencia**: el código es de sus autores y nadie más tiene permiso de reutilizarlo, aunque el repositorio sea público.
