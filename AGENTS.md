# Reglas del proyecto para agentes de IA

Este archivo lo leen Antigravity, Claude Code (a través de `CLAUDE.md`) y otras herramientas. Las reglas valen para todas.

## Idioma

- **Responde siempre en español**: explicaciones, resúmenes, preguntas, mensajes de commit y descripciones de pull request.
- El código (nombres de variables, funciones, modelos) va en español cuando describe el dominio (`Linea`, `Parada`, `urlServidor`). Las palabras técnicas estándar pueden quedar en inglés.

## Qué es el proyecto

App Android que muestra los buses urbanos de Portoviejo (Ecuador) en tiempo real. Por ahora los buses son **simulados** sobre recorridos reales, para presentarle el prototipo a las autoridades. El plan está en `ROADMAP.md`, dividido en fases del 0 al 9. **Trabaja solo en la fase y el Issue que te pidieron**; no adelantes fases.

- `movil/`: React Native + Expo + TypeScript. Lee también `movil/AGENTS.md`: Expo cambia mucho entre versiones y hay que consultar la documentación de la versión instalada.
- `servidor/`: Django 6.1 + Django REST Framework + Django Channels (WebSockets, con la capa en memoria; sin Redis hasta la fase 9). La app de Django del dominio es `transporte`.
- `datos/`: recorridos y GTFS de las líneas reales.

## Cómo trabajar

- Una tarea = un Issue = una rama. Nunca hagas commit ni push a `main`.
- Antes de crear una rama, `git pull` en `main`.
- No modifiques archivos ajenos a la tarea. Varias personas trabajan en paralelo con IAs distintas y los cambios de más causan conflictos.
- Al terminar, comprueba:
  - Servidor: `python manage.py test` desde `servidor/` (con el entorno `.venv` activado).
  - App: `npm run typecheck` desde `movil/`.
- Para agregar paquetes a la app usa `npx expo install <paquete>`, no `npm install <paquete>`.
- Para agregar paquetes al servidor, agrégalos también a `servidor/requirements.txt` con un rango de versión.
- El mensaje de posición de un bus tiene que tener siempre la forma que mandará el GPS real: `bus`, `lat`, `lon`, `velocidad`, `rumbo`, `hora`. Así, cuando haya GPS físicos, la app no se toca.

## Prohibido

- Copiar datos de Google Maps (paradas, recorridos, horarios). Sus términos lo prohíben. Los datos salen del trabajo de campo o de OpenStreetMap.
- Subir recorridos GPS sin recortar, claves, contraseñas o archivos `.env`.
- Crear o editar a mano `movil/android/` o `movil/ios/`: se generan solos.
