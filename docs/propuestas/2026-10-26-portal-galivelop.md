# Harvest portal-galivelop — 2026-10-26 (ventana de la 0.4.1)

De `db3f722b` a `b8470762` (`scripts/recoger.py`, 29 commits; `main` del proyecto). Las ideas salen de su
`docs/traspaso.md` y de las revisiones de los repos. Según el plan §7, la `0.4` solo recibe correcciones.

## P1. Sin aviso falso de «sesión abierta fuera del repo» en la nube

- **Source:** `docs/traspaso.md` del proyecto @ `b8470762` (script)
- **What changes:** `skills/opt-tokens/scripts/medir.py:88-91` avisa aunque `CLAUDE_CODE_REMOTE=true` y la variable de
  compactación estén puestas, y `doctor.py:476` (`check_session`, con `registro_sesion.py:63-74`) da WARN por lo mismo.
  En la nube, con la compactación en el entorno, no es un fallo (`AGENTS.md` ya lo dice). Unas 5-10 líneas y un test.
- **Why it is general:** reproducido: toda sesión en la nube lo ve, y un aviso que siempre sale enseña a no leerlos.
- **Version bump:** patch (corrección)
- **Status:** propuesta

## P2. Avisos y reglas nuevas — para la 1.0.0

- **Source:** `docs/traspaso.md` del proyecto (skill y guía)
- **What changes:**
  - aviso de que `pkill -f <patrón>` mata a la propia orden que lo lanza (1-3 líneas);
  - los runbooks de tareas programadas se revisan como código;
  - en `REVIEW.md` y en el encargo de revisión, marcar los datos que caducan (versiones, precios, cuotas).
- **Version bump:** patch cada una, pero son novedades → **para la 1.0.0**
- **Status:** propuesta

## P3. `gw-media-content` deja un `web.md` con el bloque del muro — para la 1.0.0

- **Source:** `docs/desarrollo.md:95-140` del proyecto (skill)
- **What changes:** un `web.md` opcional por pieza, con `estado` (`"listo"`), `fecha`, `texto` por idioma y `muro`
  {`titulo`, `cuerpo[]`, `imagenes[]`}, si el proyecto declara un canal web; unas 30-60 líneas. El contrato es del
  portal y usa `gl`, que no está en los idiomas habituales del flujo: hay que hacerlo genérico.
- **Version bump:** minor → **para la 1.0.0** (evolutivo)
- **Status:** propuesta

## Ya está aquí

- Carpeta `AAAA-MM-DD/NN-<tema>/` de las piezas: P1 de `2026-10-25-world-maker-fantasy-2.md`.

## Se queda en el proyecto

- Fichas y perfiles del Portal, y su revisión especial de los repos.
