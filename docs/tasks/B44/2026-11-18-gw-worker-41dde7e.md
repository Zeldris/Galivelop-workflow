# 2026-11-18 · gw-worker · pending · B44

## Why

El registro de desviaciones de la `0.8.0` tenía cientos de entradas de sello y de copias de `apply.py`; tapaban las reales.

## Alternatives

Recalcular la lista de copias dentro de `scope-guard.py`: descartado, se reutiliza `review-scope.vendored` (`apply.py --vendored`).

## Changed because

Sin repo del flujo (`$GW_WORKFLOW`) no salta nada: falla del lado seguro. Un commit de sello queda en silencio por el filtro de cabeceras; `chore` ya no exige ficha.
