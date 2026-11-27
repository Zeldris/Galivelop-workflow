# Revisión de seguridad E28 (2026-11-27)

Cuatro lectores de solo lectura sobre `ccr-96d7a385-yx2p8o` (`2caa6f2`): ganchos, scripts que no llaman los
ganchos, permisos con CI y secretos, y la skill
[`cloudflare/security-audit-skill`](https://github.com/cloudflare/security-audit-skill).

**Skill de Cloudflare:** licencia MIT («Copyright (c) 2025-2026 Cloudflare, Inc.»); copiar o adaptar texto obliga a
conservar el aviso. De ella se toma solo el criterio, sin texto: un hallazgo nombra a quién tiene menos confianza, qué
frontera cruza y qué resultado se observa; si no, es una nota de endurecimiento. Clases que aplican aquí: inyección en
órdenes, código no confiable en CI con privilegios, inyección de expresiones en CI, entradas sin fijar, token de CI con
más permiso del necesario, ficheros locales.

**Secretos:** ninguno real en el árbol ni en el historial (`ghp_`, `github_pat_`, `sk-ant-`, `AKIA`, claves privadas,
asignaciones); el único acierto es el dato de prueba marcado `gw-allow-secret` de `tests/test_review_before_main.py`.
**CI:** sin `pull_request_target` ni `workflow_run`, y sin `${{ github.event.* }}` dentro de un `run:`.

Severidad: alta, media, baja. «Decisión» la rellena el usuario (pregunta de la columna).

## A. Opciones de git inyectadas desde el config

| Id | Dónde | Sev. | Problema | Arreglo propuesto |
|---|---|---|---|---|
| A1 | `scripts/merge-main.py:108`, `scripts/reviewed.sh:74`, `schema/gw.schema.json` (`protectedBranch`) | media | `git fetch origin <protectedBranch>` sin `--` y el esquema solo pide `minLength`: `"protectedBranch": "--upload-pack=…"` ejecuta una orden con un remoto local | `pattern` en el esquema (sin `-` inicial ni caracteres de ref inválidos) y refspec explícito |

## B. Escrituras y borrados que siguen enlaces simbólicos

| Id | Dónde | Sev. | Problema | Arreglo propuesto |
|---|---|---|---|---|
| B1 | `scripts/apply.py:1927,1933` | media | `write_bytes` y `shutil.rmtree` siguen un enlace del repo (`.githooks/pre-commit` o `.claude/gw` → `~/.bashrc`) en `--update` | el padre real, bajo la raíz; escribir con temporal + `os.replace` |
| B2 | `scripts/metrics.py:700` (gancho `Stop`), esquema `metrics.ledger` | media | añade filas a `ledger` sin contener la ruta: `"../../.bashrc"` o un `ledger.jsonl` enlazado | ruta relativa sin `..` en el esquema; al escribir, sin enlace y bajo la raíz |
| B3 | `scripts/ci-local.py:957` | baja | `--record` escribe a través de un enlace | igual que B2 |
| B4 | `scripts/whole-read.py:644`, `scripts/session-start.sh:~236` | baja | candado y registros con nombre fijo en `/tmp`, abiertos siguiendo enlaces | `O_NOFOLLOW` o carpeta privada (`mktemp -d`) |

## C. CI y `.gitignore`

| Id | Dónde | Sev. | Problema | Arreglo propuesto |
|---|---|---|---|---|
| C1 | `.github/workflows/release.yml:7-8` | media | `contents: write` en todo el workflow: `verify` y el `check` llamado corren scripts del repo con token de escritura | `contents: read` arriba; `write` solo en el job `release` |
| C2 | `release.yml:15,63`, `templates/github/check.yml` | baja | `checkout` sin `persist-credentials: false` | añadirlo |
| C3 | `check.yml`, `release.yml`, `templates/github/check.yml` | baja | acciones fijadas por etiqueta, no por SHA (incluida `Swatinem/rust-cache@v2`, de terceros) | fijar por SHA con la versión en un comentario |
| C4 | `.gitignore`, `templates/gitignore/*` | media | no ignoran `.env`, `.env.*` ni `.claude/settings.local.json` (que `apply.py` usa) | añadirlos al repo y a un bloque común de la plantilla |

## D. Código del repo abierto que se ejecuta sin preguntar

| Id | Dónde | Sev. | Problema |
|---|---|---|---|
| D1 | `scripts/session-start.sh:~86` | media | con `core.hooksPath` vacío y `.githooks/` presente, lo activa: los ganchos de un repo clonado corren en el primer commit |
| D2 | `scripts/session-start.sh:~226` | media | corre `install`/`setup` de `.claude/gw.json` con `bash -c` al arrancar en la nube |
| D3 | `scripts/front.py:600,819` | media | `npm ci` sin `--ignore-scripts` (en Docker, como root y con `dockerImage` del config) |
| D4 | `scripts/ci-local.py:839,832` | media | los `run:` de los workflows reciben todo el entorno (tokens) y `working-directory` puede salir del repo |
| D5 | `scripts/questions-guard.py:183` | media | ejecuta `<repo>/scripts/is-code.sh` del proyecto en cada Edit/Write, aunque el repo no use el flujo |
| D6 | `scripts/mkt-sheet.py:393`, `scripts/review-scope.py:118` | baja | cargan Playwright del `node_modules` del repo y `apply.py` de la carpeta `workflowClone` |
| D7 | `check`, `relatedTests` del config con `bash -c` (`check.sh`, `push.sh`, `related-tests.sh`) | obs. | diseño: el config manda; los ganchos vigilan sus ediciones |

## E. Guardas que se saltan

`careful.py` y `review-before-main.sh` frenan errores del modelo, no a un atacante; aun así:

| Id | Dónde | Sev. | Se salta con |
|---|---|---|---|
| E1 | `scripts/careful.py:158` | media | abreviaturas que git acepta: `--force-with-lea`, `--delet`, `--mirro`, `git reset --ha` |
| E2 | `scripts/careful.py:171` | media | refspecs tras `--`: `git push -- origin +main` |
| E3 | `scripts/careful.py:215` | media | `$(…)`, comillas invertidas, `env -S`, `bash <<<`, `{ …; }`, `$g push -f`, `bash <<EOF` |
| E4 | `scripts/review-before-main.sh:70` | media | lo mismo para `gh pr merge`; además `gh alias`, `gh api graphql … mergePullRequest`, `gh pr edit --base main`, `gh api … -X PATCH -f base=main`, `curl … /pulls/N/merge` |
| E5 | `scripts/agent-signatures.py:~134` | baja | firma en `--body "$(cat f)"`; patrones del config sin tope (ReDoS) |

## F. Leves

| Id | Dónde | Problema |
|---|---|---|
| F1 | `scripts/ci-status.py:277,333` | `--branch`, `--sha`, `--repo` sin codificar en la ruta de la API (solo GET a api.github.com) |
| F2 | `scripts/config.py:1695` (`related-tests.sh:66`) | un fichero llamado `--rootdir=/x` llega como opción al comando de tests |
| F3 | `scripts/harvest.py:196,377,409,421,511` | lee `.md` enlazados a `~/.ssh/…` de un proyecto recogido y los vuelca al informe |
| F4 | `.claude/agents/gw-reviewer.md:4` | el revisor tiene `Write` y `Bash` sin límite; «sin editar» es solo prosa |
| F5 | `.claude/settings.json` | sin `permissions`; una capa `ask` para `git push --force*` y `--delete` sería un segundo cerrojo |
| F6 | `scripts/task.py`, `scripts/red-without-fix.sh`, `scripts/harvest.py` (git en clones ajenos) | rutas o órdenes que vienen del agente o de clones copiados; sin verificar |

## Decisiones

Pendientes del usuario (2026-11-27).
