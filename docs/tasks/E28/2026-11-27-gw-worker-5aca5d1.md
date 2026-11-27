# 2026-11-27 · gw-worker · pending · E28

## Why

E4 (security-review-E28.md): review-before-main.sh dejaba pasar con 0 un merge, create o retarget hacia la rama
protegida escrito de otra forma: dentro de `$(…)` o comillas invertidas, con `gh alias set`, GraphQL
(`mergePullRequest`), `curl` a la API, `gh pr edit --base`, `gh api` PATCH/POST en `pulls` y escrituras en
`git/refs/heads/<protegida>`. Decisión del usuario (Q-43 a Q-47): se arregla, cada camino con su test.

## Alternatives

- Bloquear toda sustitución con gh/curl: bloquearía `gh pr view "$(…)"` y los mensajes de commit que nombran el
  comando. Se juzga el texto de la sustitución solo cuando su orden es gh/curl, sin comillas simples ni heredocs
  con delimitador entre comillas.
- Resolver los alias de gh ya definidos (`gh alias list`): depende del gh del usuario y no se puede comprobar en
  frío; queda como límite documentado, igual que `gh alias import`, `env -S`, here-strings y `$g`.

## Changed because

GraphQL y escrituras directas en refs no tienen número de PR ni cabeza legibles: se bloquean siempre (con la orden
del camino guardado). El retarget y el create por la API reutilizan las reglas de update_pull_request y
create_pull_request; la rama protegida sale de `protected_tip` (config), nunca de un `main` fijo. De paso, por el
mismo patrón: POST `merges` hacia la protegida y `<(…)`.
