# 2026-11-22 · gw-orchestrate-dealer · pending · D157

## Why

next-id proponía ids ya usados en pendingFile (D143).

## Alternatives

Leer solo el plan: es lo que fallaba.

## Changed because

cmd_next_id suma los ids de pendingFile; si no existe, se ignora.
