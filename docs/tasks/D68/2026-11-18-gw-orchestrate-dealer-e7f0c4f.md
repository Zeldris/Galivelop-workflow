# 2026-11-18 · gw-orchestrate-dealer · pending · D68

## Why

El pliegue va en `version.py`: al subir la versión (crea la entrada y pliega) y con `--fold` (sobre la versión de `plugin.json` sin etiqueta); `--release` falla con fragmentos en `HEAD`. Formato del fragmento: solo `### ES` y `### EN`, en ese orden, con texto; todo o nada.

## Alternatives

Plegar en `merge-branch.sh` al fusionar cada rama: haría un commit más por fusión y volvería a tocar `CHANGELOG.md` en la rama de trabajo, que es justo el choque que se quiere quitar entre ramas largas. Un nombre de archivo con `__` en vez de `-` para la `/`: menos legible y sin choques reales en la práctica.

## Changed because

—
