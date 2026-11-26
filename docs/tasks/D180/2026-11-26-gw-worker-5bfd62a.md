# 2026-11-26 · gw-worker · pending · D180

## Why

Con `wholeReadDenyPaths`, un comando que `bash_reads` no sabe partir y un `Read` con `limit` enorme se colaban (E70); el usuario decidió fallar cerrado solo para las rutas denegadas (Q-40, a).

## Alternatives

Dejarlo pasar y documentarlo como límite (Q-40, b), descartada por el usuario. Seguir los `cd` en un comando que no se parte: no se hace, se resuelve contra `cwd` y la raíz.

## Changed because

—
