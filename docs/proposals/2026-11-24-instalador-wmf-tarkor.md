# Harvest instalador-wmf-tarkor — 2026-11-24

De `50535c7` a `56f0108` (`scripts/harvest.py`). 16 commits; ningún skill ni script cambiado. Lo nuevo sale de
`docs/records/retro-2026-11-24-flu-15.md` (cuatro ideas).

## P1. `check.yml`: el venv de actionlint no se pone entero en `PATH`

- **Source:** `retro-2026-11-24-flu-15.md` @ `56f0108` (arreglo `790b752` en el proyecto) (plantilla + CI)
- **What changes:** el paso «Install actionlint» hace `echo "$RUNNER_TEMP/actionlint/bin" >> "$GITHUB_PATH"` en
  `.github/workflows/check.yml` y `templates/github/check.yml`; desde ahí el `python3` de los pasos siguientes es el
  del venv y pierde los paquetes del sistema (PyYAML: `test_workflows_yaml` no cargaba). Poner en `PATH` solo el
  binario (enlace en un directorio aparte) y un test de que `PATH` no gana un `python3`. La plantilla es la fuente.
- **Why it is general:** cualquier proyecto con `ciActionlint` distinto de `off` y dependencias Python previas; el
  proyecto lo esquivó con `"ciActionlint": "off"`.
- **Version bump:** patch (arreglo)
- **Status:** aprobada (2026-11-24) → B50 (`0.9.1`)

## P2. `gw-update` comprueba que la clave existe antes de recomendarla

- **Source:** `retro-2026-11-24-flu-15.md` @ `56f0108` (skill)
- **What changes:** un paso: antes de recomendar excluir o apagar algo, mirar en `config.py`/`apply.py` que la clave
  existe (habría recomendado una clave de exclusión inexistente).
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B51 (`0.9.1`)

## P3. Clave `skillsExclude` para no instalar skills sin uso

- **Source:** `retro-2026-11-24-flu-15.md` @ `56f0108` (script + config)
- **What changes:** clave `skillsExclude: []` en `gw.json` (esquema, `config.py`, `docs/{es,en}/config.md`) que
  respetan `apply.py --update`/`--check` y `doctor.py` (hoy solo hay `OPTIONAL_SKILLS | WORKFLOW_ONLY_SKILLS`).
- **Why it is general:** un proyecto sin web no quiere `gw-seo`; sirve a todo el que no tenga el dominio.
- **Version bump:** minor (evolutivo)
- **Status:** aprobada (2026-11-24) → E90 (`0.11`)

## P4. `push.sh` dice la ruta del registro y que hay un bloqueo

- **Source:** `retro-2026-11-24-flu-15.md` @ `56f0108` (script)
- **What changes:** al empezar el check del `pre-push` imprime en stderr la ruta del registro y «lock held, a long
  check is running», con un test del texto.
- **Why it is general:** un check de más de 20 min parece colgado.
- **Version bump:** patch
- **Status:** aprobada (2026-11-24) → B55 (`0.9.1`)

## Stays in the project

- Commits FLU-15: subida a `0.8.2` y `0.9.0`, copia de `gw-seo`, avisos RUSTSEC de dependencias Rust, PyYAML por
  `apt`.
