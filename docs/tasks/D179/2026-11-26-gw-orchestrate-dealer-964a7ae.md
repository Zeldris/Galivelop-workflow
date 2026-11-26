# 2026-11-26 · gw-orchestrate-dealer · pending · D179

## Why

Hallazgos 4, 5 y 13: la regex de entradas de B52 leía ids en cualquier celda para todo (bitácora, clash, Refs) y
casaba guiones dentro del texto de una celda; doctor ignoraba $GW_TASK_ID y leía planes no .md.

## Alternatives

Una regex aparte para next-id frente a un parámetro `any_cell` de `entry_regex`: se elige el parámetro (un solo
sitio para la forma de la entrada).

## Changed because

—
