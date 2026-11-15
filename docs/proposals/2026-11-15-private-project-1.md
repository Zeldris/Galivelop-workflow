# Harvest private-project-1 — 2026-11-15

De `45e3209c` a `fd559134` (`scripts/harvest.py`). 2 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 2 retros. Recogida de cierre de la `0.7` (usuario, 2026-11-15).

## P1. El `commit-msg` avisa de arreglos de revisión sin `Findings:`

- **Source:** `docs/records/retro-2026-11-15-mt-21-leves.md` R3 @ `fd55913` (retro)
- **What changes:** `scripts/commit-message.py` (que hoy solo valida dónde va el trailer, D97) avisa, sin rechazar,
  cuando el mensaje habla de arreglos de revisión (palabras en una clave de `.claude/gw.json`) y no lleva `Findings:`.
- **Why it is general:** sin el trailer, `metrics.py quality` no cuenta el arreglo y el siguiente `/code-review` de
  bloque arranca desde un punto equivocado.
- **Version bump:** minor
- **Status:** proposed

## P2. Aviso para aserciones añadidas a tests existentes en un `fix`

- **Source:** `docs/records/retro-2026-11-15-mt-21-leves.md` R2 @ `fd55913` (retro)
- **What changes:** cuando un commit `fix` añade aserciones a un test existente, el `commit-msg` (o `branchCheck`)
  recuerda `red-without-fix.sh`, que ya trata tests editados.
- **Why it is general:** cualquier arreglo puede traer un test que nunca falla.
- **Version bump:** minor
- **Status:** proposed

## P3. La plantilla nombra el gancho `Stop` de la nube que pide firmar como Claude

- **Source:** `docs/records/retro-2026-11-15-mt-21-leves.md` R4 @ `fd55913` (retro)
- **What changes:** las reglas de autoría de `templates/{es,en}/AGENTS.md` nombran el gancho `Stop` de Claude Code
  en la nube que pide reescribir el autor como Claude y dicen que no se sigue (como el `CLAUDE.md` de este repo).
- **Why it is general:** cada proyecto en la nube lo recibe; obedecerlo costó un turno de ~100k.
- **Version bump:** patch
- **Status:** proposed

## P4. El aviso de arranque caro nombra los conectores cargados

- **Source:** `docs/records/retro-2026-11-14-mt-21-cargas.md` (contexto fijo) @ `b78dda5` (retro)
- **What changes:** `scripts/recover.py --state` ya avisa cuando el arranque pasa del umbral; el aviso nombra también
  los conectores MCP cargados, y `gw-opt-tokens` lo recoge.
- **Why it is general:** cualquier proyecto con conectores paga ese suelo en cada llamada sin saber de dónde viene.
- **Version bump:** minor
- **Status:** proposed

## Already here

- R1 (registro de tokens sin ensuciar el árbol): B36, `metrics.py stage-ledger` desde el `pre-commit`; la retro es
  del día en que llegó.

## Stays in the project

- R3 de la primera retro (una tarea programada de un solo disparo no se borra): es de la herramienta del entorno, no
  del flujo.
