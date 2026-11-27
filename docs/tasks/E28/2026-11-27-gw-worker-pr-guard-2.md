# 2026-11-27 · gw-worker · pending · E28

## Why

Segunda ronda en agent/E28-pr-guard, a petición de la sesión principal: `gh alias import` y una consulta GraphQL que
el gancho no puede leer (`-F query=@file`, `--input`, `curl -d @file`) quedaban como límite; ahora se bloquean
(fallar cerrado). Y D5, el mismo patrón que questions-guard.py: review-before-main.sh corría el
`<root>/.claude/gw/scripts/is-code.sh` del proyecto antes que su propia copia.

## Alternatives

- Seguir buscando is-code.sh en el proyecto cuando el gancho viene de la caché del plugin: en un repo ajeno eso
  ejecuta cualquier script con ese nombre. Se descarta.

## Changed because

Solo se ejecuta el is-code.sh que está junto al gancho, y solo si el gancho vive dentro de la raíz del proyecto;
si no, la misma regla escrita en Python (`code_files_builtin`: regex de `content`, `reviewMark` y `ciLocalLog`
como contenido, la política del flujo siempre como código, el config del commit de la política). Ya no se bloquea
por faltar `.claude/gw/scripts/is-code.sh`.
