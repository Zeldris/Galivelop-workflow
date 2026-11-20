# 2026-11-20 · gw-orchestrate-dealer · pending · E4

## Why

`profile.py` necesitaba editar `.claude/gw.json` en un valor anidado (`profiles.people.<hash>`, `profiles.roles.<rol>`) cambiando solo ese texto, como hace `mode.py`.

## Alternatives

Mover los helpers de `mode.py` a un módulo común (toca más archivos y a sus usuarios) o duplicarlos. Se importan `members`, `lead_of` y `replace` de `mode.py` y `profile.py` añade solo `set_at` para rutas de cualquier profundidad.

## Changed because

—
