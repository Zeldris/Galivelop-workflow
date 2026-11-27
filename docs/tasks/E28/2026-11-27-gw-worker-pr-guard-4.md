# 2026-11-27 · gw-worker · pending · E28

## Why

Cuarta ronda en agent/E28-pr-guard: la segunda revisión de 9fac54dc encontró dos regresiones (un método entre
comillas simples dentro de una sustitución ya no se leía como escritura; los paréntesis entre comillas cerraban la
sustitución antes de tiempo), un escaneo cuadrático en el número de `$(`, `curl -K` con otra URL, formas de alias
que pasaban (`--shell=true`, `--`, marcadores `$1`), `branch=refs/heads/main` en contents, un falso positivo con
contents leído y el respaldo sin python3 con `-sSK` y `-T`.

## Alternatives

- Seguir añadiendo casos sueltos de método y de comillas. Se descarta por indicación de la sesión principal: ante la
  duda con una ruta de escritura, se falla cerrado.

## Changed because

Un método que no es un GET/HEAD literal (también uno ilegible o en variable) o cualquier cuerpo cuenta como escritura;
las sustituciones se recorren en una sola pasada con pila y comillas por nivel, y solo se juzgan las más externas
(contienen a las internas); cualquier `curl -K/--config` se bloquea; contents solo cuenta si escribe.
