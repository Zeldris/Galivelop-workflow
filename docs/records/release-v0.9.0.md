# Release de GitHub `v0.9.0` (textos)

- **Etiqueta:** `v0.9.0`, sobre `8357389`, el commit de `main` de la subida del 2026-11-24.
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** pendiente (la nube no sube etiquetas: 403 del proxy). Decidido por el usuario (2026-11-24): la crea un agente desde una sesión local, con estos textos y sobre `8357389`.

```text
Galivelop-workflow v0.9.0
```

````markdown
## Galivelop-workflow v0.9.0 — 2026-11-24

**ES** · [English below](#en)

Versión «Front».

### Cambios

- Idiomas (A12): bloque `languages` en `.claude/gw.json` (`code`, `docs`, `public`, `ui`) y el idioma del agente por
  usuario en `~/.claude/gw.json`; `language` y `visibleLanguages` migran con `apply.py --update`.
- Perfiles (E4): `profile.py` y perfiles por persona y por cargo; el CI siempre usa `default`.
- Front (E5, E7, E9-E16, E78): pruebas de front con `front.py run full` (capturas, accesibilidad, matriz), su guía en
  `docs/es/patterns.md` y el sello de versión de Playwright de las capturas.
- Webs (E42, E50): skill `gw-seo` y aviso de `whole-read.py` al leer capturas sueltas (clave `screenshotSheet`).
- De la recogida de apertura (E65-E77): `merge-main.py` commitea el ledger de métricas antes de fusionar; aviso de
  `/clear` al cerrar una tarea (`contextGuard.clearAfterTask`); `wholeReadDenyPaths`; `actionlint` en el check; clave
  `generated`; `projectSkillPrefix`; aviso al leer otro repo; `measure.py` separa el arranque fijo.
- Retros (E84-E86, D176, D177): `push.sh --wip`, avisos de `whole-read.py` por `Bash`, reparto de la revisión de la
  fase 1 (`review.splitLines`), aviso de `/clear` al cerrar una fila (`clearOnTaskClose`) y de pendientes que citan
  un id cerrado (`pendingClosedIdCheck`).
- Arreglos de las revisiones (D167-D175, D178): copias instaladas de `gw-opt-tokens` y `pre-commit` al día,
  `is_workflow` en `config.py`, leves de `recover.py`, `whole-read.py` y `handoff.py`, y aviso de modelo tras
  compactar en `recover.py --state`.

---

<a id="en"></a>

**EN**

"Front" release.

### Changes

- Languages (A12): `languages` block in `.claude/gw.json` (`code`, `docs`, `public`, `ui`) and the agent's language
  per user in `~/.claude/gw.json`; `language` and `visibleLanguages` migrate with `apply.py --update`.
- Profiles (E4): `profile.py` and per-person and per-role profiles; CI always uses `default`.
- Front end (E5, E7, E9-E16, E78): front-end tests with `front.py run full` (screenshots, accessibility, matrix),
  their guide in `docs/en/patterns.md` and the Playwright version stamp of the screenshots.
- Websites (E42, E50): `gw-seo` skill and a `whole-read.py` warning when loose screenshots are read
  (`screenshotSheet` key).
- From the opening harvest (E65-E77): `merge-main.py` commits the metrics ledger before merging; `/clear` warning
  when a task closes (`contextGuard.clearAfterTask`); `wholeReadDenyPaths`; `actionlint` in the check; `generated`
  key; `projectSkillPrefix`; warning when reading another repo; `measure.py` shows the fixed start-up apart.
- Retros (E84-E86, D176, D177): `push.sh --wip`, `whole-read.py` warnings for `Bash` reads, split of the phase-1
  review (`review.splitLines`), `/clear` warning when a task row closes (`clearOnTaskClose`) and of pending entries
  citing a closed id (`pendingClosedIdCheck`).
- Review fixes (D167-D175, D178): installed copies of `gw-opt-tokens` and `pre-commit` up to date, `is_workflow` in
  `config.py`, minor fixes in `recover.py`, `whole-read.py` and `handoff.py`, and a model notice after compaction in
  `recover.py --state`.
````
