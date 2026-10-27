# Harvest verinews_ai — 2026-10-26

De `a9b5761e` a `693ec58d` (`scripts/recoger.py`, 5 commits; el proyecto usa la v0.4.0). Las ideas salen de las
retros de `docs/registros/` y de `docs/registros/propuestas-al-flujo-2026-10-26.md` @ `2cbb149`. Lo marcado «por
confirmar» se reproduce antes de aplicarlo.

## P1. `ciIgnore`: estados de CI ajenos que no bloquean la fusión

- **Source:** `docs/registros/retro-2026-10-26-galivelop-v040.md` @ `2cbb149` (R5) (script)
- **What changes:** `scripts/revision-antes-de-main.sh` (~l.524-536) cuenta como rojo cualquier estado que no sea
  `success`, también el despliegue de Vercel pendiente o en rojo. Una clave `ciIgnore` en `.claude/gw.json` (con su
  entrada en `docs/es|en/config.md`) lista los contextos que no cuentan.
- **Why it is general:** cualquier proyecto con un despliegue que publica estados en GitHub se queda con el PR
  bloqueado aunque su CI esté en verde.
- **Version bump:** minor → 1.0.0 (clave nueva)
- **Status:** aprobada (2026-10-27)

## P2. Firmas del agente en PR, comentarios y `user.email`

- **Source:** `docs/registros/retro-2026-10-26-galivelop.md` @ `2cbb149` (R1/R4) (script)
- **What changes:** la 1.0.0 ya rechaza firmas en los mensajes de commit (`agentSignatures`). Faltan dos cosas: que
  `scripts/session-start.sh` avise si `git config user.email` es `noreply@anthropic.com`, y que el gancho PreToolUse
  mire el cuerpo de un PR, issue o comentario de las herramientas de GitHub con `agentSignatures: false`.
- **Why it is general:** los PR y los comentarios son por donde se cuelan las firmas cuando el commit ya está limpio.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P3. Nombres de secretos que el `pre-commit` no ve

- **Source:** `docs/registros/propuestas-al-flujo-2026-10-26.md` @ `2cbb149` (script)
- **What changes:** `NAME` en `templates/githooks/pre-commit:61` no casa con `api.key` ni con nombres pegados como
  `openaikey`; ampliar a `[Aa][Pp][Ii][._-]?[Kk][Ee][Yy]` y revisar el sufijo. Con su caso en los tests (que el aviso
  diga el nombre).
- **Why it is general:** es un hueco del filtro de secretos de todos los proyectos.
- **Version bump:** patch (corrección, `0.4.2`)
- **Status:** aprobada (2026-10-27)

## P4. `fusionar.sh` sin los tests relacionados

- **Source:** `docs/registros/propuestas-al-flujo-2026-10-26.md` @ `2cbb149` (script)
- **What changes:** `scripts/fusionar.sh` corre el check pero no `relatedTests` (`tests-relacionados.sh`), que sí
  corre el `pre-push`; la rama de un subagente puede volver con un test roto que solo salta al subir.
- **Why it is general:** afecta a todo proyecto con `relatedTests`.
- **Version bump:** patch (corrección, `0.4.2`): se reproduce, `fusionar.sh` no llama a `tests-relacionados.sh`
- **Status:** aprobada (2026-10-27)

## P5. `rojo-sin-arreglo.sh`: arreglo ya commiteado y tipo de rojo

- **Source:** `docs/registros/retro-2026-10-26-galivelop-v040.md` @ `2cbb149` (R6) y
  `docs/registros/retro-2026-10-26-qa12-veriai.md` @ `693ec58` (R1) (script)
- **What changes:** `--fix-at <commit>` para un arreglo ya commiteado (hoy exige cambios sin commitear); y distinguir
  un rojo por compilación de uno por la aserción (hoy `--fails-with` solo lo mitiga).
- **Why it is general:** el script es del flujo y los dos casos salen en cualquier proyecto.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P6. Aviso de código sin revisar desde la última marca

- **Source:** `docs/registros/retro-2026-10-26-fase-d-1.8.md` @ `c22ba7a` (R1) (script)
- **What changes:** `scripts/revisado.sh` lista los archivos de código cambiados desde la marca anterior (o desde la
  fase 1) para que los arreglos de la fase 2 no lleguen a `main` sin revisión.
- **Why it is general:** es el hueco de la fase 3 en todos los proyectos.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P7. `bitacora.py set-row`

- **Source:** `docs/registros/retro-2026-10-26-fase-b-1.8.md` @ `02ac654` (P1) (script)
- **What changes:** editar la fila propia a mitad de tarea sin cerrarla (hoy solo hay `close-row`), con el límite
  de 600 caracteres comprobado; y su entrada en `docs/es|en/patrones.md`.
- **Why it is general:** todos editan esa fila a mano varias veces por tarea.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P8. `doctor.py` avisa de `cd <carpeta> && …` sin `worktreeLinks`

- **Source:** `docs/registros/retro-2026-10-26-fase-b-1.8.md` @ `02ac654` (R2) (script)
- **What changes:** si una orden de `check` entra en una subcarpeta con `node_modules` o `.venv` que no está en
  `worktreeLinks`, `doctor.py` avisa: en el worktree temporal del `pre-push` esa carpeta no existe.
- **Why it is general:** el fallo es difícil de ver y le pasa a cualquier monorepo.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P9. Encargo de revisión con `git diff --stat`

- **Source:** `docs/registros/retro-2026-10-26-qa12-veriai.md` @ `693ec58` (R2) (skill)
- **What changes:** en `skills/orchestrate-dealer/SKILL.md`, el encargo de un subagente revisor empieza por
  `git diff --stat origin/main` y pide decir cada archivo leído o descartado.
- **Why it is general:** evita revisiones que se saltan archivos sin decirlo.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P10. Textos menores de `AGENTS.md` y `opt-tokens`

- **Source:** `docs/registros/retro-2026-10-26-galivelop-v040.md` @ `2cbb149` (T1-T3) (plantilla)
- **What changes:** `/clear` también tras un commit `WIP:` de relevo; `perPage: 1` al mirar el CI de la última
  subida; `git fetch -q && git status -sb` en el paso 2 de inicio.
- **Why it is general:** ahorros de tokens pequeños en todos los proyectos.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P11. Menores por confirmar

- **Source:** `docs/registros/propuestas-al-flujo-2026-10-26.md` @ `2cbb149` y
  `docs/registros/retro-2026-10-26-fase-d-1.8.md` @ `c22ba7a` (scripts y plantillas)
- **What changes:** `mapa-agente.py` con métodos Java con tipo de retorno; `tests-relacionados.sh` con archivos
  borrados; formato `csk-` en `KEY_FORMATS`; excluir rutas de contenido en el `pre-commit`; `setup-node` en
  `comprobar.yml` si el `package.json` está en una subcarpeta; aviso de `medir.py` cuando no ve subagentes; receta
  `git merge -s ours` para reiniciar una rama fusionada sin `--force`.
- **Why it is general:** todas tocan piezas del flujo; las dos primeras serían correcciones si se reproducen.
- **Version bump:** patch `0.4.2` (Java en `mapa-agente.py`); minor → 1.0.0 (archivos borrados en `tests-relacionados.sh`)
- **Status:** aprobada en parte (2026-10-27): `mapa-agente.py` con métodos Java, en la `0.4.2` (se reproduce: ni `void run() {` se reconocía); `tests-relacionados.sh` con archivos borrados, a la `1.0.0` (es el comportamiento que documenta su cabecera, no un defecto); el resto, descartado

## Stays in the project

- P2 de `fusion-pr2`, `deployAuthor`: es de Vercel Hobby; el proyecto ya lo aplica en su `AGENTS.md`.
- `branches-ignore` de `comprobar.yml`: en el flujo es deliberado.

## Ya está

- Firmas en los mensajes de commit: `agentSignatures` en la 1.0.0.
- P3 de `fusion-pr2` (`requireRetro` en un PR de solo contenido): el gancho ya no pide marca con solo contenido; el
  proyecto corrió `revisado.sh` por su propia regla.
