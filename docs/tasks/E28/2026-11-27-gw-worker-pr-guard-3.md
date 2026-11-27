# 2026-11-27 · gw-worker · pending · E28

## Why

Tercera ronda en agent/E28-pr-guard: el gw-reviewer encontró 10 huecos en review-before-main.sh (mutaciones GraphQL
mezcladas o que escriben ramas, la API de contenidos, sustituciones con el gh en medio, opciones cortas juntas,
`curl -K`, alias con `pr` o de shell, URLs completas, el respaldo sin python3) y dos falsos positivos (lecturas de la
API dentro de `$(…)` y un backtick escapado en un mensaje de commit), además de la pista de reintento fija en
`gh pr merge`.

## Alternatives

- Seguir exigiendo que el gh/curl abra la sustitución: deja pasar `$(cd x && gh pr merge 7)`. Se descarta.
- Bloquear cualquier llamada a la API dentro de `$(…)`: rompe las lecturas habituales (`--jq .object.sha`). Se
  descarta; dentro de una sustitución la ruta de la API solo cuenta con un método de escritura o un cuerpo.

## Changed because

Se juzga el cuerpo entero de cada sustitución, se separan las opciones cortas juntas antes de leerlas, se normalizan
las URLs completas (también GHE), se miran todas las mutaciones, y la API de contenidos con `branch` protegida (o sin
ella) cuenta como escritura en la rama. Un alias con la palabra `pr`, de shell o con `!` se bloquea; `gh alias set v
'pr view'` también, a propósito.
