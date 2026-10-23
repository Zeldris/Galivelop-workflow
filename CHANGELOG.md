# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · Versiones: [SemVer](https://semver.org/).
Cada entrada lleva `### ES` y `### EN`. La versión vive solo en `.claude-plugin/plugin.json`; el CI comprueba que
tiene entrada aquí.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versions: [SemVer](https://semver.org/). Each
entry has `### ES` and `### EN`. The version lives only in `.claude-plugin/plugin.json`; CI checks it has an entry
here.

## [0.3.0] - 2026-10-23

### ES

Propuestas de los pilotos de la Fase 6, World-Maker-Fantasy y el instalador
(`docs/propuestas/2026-10-23-world-maker-fantasy.md` y `…-instalador-wmf-tarkor.md`). La P7 del instalador (CI pasado
en local) queda aplazada.

- `taskId` con grupos de captura ya no rompe `bitacora.py closed`; `doctor.py` acepta «Siguientes pasos» (inst. P1, P2).
- `revisado.sh`: ignora los archivos sin seguimiento, lee el párrafo entero del Estado, acepta «aprobad*» y añade
  `--footer` para la línea `Siguiente:` (WMF P1).
- `pre-commit` limpia `GIT_DIR`, `GIT_WORK_TREE` y `GIT_INDEX_FILE` en un worktree enlazado (WMF P2).
- `doctor.py`: reconoce los ganchos del flujo por su cabecera, exige que `reviewMark` esté en seguimiento y avisa de
  términos repetidos en `GLOSSARY.md` (WMF P3, P9).
- `bitacora.py closed` y `check`, más estrictos; `rojo-sin-arreglo.sh --ran-one` (WMF P4).
- Gancho del PR: sale pronto si la orden no es suya, prueba el acceso leyendo el propio repo (`gh api repos/<o>/<r>`,
  que también vale con un token de GitHub App) y explica un PR cerrado o fusionado (WMF P5).
- `es-codigo.sh` distingue una regex inválida de otros fallos (WMF P6).
- Claves nuevas: `checkWrapper`, `worktreeLinks`, `relatedTests` con `paths` y `cwd`, `ciInstall`, `setup`,
  `staleRefs` con `skip`, `linkRoots` y `scoutDir` (WMF P10-P13, inst. P3, P6).
- `pre-push`: worktree en una carpeta por repo bajo `${TMPDIR:-/tmp}` (o `worktreeDir`, clave nueva, para un sandbox
  que no ve `$TMPDIR`), con limpieza de huérfanos de más de 24 h, logs con `mktemp` y rutas enlazadas que no salen
  del worktree (WMF P10).
- `session-start.sh`: `setup` tras `install`, con un límite por orden (`GW_COMMAND_TIMEOUT`) que mata su grupo de
  procesos (WMF P11).
- Toda skill lee sus notas en `.claude/gw/<skill>.md` (inst. P4).
- `opt-tokens/medir.py` con test y aviso de ventanas de compactación mezcladas; `opt-ai/medir.py` con tabla por turno;
  `scout-updates`: títulos en el idioma del proyecto y banco por pares a ciegas `quality_bench.py` (WMF P7, P8, P13).
- Plantillas con «la persona»; `aplicar.md`: `.gitignore` con `.claude/*`, scripts del flujo que no se editan en el
  proyecto, migrar desde una copia anterior y tests de las skills (inst. P5, P8, P9).

### EN

Proposals from the Phase 6 pilots, World-Maker-Fantasy and the installer
(`docs/propuestas/2026-10-23-world-maker-fantasy.md` and `…-instalador-wmf-tarkor.md`). Installer P7 (CI run
locally) is postponed.

- A `taskId` with capturing groups no longer breaks `bitacora.py closed`; `doctor.py` accepts «Siguientes pasos»
  (inst. P1, P2).
- `revisado.sh`: ignores untracked files, reads the whole Estado paragraph, accepts «aprobad*» and adds `--footer` for
  the `Siguiente:` line (WMF P1).
- `pre-commit` unsets `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE` in a linked worktree (WMF P2).
- `doctor.py`: recognises the flow's hooks by their header, requires `reviewMark` to be tracked and warns about
  repeated terms in `GLOSSARY.md` (WMF P3, P9).
- Stricter `bitacora.py closed` and `check`; `rojo-sin-arreglo.sh --ran-one` (WMF P4).
- PR hook: exits early for commands that are not its own, probes access by reading the repo itself
  (`gh api repos/<o>/<r>`, which also works with a GitHub App token) and explains a closed or merged PR (WMF P5).
- `es-codigo.sh` tells an invalid regex apart from other failures (WMF P6).
- New keys: `checkWrapper`, `worktreeLinks`, `relatedTests` with `paths` and `cwd`, `ciInstall`, `setup`,
  `staleRefs` with `skip`, `linkRoots` and `scoutDir` (WMF P10-P13, inst. P3, P6).
- `pre-push`: worktree in a per-repo folder under `${TMPDIR:-/tmp}` (or `worktreeDir`, a new key, for a sandbox that
  cannot see `$TMPDIR`), with cleanup of orphans older than 24 h, `mktemp` logs and linked paths that cannot leave the
  worktree (WMF P10).
- `session-start.sh`: `setup` after `install`, with a per-command limit (`GW_COMMAND_TIMEOUT`) that kills its process
  group (WMF P11).
- Every skill reads its notes from `.claude/gw/<skill>.md` (inst. P4).
- `opt-tokens/medir.py` with tests and a mixed-compaction-windows warning; `opt-ai/medir.py` with a per-turn table;
  `scout-updates`: headings in the project's language and the blind pairwise bench `quality_bench.py` (WMF P7, P8,
  P13).
- Templates say «the person»; `apply.md`: `.gitignore` with `.claude/*`, flow scripts are not edited in the project,
  migrating from an earlier copy and skill tests (inst. P5, P8, P9).

## [0.2.0] - 2026-10-22

### ES

Propuestas del piloto del portal y de la tercera recogida de Tarkor (reparto en
`docs/propuestas/2026-10-22-reparto.md`):

- `pre-push` y el gancho de PR juzgan la rama protegida con la config de la propia rama remota; `.claude/gw.json`
  cuenta como código (P1).
- Se buscan marcadores de conflicto en todo `base..local` (P16).
- `content` por defecto acotado en `templates/gw.json` (P9).
- Versión obligatoria si cambia algo copiable; los mensajes distinguen «edición local» de «copia anterior» (P2 a, b).
- `recuperar.py --estado` ya no se cuelga sin entrada (`select`) ni con la tubería cerrada (`BrokenPipeError`) (P5).
- Fuera las referencias a `.claude/hooks/` de la plantilla de `CLAUDE.md`, con un test de rutas obsoletas (P19).
- `aplicar.py` copia `LICENSE-mattpocock-skills` con las skills adaptadas (P17).
- `recoger.py` saca ideas de cualquier `.md` cambiado (P21).
- `retro` sin `disable-model-invocation`: el agente puede lanzarla (P4).
- `doctor.py` y `aplicar.py` avisan de archivos del flujo ignorados por git (`git check-ignore`) (P3).
- `doctor.py` avisa de propuestas `*.gw-nuevo` pendientes y de ganchos duplicados (P7).
- `aplicar.md`, paso 6: la prueba de la protección en simulacro (`--dry-run`) y sus dos mensajes (P12).
- `aplicar.py --init` con banderas para las claves que decide el proyecto; `requireRetro` con un solo valor por
  defecto (P10).
- `aplicar.py` imprime el diff de un `REVIEW.md` o `GLOSSARY.md` que ya existía (P18).
- El CI de la plantilla (`comprobar.yml`) detecta e instala su cadena con `setup-node`/`setup-python` (P13, en parte).
- `es-codigo.sh --explicar`; los tests de un fallo comprueban el motivo (P14 a, c).
- `recuperar.py --estado` muestra las secciones de la config que importan (P15 a).
- Al aplicar el flujo se lee con un subagente; fila nueva en `selector` y aviso en `opt-tokens` (P11).
- `orchestrate-dealer` (Tarkor P1-P4): los arreglos de una revisión van con `sonnet`; un arreglo de un archivo con el
  sitio dado lo hace la principal; antes del PR solo lo grave o medio; el worktree del encargo parte de
  `origin/<rama>`.

Retro antes de `main`:

- R1: `doctor.py` avisa (`compaction`) de una sesión en la nube sin `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en el entorno;
  fila en `problemas.md` / `troubleshooting.md`.
- R2: `orchestrate-dealer` reparte las filas aprobadas a subagentes, o la principal cierra cada 4-5 filas con
  `/clear`.
- R3: `tests/shellcheck.sh`; en la nube y en el CI falla sin shellcheck (remedio: `pip install shellcheck-py`); en
  local solo avisa.

Arreglos de las revisiones de código antes de `main`:

- Un `.claude/gw.json` inválido en la punta remota de una rama no protegida ya no bloquea la subida que lo arregla
  ni un PR hacia ella; el gancho de PR carga cada config una vez.
- `README.es.md`, `CHANGELOG.md` y `CREDITS.md` cuentan como contenido en `templates/gw.json`.
- `recuperar.py` espera 1 s la entrada del gancho `SessionStart`.
- `aplicar.py` importa `ignored_paths` y `stale_flow_hooks` de `doctor.py` (un dato, un sitio).
- `version.py --release` corre en el `pre-push` hacia `main` (`GW_PUSH_PROTECTED`) y compara con la última etiqueta
  alcanzable desde `HEAD`; `release.yml` ya no lo llama.
- `.claude/gw.json` de este repo instala `shellcheck-py` en la nube; `doctor.py` solo mira la ventana de
  compactación si el `settings.json` del proyecto la fija; `tests/shellcheck.sh` recibe los archivos de
  `comprobar.sh`.

### EN

Proposals from the portal pilot and the third Tarkor harvest (split in `docs/propuestas/2026-10-22-reparto.md`):

- `pre-push` and the PR hook judge the protected branch by the remote branch's own config; `.claude/gw.json` counts
  as code (P1).
- Conflict markers are searched in all of `base..local` (P16).
- Narrower default `content` in `templates/gw.json` (P9).
- A version bump is required when anything copyable changes; messages tell "local edit" from "older copy" (P2 a, b).
- `recuperar.py --estado` no longer hangs without input (`select`) nor on a closed pipe (`BrokenPipeError`) (P5).
- No more `.claude/hooks/` references in the `CLAUDE.md` template, with a stale-path test (P19).
- `aplicar.py` copies `LICENSE-mattpocock-skills` along with the adapted skills (P17).
- `recoger.py` takes ideas from any changed `.md` (P21).
- `retro` without `disable-model-invocation`: the agent can launch it (P4).
- `doctor.py` and `aplicar.py` warn about workflow files ignored by git (`git check-ignore`) (P3).
- `doctor.py` warns about pending `*.gw-nuevo` proposals and duplicated hooks (P7).
- `aplicar.md`, step 6: the protection test as a dry run (`--dry-run`) and its two messages (P12).
- `aplicar.py --init` with flags for the keys the project decides; `requireRetro` with a single default (P10).
- `aplicar.py` prints the diff of a `REVIEW.md` or `GLOSSARY.md` that already existed (P18).
- The template CI (`comprobar.yml`) detects and installs its toolchain with `setup-node`/`setup-python` (P13, part).
- `es-codigo.sh --explicar`; tests of a failure check the reason (P14 a, c).
- `recuperar.py --estado` shows the config sections that matter (P15 a).
- The workflow is read by a subagent when applying it; new row in `selector` and a warning in `opt-tokens` (P11).
- `orchestrate-dealer` (Tarkor P1-P4): review fixes go to `sonnet`; a one-file fix with its place given is done by
  the main session; before the PR only severe or medium findings; the task's worktree starts from `origin/<branch>`.

Retro before `main`:

- R1: `doctor.py` warns (`compaction`) about a cloud session without `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in its
  environment; row in `problemas.md` / `troubleshooting.md`.
- R2: `orchestrate-dealer` deals approved rows to subagents, or the main session closes every 4-5 rows with
  `/clear`.
- R3: `tests/shellcheck.sh`; in the cloud and in CI it fails without shellcheck (fix: `pip install shellcheck-py`);
  locally it only warns.

Fixes from the code reviews before `main`:

- An invalid `.claude/gw.json` at the remote tip of an unprotected branch no longer blocks the push that fixes it nor
  a PR into it; the PR hook loads each config once.
- `README.es.md`, `CHANGELOG.md` and `CREDITS.md` count as content in `templates/gw.json`.
- `recuperar.py` waits 1 s for the `SessionStart` hook's input.
- `aplicar.py` imports `ignored_paths` and `stale_flow_hooks` from `doctor.py` (one fact, one place).
- `version.py --release` runs in the `pre-push` to `main` (`GW_PUSH_PROTECTED`) and compares with the last tag
  reachable from `HEAD`; `release.yml` no longer calls it.
- This repo's `.claude/gw.json` installs `shellcheck-py` in the cloud; `doctor.py` only checks the compaction window
  if the project's `settings.json` sets it; `tests/shellcheck.sh` gets its files from `comprobar.sh`.

## [0.1.0] - 2026-10-22

### ES

- Esqueleto del repo: licencia MIT, `AGENTS.md` y `CLAUDE.md` (el repo usa su propio flujo), README en inglés y
  español, bitácora, manifiestos de plugin y marketplace, y CI que valida JSON, scripts, pares ES/EN y que esta
  versión tenga entrada.
- Plan revisado tras la Fase 0 (`docs/plan.md` §0) e investigación en `docs/investigacion/`.
- Skills: 11 de Matt Pocock; propias `selector`, `orchestrate-dealer`, `opt-tokens` (+ `medir.py`), y opcionales
  `opt-ai` (IA local) y `scout-updates`; `gw-harvest` + `scripts/recoger.py` para recoger propuestas de los
  proyectos. Todas validadas contra la especificación Agent Skills.
- Ganchos y scripts (`config.py`, `pre-push`, `pre-commit`, `revisado.sh`, gancho de PR a la rama protegida,
  arranque, recuperación, `doctor.py`, utilidades) y `aplicar.py`; plantillas ES/EN; guías para aplicar el flujo,
  problemas conocidos, config, patrones y cómo contribuir; skills `gw-init`, `gw-update`, `gw-doctor`.
- Antes de la primera publicación, `/code-review` del conjunto: 10 arreglos (gancho de PR ante `gh -R`, `bash -c`,
  `xargs` y `gh api`; config leído del commit que se sube; marca exigida en toda subida directa a la rama protegida;
  scripts de guarda fuera de `content`; rama protegida configurable en las utilidades; falsos positivos del
  antisecretos; tests relacionados sobre el commit subido; scripts opcionales sin bit de ejecución; retro sin decidir
  rechazada; un solo backend de la API).
- Tras la retro de las fases 0-4: `requireRetro` activado por defecto en `templates/gw.json` (`revisado.sh` pide una
  retro decidida antes de marcar); las plantillas `AGENTS.md` piden `/clear` al cerrar cada fase y mirar el CI al
  cerrar cada bloque; `orchestrate-dealer` pide revisar las guardas al volver cada trozo; `gw-harvest` y las guías
  piden no registrar en la sesión los repos que solo se leen; `docs/mapa-agente.md` para los encargos.
- `scripts/version.py` (comprueba y sube todos los marcadores de versión) y `release.yml` (release desde la entrada
  del CHANGELOG al etiquetar `vX.Y.Z`); el `pre-push` ya no pregunta «did you commit?» al mover una rama a commits que
  el remoto ya tiene en otra.
- Segunda recogida de Tarkor (7 propuestas aplicadas): `orchestrate-dealer` revisa todo el código de subagentes, tandas
  de 6-8 puntos, encargos que leen su fila con `recuperar.py --estado`, subagentes cortados se retoman, estado
  intermedio fuera de git; `opt-ai` no compara con menos de ~8 turnos; `recoger.py` avisa de un clon atrasado.
- Retro de la segunda subida: los encargos de código de guarda piden listar los casos límite y probar cada uno antes
  de entregar.
- Skills de Matt Pocock (mattpocock/skills, MIT) con su mención en cada una, `CREDITS.md` y agradecimiento en los
  README: de su trabajo aprendimos esta forma de trabajar.

### EN

- Repository skeleton: MIT licence, `AGENTS.md` and `CLAUDE.md` (the repo uses its own workflow), README in English
  and Spanish, log, plugin and marketplace manifests, and CI that validates JSON, scripts, ES/EN pairs and that this
  version has an entry.
- Plan revised after Phase 0 (`docs/plan.en.md` §0) and research in `docs/investigacion/`.
- Skills: 11 by Matt Pocock; own `selector`, `orchestrate-dealer`, `opt-tokens` (+ `medir.py`), and optional
  `opt-ai` (local AI) and `scout-updates`; `gw-harvest` + `scripts/recoger.py` to harvest proposals from projects.
  All validated against the Agent Skills specification.
- Hooks and scripts (`config.py`, `pre-push`, `pre-commit`, `revisado.sh`, PR-to-protected-branch hook, session
  start, recovery, `doctor.py`, utilities) and `aplicar.py`; ES/EN templates; guides to apply the workflow,
  troubleshooting, config, patterns and contributing; `gw-init`, `gw-update`, `gw-doctor` skills.
- Before the first release, `/code-review` of the whole set: 10 fixes (PR hook against `gh -R`, `bash -c`, `xargs`
  and `gh api`; config read from the pushed commit; review mark required on every direct push to the protected branch;
  guard scripts out of `content`; configurable protected branch in the utilities; secret-scan false positives; related
  tests on the pushed commit; optional scripts without the exec bit; undecided retro refused; a single API backend).
- After the phase 0-4 retro: `requireRetro` on by default in `templates/gw.json` (`revisado.sh` asks for a decided
  retro before marking); the `AGENTS.md` templates ask for `/clear` when each phase closes and a CI look when each block
  closes; `orchestrate-dealer` asks for a review of guard code as each chunk returns; `gw-harvest` and the guides say
  not to register read-only repos in the session; `docs/mapa-agente.md` for briefs.
- `scripts/version.py` (checks and bumps every version marker) and `release.yml` (release from the CHANGELOG entry when
  tagging `vX.Y.Z`); `pre-push` no longer asks "did you commit?" when moving a branch to commits the remote already has
  in another.
- Second Tarkor harvest (7 proposals applied): `orchestrate-dealer` reviews all subagent code, batches of 6-8 items,
  briefs read their row with `recuperar.py --estado`, cut-off subagents are resumed, intermediate state out of git;
  `opt-ai` does not compare with fewer than ~8 turns; `recoger.py` warns about a stale clone.
- Second-push retro: briefs for guard code ask to list the edge cases and test each one before delivering.
- Matt Pocock's skills (mattpocock/skills, MIT) with his credit in each one, `CREDITS.md` and acknowledgements in the
  READMEs: we learned this way of working from his work.
