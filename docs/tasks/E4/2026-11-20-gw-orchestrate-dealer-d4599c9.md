# 2026-11-20 · gw-orchestrate-dealer · pending · E4

## Why

La revisión del trozo 2a halló que `profile.py` cargaba con las capas de quien ejecuta (las órdenes que arreglan un perfil o cargo roto fallaban) y no validaba la cadena de destino al escribir.

## Alternatives

Cargar con un correo vacío (no vale: `config.load` lee el correo de git) o un parámetro de `load`. Se añade `load(profiles=False)` y `apply_profiles(force=True)`, que solo los usa `profile.py`.

## Changed because

—
