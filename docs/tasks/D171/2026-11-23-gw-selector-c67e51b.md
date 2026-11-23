# 2026-11-23 · gw-selector · pending · D171

## Why

`doctor.py` copiaba `is_workflow` de `review-scope.py` («un dato, un sitio») y avisaba de más con `--root <proyecto>` desde un clon del flujo.

## Alternatives

Importar desde `review-scope.py` (su nombre con guion no se importa limpio): descartado; `config.py` ya es el sitio común.

## Changed because

Nada aún: primera entrada.
