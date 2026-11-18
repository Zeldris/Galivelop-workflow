# El flujo desde opencode y Codex

[English](../en/other-agents.md)

El flujo está hecho para Claude Code, pero su parte escrita también sirve en otros agentes de código. Esta página dice
qué funciona fuera de Claude Code y qué no (B9, D7).

## Qué funciona

- **`AGENTS.md`:** opencode y Codex lo leen al empezar. El del flujo se entiende sin `@include` (solo `CLAUDE.md` hace
  `@AGENTS.md`), así que las reglas llegan enteras.
- **Skills:** `apply.py` copia las skills también en `.agents/skills` (clave `agentsSkillsDir`, [config](config.md)),
  donde las busca opencode. Codex usa su propia carpeta (`~/.codex/skills`, según el diseño D-7 de
  `docs/design/D-git.md`): si las quieres allí, cópialas a mano.
- **Ganchos de git** (`.githooks`): son de git, no de Claude Code, así que el `pre-commit`, el `commit-msg` y el
  `pre-push` comprueban igual cada commit y cada subida.
- **Scripts:** `handoff.py`, `recover.py`, `check.sh`, `task.py` y el resto se corren a mano o los corre el agente.

## Qué no funciona

- **Ganchos de Claude Code** (`.claude/settings.json`): el `SessionStart` que muestra la bitácora, el `Stop` que avisa
  de lo que queda sin subir y los guardas de permisos no corren. Al empezar, lee `docs/handoff.md` y corre
  `python3 .claude/gw/scripts/recover.py --state`; antes de parar, `git status` y sube.
- **Subagentes** con `model` y `effort` por encargo (`gw-orchestrate-dealer`): dependen de la herramienta Agent de
  Claude Code.
- **Libro de tokens:** `metrics.py record` lee los transcripts de Claude Code; el gasto de opencode y Codex no se
  apunta todavía (va a una `1.x`).

## Modelos de fuera de Anthropic

Claude Code solo lanza modelos de Claude. GPT, Gemini, DeepSeek y los demás se usan desde opencode u otra herramienta
que los admita, nunca como subagentes del flujo. `gw-selector` puede recomendarlos para una sesión en esa herramienta.
Sus precios pueden ir como dato en `metrics.prices` (una tabla con su `since` y su `source`), pero el libro no tendrá
filas suyas hasta que se lea el gasto de esas herramientas.
