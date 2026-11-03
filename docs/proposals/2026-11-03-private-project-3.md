# Harvest private-project-3 — 2026-11-03

De `never` a `195bb867` (`scripts/harvest.py`). Primera recogida; el proyecto usa la v0.3.0.

## P1. `selector`: el documento de entrada de un diseño se lee entero una vez

- **Source:** `docs/registros/retro-2026-10-25-diseno-voces.md` (R4) @ HEAD 195bb867 (retro)
- **What changes:** En `skills/gw-selector/SKILL.md`, fila «traer algo de otro repo», matizar «la sesión principal nunca lee los archivos enteros»: el documento único del que nace un diseño se lee entero una vez en la sesión principal; el resto, con `Explore`.
- **Why it is general:** la fila actual del flujo (línea 26) sigue con la regla absoluta y cualquier proyecto que parta de un único documento de diseño choca con ella.
- **Version bump:** patch
- **Status:** proposed

## P2. `doctor.py`: avisar de sesión dentro de un Flatpak

- **Source:** `docs/registros/retro-2026-10-25-diseno-voces.md` (R3) @ HEAD 195bb867 (retro)
- **What changes:** `doctor.py` detecta `/.flatpak-info` y avisa (WARN informativo) de que compilador y herramientas son del SDK y de que el anfitrión se alcanza con `flatpak-spawn --host`.
- **Why it is general:** cualquier proyecto abierto desde un IDE en Flatpak lo sufre; el flujo solo lo toca de pasada (`worktreeDir` en `docs/en/config.md`, sin detección en `scripts/doctor.py`).
- **Version bump:** minor
- **Status:** proposed

## Stays in the project
- Ninguna skill ni script propio relevante: las skills "nacidas" (`opt-ai`, `opt-tokens`, `orchestrate-dealer`, `scout-updates`, `selector`) son copias antiguas sin prefijo `gw-` de las del flujo (mismas descripciones), no propuestas.

## Already here
- `gw-init`, `writing-for-agents` (`.claude/skills/...`): el proyecto está en 0.3.0 y el flujo en 0.4.3; el diff son solo cambios más nuevos del flujo (`apply.py`, `.gw-new`, clonar por etiqueta, sección «Documents read every session»), nada propio del proyecto.
- `gw-doctor`, `gw-update`, `pr`, `retro` (`.claude/skills/...`): copias viejas del flujo, sin cambios locales.
- `.claude/gw/scripts/config.py`, `doctor.py`, `session-start.sh`: versiones 0.3.0 del flujo (el flujo ya tiene v0.4.3, p. ej. `toplevel()` con `unset GIT_DIR` y aviso de `agentSignatures`).
- Retro F0 R2 (`Siguiente:` en el bloque final de trailers): `commit-msg` con `commitNext` en `.claude/gw.json` / `scripts/commit-message.py`.
- Retro F0 R3 (`bash -n a b` solo comprueba `a`): `scripts/doctor.py` (`check syntax-only`), `skills/gw-doctor/SKILL.md`, `docs/es/apply.md`, `docs/es/troubleshooting.md`.
- Retro diseño-voces R2 / aplicar-flujo (CI agotado, `ci-local`): `scripts/ci-local.py --record` y `scripts/ci-status.py`.
