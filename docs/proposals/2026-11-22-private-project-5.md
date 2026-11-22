# Harvest private-project-5 — 2026-11-22

De `9114b8b3` a `0edac88` (`scripts/harvest.py`). 93 commits; skills y scripts iguales a `da1a462` (`0.8.1`). Lo nuevo
sale de las retros de cierre de sus versiones `0.2.0` y `0.3.0`.

## P1. Aviso de filas abiertas de la versión antes de cerrarla

- **Source:** retro de cierre de su `0.2.0`, P1 @ `a390e8a`; se repite en la de `0.3.0` (retro)
- **What changes:** `recover.py --state` lista las filas no hechas de la versión de la tarea (`roadmapFiles`, la lógica
  de `roadmap.py list`), y `reviewed.sh` avisa, sin bloquear, si la versión que va a la protegida tiene filas abiertas.
- **Why it is general:** dos versiones seguidas casi se cerraron con una fila pendiente sin aviso.
- **Version bump:** minor (patch si solo la línea de `recover.py --state`)
- **Status:** aprobada (2026-11-22) → D166, E81

## P2. `gw-reviewer` sin subagentes anidados

- **Source:** retro de cierre de su `0.3.0` @ `a390e8a` (retro; pregunta aprobada en el proyecto)
- **What changes:** quitar `Agent` de `tools:` en `gw-reviewer.md` y decirle que haga los ángulos de `/code-review` en
  línea.
- **Why it is general:** el revisor lanzó un `general-purpose` en Opus que gastó 2,3M de los 2,6M de la revisión (26 %
  de la tarea).
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D146

## P3. El aviso de arranque no salta por lo que no se puede tocar

- **Source:** retro de cierre de su `0.3.0`, P4 @ `a390e8a` (retro)
- **What changes:** en `scripts/context_guard.py`, con `system_weighs_most`, el aviso y la alarma de arranque se miden
  sobre la parte controlable (instrucciones, skills, bitácora, conversación), o al menos dicen que no hay nada que hacer,
  como la alarma de bucle (D122).
- **Why it is general:** en la nube la alarma salta en cada arranque (87k de 160k, 91 % sistema y MCP) y se acaba
  ignorando.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D156

## P4. La guía de instalación recomienda una sesión por repo

- **Source:** retro de cierre de su `0.2.0` @ `a390e8a` (retro)
- **What changes:** `docs/es/apply.md` ↔ `docs/en/apply.md` dicen, en la instalación, abrir las sesiones de la nube con
  solo ese repo.
- **Why it is general:** con dos repos en la sesión el gancho de inicio no corre y nada avisa; hoy solo lo dice
  `troubleshooting.md`, cuando ya ha pasado.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D164

## Stays in the project

- Tests de fallo que no leen el motivo (`assertRaises` sin `as`): de Python y a prueba en el proyecto.
- Sus barridos y decisiones de dominio.

## Already here

- «`roadmap.py list` no corta en el siguiente `## `»: no se reproduce (corte por sección desde B33).
- Umbral del aviso de arranque configurable: `contextGuard.warn`/`alarm` (B21).
