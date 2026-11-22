# 2026-11-22 · gw-implementer · pending · D166

## Why

Dos versiones casi se cerraron con una fila pendiente sin aviso (private-project-5 P1).

## Alternatives

Otra orden (`roadmap.py open`) o parsear en recover.py; se reutiliza `roadmap.py` (`list_rows`/`open_rows`) para no duplicar el análisis.

## Changed because

`recover.py --state` da una línea con las filas abiertas de la rama `version/X.Y[.Z]`; el aviso de `reviewed.sh` queda en E81.
