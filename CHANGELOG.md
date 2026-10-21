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
- Matt Pocock's skills (mattpocock/skills, MIT) with his credit in each one, `CREDITS.md` and acknowledgements in the
  READMEs: we learned this way of working from his work.
