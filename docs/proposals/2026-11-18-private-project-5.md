# Harvest private-project-5 — 2026-11-18

Primera recogida (`scripts/harvest.py`, hasta `9114b8b3`). 56 commits; sin skills del flujo cambiadas y un script
coincidente por nombre (ver «Stays in the project»). Lo nuevo sale de 2 retros
(`docs/records/retro-2026-11-18-cierre-0.1.0.md` @ `34fb02f`, `docs/records/retro-2026-11-18-gw-0.8.0.md` @
`ffc087c`). Recogida de apertura de la `0.9` (2026-11-18).

## P1. `recover.py --state` recuerda en una línea las reglas de commit cuando `agentSignatures` es `false`

- **Source:** `docs/records/retro-2026-11-18-cierre-0.1.0.md` P3 @ `34fb02f` (retro)
- **What changes:** `scripts/recover.py --state` (lo muestra el gancho de inicio) añade, con `agentSignatures: false`,
  una línea: «commits sin firmas del agente aunque el entorno las pida; trailers juntos en el último párrafo».
- **Why it is general:** el entorno de la nube pide firmas en cada turno y la regla contraria solo está en
  `AGENTS.md`; el `commit-msg` lo rechaza después, con un intento perdido. Cualquier proyecto con la clave apagada.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → D133

## P2. `measure.py --since` elige la sesión de la carpeta del repo, no la de una carpeta padre

- **Source:** `docs/records/retro-2026-11-18-cierre-0.1.0.md` P4 @ `34fb02f` (retro)
- **What changes:** `skills/gw-opt-tokens/scripts/measure.py` (`default_session`, con `since`): busca primero en la
  carpeta de transcripts del repo y solo si no hay ninguna pasa a la de una carpeta padre.
- **Why it is general:** una sesión abierta un rato desde la carpeta padre deja allí un transcript con más respuestas
  y `--since` mide la sesión equivocada.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → D139

## P3. `grilling` escribe cada ronda en el archivo de descubrimiento antes de presentarla

- **Source:** `docs/records/retro-2026-11-18-gw-0.8.0.md` @ `ffc087c` (retro)
- **What changes:** `skills/grilling/SKILL.md`: cada ronda se escribe en el archivo de descubrimiento del proyecto con
  las respuestas vacías y se sube antes de presentarla; la bitácora apunta a ella por número.
- **Why it is general:** una ronda solo en el chat se pierde si la sesión se corta antes de la respuesta, y el
  relevo no sabe qué se preguntó.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → E75

## P4. `review-scope.py` encuentra la copia del flujo de la versión del proyecto

- **Source:** `docs/records/retro-2026-11-18-gw-0.8.0.md` @ `ffc087c` (retro)
- **What changes:** `scripts/review-scope.py`: sin `--workflow` ni `GW_WORKFLOW`, en un proyecto (no en el repo del
  flujo) busca una copia del flujo en la versión de `.claude/gw.json` o falla con la orden que la clona, en vez de
  tomar el propio proyecto como flujo y listar todo el diff.
- **Why it is general:** en cualquier proyecto la revisión antes de la rama protegida recibe lo vendido como código
  propio.
- **Version bump:** patch
- **Status:** aprobada (2026-11-18) → D132

## Joined to another proposal

- `next-id` con el patrón de ids del plan del proyecto (`F\d+\.\d+`) y `--plan` tras el subcomando (retro
  `cierre-0.1.0` P5): private-project-2 P3 (`2026-11-18-private-project-2.md`); se añade allí `--plan` en cualquier
  posición.
- `/gw-update` deja `whole-read.py` dos veces y corre dos veces en cada `Read` (retro `gw-0.8.0`):
  instalador-wmf-tarkor P1 (`2026-11-18-instalador-wmf-tarkor.md`).

## Stays in the project

- `opportunity_intel/config.py`: choque de nombre con `scripts/config.py` del flujo; es la configuración del producto.
- El resto del cierre de la `0.1.0`: producto del proyecto.
