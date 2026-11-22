# 2026-11-22 · gw-worker · pending · D150

## Why

Revisión: el aviso mandaba a `workflowClone` también cuando fallaba apply.py --vendored, y repetía la orden de review-scope.

## Alternatives

Redactar el aviso sin clave: descartado, la causa de falta de clon sí se arregla con ella.

## Changed because

Hallazgos 1 y 2 de la revisión de D149/D150.
