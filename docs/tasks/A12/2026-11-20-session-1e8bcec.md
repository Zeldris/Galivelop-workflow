# 2026-11-20 · session · pending · A12

## Why

La revisión del trozo 3 halló que Q-16 fallaba tras una compactación, con el config roto, con otro tipo de letra en el
correo y con códigos que no son un idioma.

## Alternatives

Añadir `compact` al matcher de `session-start.sh`: descartado, repetiría todo el gancho; `recover.py --state` ya corre ahí.

## Changed because

`config.agent_language_line()` es la única fuente de la línea; `recover.py` la imprime solo con `--source compact`
para que en `clear` no salga dos veces.
