# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) · Versiones: [SemVer](https://semver.org/).
Cada entrada lleva `### ES` y `### EN`. La versión vive solo en `.claude-plugin/plugin.json`; el CI comprueba que
tiene entrada aquí.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versions: [SemVer](https://semver.org/). Each
entry has `### ES` and `### EN`. The version lives only in `.claude-plugin/plugin.json`; CI checks it has an entry
here.

## [0.1.0] - Unreleased

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
- Matt Pocock's skills (mattpocock/skills, MIT) with his credit in each one, `CREDITS.md` and acknowledgements in the
  READMEs: we learned this way of working from his work.
