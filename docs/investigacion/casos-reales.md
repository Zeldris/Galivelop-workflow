# Fase 0 — Dos casos reales del flujo

> Inventario del 2026-10-21 de **World-Maker-Fantasy (Tarkor)** y **Instalador-WMF-Tarkor**, leídos en solo lectura
> con un subagente. Sirve para contrastar el plan con lo que de verdad se usa. Rutas relativas a la raíz de cada
> repo. Antes de la Fase 8 (público) este archivo se resume o se quita (§10: nada privado).

## Resumen

| Pieza | Tarkor | Instalador | Más reciente |
|---|---|---|---|
| `CLAUDE.md` | 122 líneas; relevos entre dos cuentas, 3 fases antes del PR (`QA-183`), PR de la sesión local lo crea la nube (`QA-184`) | 99 líneas, misma estructura; añade «si la usuaria dice que se para, se para» y `## Pruebas` | Tarkor (reglas) |
| Bitácora | `docs/registros/traspaso.md`, una fila «Tarea en curso · `<rama>`» por rama, ≤600 caracteres | Igual | — |
| Skills | 18 en `.claude/skills/` + `README.md` de origen + `LICENSE-mattpocock-skills` | Las mismas 18, 15 con notas adaptadas | Divergen |
| Ganchos Claude | `SessionStart` (`startup\|resume\|clear`, `clear`, `compact`) y `PreToolUse` create/merge PR | Igual; matcher ampliado a `enable_pr_auto_merge` y `update_pull_request` | Instalador |
| `revision-antes-de-main.sh` | Marca == HEAD local; CI verde al fusionar | Cabeza del PR leída de `git ls-remote` (la rama en GitHub), auto-merge cuenta como fusión | Instalador |
| `pre-push` | Muchos checks propios + `prepush-ramas.sh` + `tests-relacionados.sh` | Guarda stdin antes de reenviarlo; añade `enlaces-md.py` | Instalador |
| `session-start.sh` | Solo nube; `set -e`; Postgres, Prisma, Ollama… | Solo nube; falla abierto (`AVISO`); Tauri, cargo… | Casi todo es propio |
| Marca de revisado | `.claude/revision-main.sha`, **ignorada por git** | Igual | — |
| Subida a `main` | Siempre por PR, CI verde, confirmación | Igual | — |
| Roadmap | `docs/producto/21-roadmap.md`, `tools/roadmap/cobertura.py`, `tools/roadmap/cerrar.py` | No: plan con casillas `INS-n` en `docs/05-plan-de-trabajo.md` | — |
| CI | `ci.yml`: jobs `roadmap`, `backend`, `frontend` | `comprobar.yml`: `linux`, `windows`, `qa` | — |
| Stack | Node/TS + Postgres + React; utilidades en Python | Tauri v2 (Rust) + React/TS | — |

## Lo que el plan no recoge (propuesto para el inventario, §3)

Piezas genéricas que existen en los dos repos y el plan no menciona:

- `tools/qa/bitacora.py`: una fila por rama, ≤600 caracteres, tareas cerradas en «Hecho». Con `ROADMAPS`
  configurable y `[x]` como cerrada en el instalador.
- `tools/qa/prepush-ramas.sh`: qué commits se suben y que solo tocan su fila de la bitácora
  (`BITACORA_COMPARTIDA=1` para una fila compartida).
- `tools/qa/fusionar.sh` (fusionar la rama de un subagente), `rojo-sin-arreglo.sh` (el test nuevo falla sin el
  arreglo), `tests-relacionados.sh` (tests de lo que cambia), `enlaces-md.py` (enlaces rotos en `.md`).
- `tools/roadmap/cerrar.py` (cierra una tarea en roadmap, mapa y bitácora), además de `cobertura.py`.
- `revisado.sh` exige una retro (`docs/registros/retro-*.md` con `**Estado` distinto de «pendiente») añadida en la
  rama antes de escribir la marca.
- Skills `scout-updates` (actualizaciones de dependencias y modelos) y `to-questionnaire` (mattpocock).
- Reglas de `CLAUDE.md`: una rama por sesión (`claude/<tema>`), traer `main` por merge al empezar cada tarea,
  `git status`/`git diff` tras una llamada interrumpida, las tres fases antes del PR, y el reparto «la sesión
  local prepara el PR, la nube lo crea» cuando la local no tiene GitHub.

## Lo que choca con el plan

1. **Marca de revisado.** El plan (§5.3) la quiere versionada en `docs/registros/revisado.txt` para que la vean
   otras cuentas y tareas programadas; los dos repos la tienen en `.claude/revision-main.sha` ignorada por git. Me
   quedo con la del plan (la usa el portal, según el plan) — conviene confirmarlo al leer el portal.
2. **Un solo `check`.** Ninguno de los dos tiene una orden única: el check real es el `pre-push` + la CI. Propuesta:
   `check` admite una lista de órdenes, y `/gw-init` propone crear un `tools/check.sh` si no hay ninguna.
3. **Raíz del repo.** Los ganchos de Tarkor usan `$CLAUDE_PROJECT_DIR` o `pwd`, justo lo que la §12 prohíbe. El
   portal ya lo arregló (según el plan); confirma que la fuente buena es la del portal.
4. **`session-start.sh` falla cerrado en Tarkor y abierto en el instalador.** Para el plugin: la parte genérica
   (`core.hooksPath`, avisos) falla abierta con aviso; lo que bloquee de verdad está en `pre-push` y `PreToolUse`.
5. **Fuente principal.** El plan toma el portal como fuente, pero esta sesión no lo tiene. El instalador trae
   versiones más nuevas de varias piezas (lista arriba). Hay que comparar las tres antes de portar (Fase 2–3).

## Lo que no va al plugin

Instalación de Postgres/Prisma/Ollama/Tauri, la lista concreta de checks, el pre-commit de `borradores-opencode`,
`AGENTS.md` y lore, `escenario.sh`/`sql.sh`/`host.sh`, Flatpak/Deck, MCP de Playwright, `mapa-agente`,
`matriz-pruebas`, hallazgos, `opt-ai` (IA local; quizá módulo opcional), identificadores de tareas (`QA-`, `INS-`,
`UX-`…), nombres de personas, juegos e instaladores de referencia, y el contenido de `REVIEW.md` y `GLOSSARY.md`.
Los mensajes de los scripts están en español: se pasan a inglés (§4.4).

## De paso: prueba de la opción D en una sesión real

Tras reiniciarse el proceso de esta sesión en la nube, la skill `galivelop-workflow:gw-ping` apareció cargada:
el plugin se había instalado a nivel de usuario en el contenedor antes del reinicio. Confirma que **un plugin
instalado antes de que arranque Claude carga en la nube**, que es en lo que se apoya la opción D (falta probarlo
desde el script de configuración del entorno). Las skills de proyecto de los dos repos añadidos también cargaron.
