# 2026-11-19 · gw-orchestrate-dealer · pending · E65

## Why

El id del commit del ledger sale de `--refs` o del último `Refs:` de HEAD: así pasa `commitRefs` sin una clave nueva de config. Sin id, exit 1 que pide `--refs`.

## Alternatives

Un id fijo o leído de la bitácora: descartado, frágil. Una clave nueva: no hace falta.

## Changed because

Nada cambió.
