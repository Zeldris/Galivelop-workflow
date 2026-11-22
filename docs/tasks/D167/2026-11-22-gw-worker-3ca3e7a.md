# 2026-11-22 · gw-worker · pending · D167

## Why

La copia de `.agents/skills/` está a una carpeta más del proyecto que la de `.claude/skills/`, y `measure.py` y su test solo miraban a tres niveles: sin esquema, `minCalls` daba 0 y los tests fallaban.

## Alternatives

Editar la copia generada a mano (se pierde en el siguiente `apply.py`) o excluir el test con `doctorTestDirsIgnore` (lo oculta, no lo arregla).

## Changed because

—
