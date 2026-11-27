# 2026-11-27 · gw-worker · pending · E28

## Why

Última ronda en agent/E28-pr-guard (tercera revisión de a320b2bf, sin regresiones). Quedaban 5 hallazgos:
- Un cuerpo `-f`/`-d` buscado en todo `$(…)` bloqueaba `… --jq .sha | tr -d x`.
- `-s=true` y `--clobber=true` dejaban pasar el alias de shell, y `--shell=0` o `false` se tomaba por shell.
- El prefiltro sin python3 no veía `-Kcfg` ni `-sSKv`, y en cambio veía `ssh -K` o `sort -T` en otro comando de la
  tubería.

## Alternatives

- Ninguna: la sesión principal fijó cada arreglo; lo que quede después se documenta como límite.

## Changed because

Las señales de escritura se buscan solo en el comando simple de gh o curl (hasta `|`, `;`, `&&`, `||` o `)`).
Las opciones de `gh alias set` se descartan estén donde estén; `-s`/`--shell` con un valor distinto de 0, f o false
lo hace de shell. En bash, `-K`/`--config` y `-T` se buscan solo en los argumentos del propio curl.
