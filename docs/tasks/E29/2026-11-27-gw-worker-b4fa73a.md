# 2026-11-27 · gw-worker · pending · E29

## Why

Arreglos de la revisión de cfeb5386: el array `pc_cfg` vacío sin guarda abortaba en bash 3.2 con `set -u`, y las
llamadas `--text` no pasaban `--ref`, que otra rama usará para `privateCheck.requireNames`.

## Alternatives

Un test del respaldo E84 con una etiqueta: no es alcanzable, porque con `GW_PUSH_WIP` el paso WIP rechaza las
etiquetas antes de llegar al paso nuevo; el caso de rama ya lo cubre PrePushWip.

## Changed because

—
