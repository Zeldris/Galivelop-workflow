# 2026-11-26 · session · pending · D179

## Why

Arreglos 9, 10, 11 y 16 de la revisión de D179: el pre-push anunciaba `tail -f` de un registro que borra en un
acierto de caché; la línea de actionlint estaba en el grupo de v0.5.1; other-repo-read.py eximía el apply.py de
cualquier repo y todas las palabras tras el intérprete; tres filas del roadmap atribuían mal.

## Alternatives

Para el 11, comprobar solo el nombre del repo en la ruta; se descartó: `config.is_workflow` ya es el criterio común.

## Changed because

—
