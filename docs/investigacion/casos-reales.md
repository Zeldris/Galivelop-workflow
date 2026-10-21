# Fase 0 — Tres casos reales del flujo

> Inventario del 2026-10-21 de **World-Maker-Fantasy (Tarkor)**, **Instalador-WMF-Tarkor** y **Portal-Galivelop**
> (este último es público; clon anónimo de solo lectura), leídos con subagentes. Sirve para contrastar el plan con lo que de verdad se usa. Rutas relativas a la raíz de cada
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

## Portal-Galivelop (fuente principal según el plan)

- **Sube a `main` directamente** (GitHub Pages), con confirmación; la tarea programada semanal sube la rama de
  trabajo a `main` **sin** confirmación, así que la rama tiene que estar siempre publicable.
- **Bitácora** `docs/traspaso.md` sin filas por rama ni límite de caracteres (no tiene `bitacora.py`).
- **Marca de revisado versionada** en `docs/registros/revisado.txt`; `revisado.sh` exige árbol limpio, HEAD ==
  `origin/<rama>` y `origin/main` como antecesor, y hace commit «Revisado: …». No exige retro.
- **`pre-push`**: lee stdin primero, corre `npm run check` sobre **el commit que se sube** (worktree temporal si no es
  HEAD limpio), y a `main` exige la marca como antecesora sin código después (`es-codigo.sh`). Falla cerrado.
- **Raíz** desde `dirname "$0"` o `git rev-parse` en todos los ganchos (la lección de la §12 sí está aplicada).
- **Los «29 fallos»** no tienen archivo de retro: son dos rondas de `/code-review` (14 + 15) apuntadas en la bitácora
  y en `REVIEW.md` § «Ganchos y scripts». Categorías: raíz desde `$CLAUDE_PROJECT_DIR`/cwd; el gancho miraba la
  carpeta y no el commit subido; fallar abierto sin datos; flujo por PR y marca ignorada sin adaptar a subida directa;
  falta de tests. `tools/qa/tests/test-ganchos.sh` cubre **8 casos de `pre-push`** y nada más (ni
  `revision-antes-de-main.sh`, ni `session-start.sh`, ni `revisado.sh`, ni `recuperar.py`).
- **Skills** recortadas respecto a Tarkor; solo aporta la fila «Traer algo de otro repo» del `selector` y el respaldo
  de `medir.py` para sesiones que arrancan en `/home/user`.
- `npm run check` = `tsc -b && vitest run && bash tools/qa/tests/test-ganchos.sh`; CI `comprobar.yml` en PR y en
  push a ramas que no son `main`.

### La mejor versión de cada pieza

| Pieza | De dónde portarla |
|---|---|
| `pre-push` (commit subido en worktree, marca para `main`, fallar cerrado) | Portal, + lo genérico del instalador (`prepush-ramas.sh`, lista de commits subidos) |
| `revision-antes-de-main.sh` | Instalador (`git ls-remote` sin escribir refs, auto-merge y `update_pull_request` cuentan, matcher anclado) + del portal: statuses además de check-runs, raíz por `dirname` |
| Marca de revisado | Portal (versionada; vale para subida directa y para PR) |
| `revisado.sh` | Portal + retro exigida de Tarkor/instalador como opción del config |
| Bitácora con filas por rama + `bitacora.py` | Instalador (`ROADMAPS` configurable, `[x]`) |
| `recuperar.py`, `medir.py` | Portal (respaldo de rutas en la nube) |
| `selector`, `orchestrate-dealer`, `retro`, `opt-tokens` | Tarkor/instalador (más completos) + fila «traer de otro repo» del portal |
| Tests de ganchos | Portal como base; faltan casos del resto de scripts |
| `REVIEW.md` § «Un dato, un sitio» y § «Ganchos y scripts» | Portal |
| Roadmap e hitos | Tarkor (`cobertura.py`, `cerrar.py`) |

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

> **Decidido (2026-10-21):** el usuario aprobó las propuestas; ver `docs/plan.md` §0.

1. **Marca de revisado.** Tarkor y el instalador la tienen en `.claude/revision-main.sha` ignorada por git; el portal,
   versionada, como dice el plan (§5.3). Confirmado: la versionada vale para los dos modos de subida.
2. **Un solo `check`.** Ninguno de los dos tiene una orden única: el check real es el `pre-push` + la CI. Propuesta:
   `check` admite una lista de órdenes, y `/gw-init` propone crear un `tools/check.sh` si no hay ninguna.
3. **Raíz del repo.** Los ganchos de Tarkor usan `$CLAUDE_PROJECT_DIR` o `pwd`, justo lo que la §12 prohíbe. El
   portal lo tiene arreglado (confirmado).
4. **`session-start.sh` falla cerrado en Tarkor y abierto en el instalador.** Para el plugin: la parte genérica
   (`core.hooksPath`, avisos) falla abierta con aviso; lo que bloquee de verdad está en `pre-push` y `PreToolUse`.
5. **Fuente principal.** No hay una: el portal es mejor en ganchos de subida y rutas, pero tiene las skills
   recortadas y no tiene bitácora por ramas; el instalador es más nuevo en `revision-antes-de-main.sh`. Se porta pieza
   a pieza según la tabla de arriba, no «del portal».
6. **Tests de los 29 fallos.** La Fase 3 pide incluirlos, pero solo existen 8 casos de `pre-push`. Los demás hay que
   escribirlos a partir de las categorías.
7. **Subida sin confirmación.** La tarea semanal del portal sube a `main` sola. El flujo tiene que admitir esa
   excepción explícita (documentada en `patrones.md`) sin abrir un agujero en los ganchos: la marca de revisado sigue
   siendo obligatoria si hay código.

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
