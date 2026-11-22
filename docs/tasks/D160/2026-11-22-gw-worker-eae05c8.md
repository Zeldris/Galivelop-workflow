# 2026-11-22 · gw-worker · pending · D160

## Why

La plantilla check.yml escribe `.gw-ci/` en el árbol y dejaba `dirty()` en rojo.

## Alternatives

Cambiar la plantilla a $RUNNER_TEMP: toca copias generadas; borrar en ci-local es local.

## Changed because

Ninguna desviación.
