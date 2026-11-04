# Harvest portal-galivelop — 2026-11-04

De `5248b0a7` a `dd327106` (`scripts/harvest.py`). El proyecto pasó de la 0.4.3 a la 0.5.0 con `/gw-update`; lo nuevo
está en `docs/records/retro-2026-11-04-gw-portal-0-5-0.md`, sección «For Galivelop-workflow». Lo demás de «Ideas» que
lista el informe ya se recogió en las recogidas anteriores.

## P1. `apply.py --update` lista los usos de nombres viejos en los archivos propios del proyecto

- **Source:** `docs/records/retro-2026-11-04-gw-portal-0-5-0.md` @ `38ed903` (retro, P3)
- **What changes:** tras migrar nombres (A8), `apply.py --update` (o `doctor.py`) hace `git grep` de los nombres viejos
  (`docs/traspaso.md`, `docs/difusion`, `"estado": "listo"`, `revisado`…) en los archivos que el flujo no copia y los
  lista con la ruta y la línea.
- **Why it is general:** cualquier proyecto con skills o scripts propios que citen rutas del flujo queda con rutas
  rotas tras la 0.5.0; en el portal fueron 3 de los 12 hallazgos de la revisión, y solo los vio la revisión.
- **Version bump:** patch
- **Status:** aprobada (2026-11-04) → D46

## P2. `apply.py --update` vuelve a quitar los pasos propios del CI del proyecto

- **Source:** `docs/records/retro-2026-11-04-gw-portal-0-5-0.md` @ `38ed903` (retro)
- **What changes:** comprobar por qué la protección de la 0.4 (un archivo del flujo que difiere de la versión de su
  cabecera se propone como `.gw-new`) no salvó el `check.yml` del portal en el paso a 0.5.0 (¿el renombrado
  `comprobar.yml` → `check.yml` se salta la comparación?), arreglarlo con su test y, si hace falta, un bloque marcado
  como propio del proyecto que la plantilla conserva (lo aplazado de la P2 de `2026-10-23-portal-galivelop.md`).
- **Why it is general:** es la tercera vez que una actualización le borra al portal Node 22, la caché de npm y su
  build; cualquier proyecto con pasos propios en el CI los pierde igual.
- **Version bump:** patch (el arreglo); minor (el bloque propio, si hace falta clave nueva)
- **Status:** aprobada (2026-11-04) → D45

## P3. La caché del check no ve los archivos ignorados que el check lee

- **Source:** `docs/records/retro-2026-11-04-gw-portal-0-5-0.md` @ `38ed903` (retro)
- **What changes:** la clave de `scripts/check-green.sh` sale del índice y del árbol de git; un archivo ignorado que el
  check lee (`.claude/gw.local.json`, que usa `private-check.py`) cambia sin invalidarla. Meter en la clave esos
  archivos (una lista fija del flujo más lo que declare el proyecto) o, como mínimo, decirlo en el mensaje del verde
  reutilizado.
- **Why it is general:** un verde viejo tras cambiar la configuración local deja subir algo que el check habría parado.
- **Version bump:** patch
- **Status:** aprobada (2026-11-04) → E23

## P4. El `pre-push` sugiere `git rebase -i` en un flujo que dice «merge, nunca rebase»

- **Source:** `docs/records/retro-2026-11-04-gw-portal-0-5-0.md` @ `38ed903` (retro); en el flujo,
  `templates/githooks/pre-push` línea 278 y `scripts/private-check.py` línea 262
- **What changes:** cuando el `pre-push` para datos privados, el mensaje dice que los commits aún no están subidos (y
  por eso reescribirlos no choca con la regla) y propone `git commit --amend` si es el último, o `git rebase -i` sobre
  la rama remota si son varios; nunca sobre commits ya subidos.
- **Why it is general:** el mensaje contradice `AGENTS.md` en apariencia y un agente puede negarse o dudar.
- **Version bump:** patch
- **Status:** aprobada (2026-11-04) → D47

## Stays in the project

- `gw-portal` (`.claude/skills/gw-portal/SKILL.md`, nacida en el proyecto): pone al día el portal con los repos de la
  cuenta; es del portal.
- Retro P1, P2 y P4 (clones de `gw-portal` en el scratchpad, `proyectos.md` por sección, mirar el diagrama tras el
  último cambio): ya aplicadas en el proyecto. P5 (abrir la sesión desde el repo): ya es regla del flujo.

## Already here

- Leer otros repos clonados en el scratchpad sin registrarlos: `skills/gw-harvest/SKILL.md` paso 1.
