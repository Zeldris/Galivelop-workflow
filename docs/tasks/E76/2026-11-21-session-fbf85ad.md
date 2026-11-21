# 2026-11-21 · session · pending · E76

## Why

La revisión de E75-E77 halló que el arranque fijo contaba los mensajes sintéticos como llamadas, que el texto decía
que nada lo reduce (su total sí baja con menos llamadas), que en el log de un subagente daba un motivo falso y que una
copia instalada de `context_guard.py` que falla no dejaba probar la del repo.

## Alternatives

Correr `context_guard.py` en un subproceso para aislar el `SystemExit`: más lento y con otra interfaz; basta con
capturarlo y pasar a la siguiente copia.

## Changed because

—
