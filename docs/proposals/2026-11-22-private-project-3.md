# Harvest private-project-3 — 2026-11-22

De `12badcbd` a `d7d8def` (`scripts/harvest.py`). 14 commits; skills y scripts iguales a `da1a462` (`0.8.1`). Lo
nuevo sale de `docs/records/retro-2026-11-19-gw-update-0-8-1.md` y de dos cambios de su `.claude/gw.json`.

## P1. `tests-for.py --run` no pasa shellcheck a las copias del flujo

- **Source:** `.claude/gw.json` @ `90216aa` (config)
- **What changes:** `run_shellcheck` (`scripts/tests-for.py`) salta los `.sh` bajo `.claude/gw/` (ya se revisan en el
  flujo), o el aviso D137 de `doctor.py` propone la entrada de `relatedTests` con `paths`.
- **Why it is general:** con `tests-for.py --run {files}` en `relatedTests.fast` (lo que propone D137) y sin
  shellcheck en la nube, el `pre-push` falló tras un `/gw-update` que tocó scripts `.sh`, antes de correr los tests.
- **Version bump:** patch
- **Status:** aprobada (2026-11-22) → D152

## Joined to another proposal

- Retro P1 (el ledger fuera del árbol hasta el commit de trabajo; 5 turnos y ~0,5M): con
  `2026-11-22-private-project-6.md` P1.

## Stays in the project

- `testMap` de su paquete (`3fb014c`); retro P4 (una línea de su `AGENTS.md`); retro P2 (desconectar Claude Docs, lo
  hace la persona).

## Already here

- Retro P3 (`measure.py` sin `--session` mide una sesión vieja): `pending.md`, D144 (antes «D142», id repetido).
- Separar el arranque fijo en `measure.py`: E76.
