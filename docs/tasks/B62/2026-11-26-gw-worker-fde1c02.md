# 2026-11-26 · gw-worker · pending · B62

## Why

La revisión de B62 dio 3 hallazgos: la doc de `findingsWords` no nombraba la excepción, sin rama protegida se recorría toda la historia, y faltaban tests de esos dos bordes.

## Alternatives

- Sin rama protegida, recorrer desde HEAD hasta el primer commit sin el trailer: callaría el aviso con un `Findings:` viejo en una historia sin `main`.

Elegido: devolver False sin rama protegida, como `block()` de `change-size.py` (sin bloque no hay cierre).

## Changed because

Hallazgos de la revisión del primer commit (eff15e5e).
