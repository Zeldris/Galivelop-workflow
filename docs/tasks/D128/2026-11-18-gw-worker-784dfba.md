# 2026-11-18 · gw-worker · pending · D128

## Why

El /code-review halló que `--update` quitaba cualquier registro de un comando del flujo bajo un matcher que la
plantilla no usa (perdía un `Bash|mcp__shell__run` del proyecto) y que `doctor.py` daba FAIL por «corre dos veces»
también para comandos del proyecto con matchers disjuntos, sugiriendo un `--update` que no los toca.

## Alternatives

Regla más estrecha para el caso original: el matcher viejo (`Read`) tiene sus alternativas dentro de las del de la
plantilla (`^(Read|Bash)$`), así que cabe en la regla de subconjunto y no hizo falta otra. Se descartó avisar solo
sin borrar nunca (dejaría el duplicado de la 0.7.x). En doctor, «comando del flujo» = el que corre desde
`.claude/gw/scripts/`, porque la plantilla no está en el proyecto instalado.

## Changed because

`apply.py` quita la entrada vieja solo si sus alternativas (separadas por `|`, sin `^$()`) son subconjunto de un
matcher de la plantilla para ese comando; si no, la deja y avisa con evento, matcher y cómo quitarla a mano.
`doctor.py` da FAIL solo para comandos del flujo con matchers que se solapan (alternativa común o matcher vacío o
`*`), WARN con la entrada a borrar a mano para los del proyecto, y nada si son disjuntos.
