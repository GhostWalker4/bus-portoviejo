# Cómo trabajamos

Somos pocos y cada uno trabaja con una herramienta de IA distinta (Claude Code, Antigravity…). Estas reglas existen para que no nos pisemos.

## El ciclo de una tarea

1. **Elige un Issue** en [Issues](../../issues) y **asígnatelo** (o comenta "lo tomo"). Si no hay Issue para lo que quieres hacer, créalo primero.
   Una tarea = una persona. Si un Issue ya tiene dueño, no lo toques sin hablar con esa persona.
2. **Actualiza tu copia** antes de empezar:

   ```bash
   git checkout main
   git pull
   ```

3. **Crea una rama** con un nombre que diga qué haces:

   ```bash
   git checkout -b fase2-modelos-linea
   ```

4. Trabaja y haz commits pequeños con mensajes **en español** que digan qué cambia y por qué.
5. **Comprueba que nada se rompió:**
   - Servidor: `python manage.py test` (desde `servidor/`)
   - App: `npm run typecheck` (desde `movil/`)
6. **Sube tu rama y abre un pull request** a `main`:

   ```bash
   git push -u origin fase2-modelos-linea
   ```

   En el pull request escribe `Cierra #12` (con el número del Issue), para que se cierre solo al fusionarlo.
7. **Otra persona lo revisa** antes de fusionarlo. Nadie sube directo a `main`.

## Si trabajas con una IA

- La IA lee [`AGENTS.md`](AGENTS.md) (Antigravity y otros) o [`CLAUDE.md`](CLAUDE.md) (Claude Code). Ahí están las reglas del proyecto. Si algo cambia, se cambia en `AGENTS.md` y vale para todas.
- **Revisa lo que hizo antes de hacer commit.** Tú respondes por el código que subes, no la IA.
- Pídele que trabaje solo en lo del Issue. Si toca archivos que no tienen que ver con la tarea, es más probable que choque con el trabajo de otro.
- No pegues contraseñas, claves ni tokens en el chat de la IA, ni los subas al repositorio.

## Qué nunca se sube

- **Recorridos GPS sin recortar** (`.gpx`, `.csv` de posiciones). Dicen dónde estuvo una persona. Antes de subir uno a `datos/`, quita los tramos cercanos a casas.
- Claves, contraseñas, archivos `.env` o `.env.local`.
- `node_modules/`, `.venv/` y `db.sqlite3`: cada uno los genera en su computadora.

## Si hay un conflicto

Si `git pull` o el pull request dicen que hay **conflictos**, no borres el trabajo del otro para que "pase". Avisa en el grupo y resuélvanlo juntos. Si es tu primera vez, pídele a tu IA que te explique el conflicto antes de tocar nada.
