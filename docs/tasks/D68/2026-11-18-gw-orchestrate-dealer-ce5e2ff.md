# 2026-11-18 · gw-orchestrate-dealer · pending · D68

## Why

Revisión de la rama: `--fold` decidía «no publicada» con `git tag --list`, que en un clon sin etiquetas sale vacío. Ahora `closed_entry()` falla cerrado si no hay ninguna etiqueta `v*` alcanzable (con `git fetch --tags origin`) y la comparten `--fold` y la subida de versión; esta además rechaza siempre una versión que ya tiene etiqueta.

## Alternatives

Exigir etiquetas alcanzables en toda subida de versión: rompería la primera versión de un repo y no protege nada si no hay fragmentos que plegar; se exige solo cuando hay fragmentos.

## Changed because

—
