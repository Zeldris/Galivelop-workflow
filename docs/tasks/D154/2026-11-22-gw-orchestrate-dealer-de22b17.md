# 2026-11-22 · gw-orchestrate-dealer · pending · D154

## Why

El commit-msg rechaza el commit siguiente a un set-row/close-row porque la fila Actualizado queda vieja.

## Alternatives

Hacerlo en el commit-msg o dejarlo a mano: peor, mueve la regla al gancho.

## Changed because

rewrite_row pone la fecha de hoy si la fila existe.
