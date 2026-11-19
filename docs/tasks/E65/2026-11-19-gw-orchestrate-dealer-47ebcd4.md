# 2026-11-19 · gw-orchestrate-dealer · pending · E65

## Why

Revisión de E65 (7 hallazgos): el id salía de HEAD (un merge o un commit de main), la spike y `commitLedger` no se respetaban, se commiteaba sin nada que fusionar y `--root` no pasaba por `find_root`.

## Alternatives

Leer el id de la bitácora: descartado; `git log --first-parent --no-merges` basta y no añade claves.

## Changed because

Cambia merge-main.py (+ copia .claude/gw), las plantillas, README.es.md y los tests.
