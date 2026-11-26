# 2026-11-26 · gw-worker · pending · D180

## Why

Un Read con `offset` 1 y sin `limit` lee el fichero desde arriba como si no tuviera offset y rodeaba el rechazo de `wholeReadDenyPaths`; la sesión principal pidió tratarlo como lectura entera sobre una ruta denegada (falla cerrado, Q-40 a).

## Alternatives

Dejarlo como lectura parcial porque Read corta en 2000 líneas: descartada, porque rodea la guarda.

## Changed because

La primera entrada dejaba pasar `offset` 1 sin `limit`; la revisión de la sesión principal lo corrigió.
