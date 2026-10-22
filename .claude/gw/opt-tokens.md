<!-- galivelop-workflow v0.1.0 -->
# opt-tokens — notas del proyecto

Las lee la skill `opt-tokens` antes de proponer nada, y se actualizan cuando el usuario aprueba un cambio. El flujo
las crea una vez; desde entonces son del proyecto.

## Herramientas que ya ahorran

<!-- Una línea cada una, con cómo se corre. -->
- `python3 .claude/gw/scripts/recuperar.py --estado` y `--buscar "<texto>"`: recuperar lo que se llevó una
  compactación.
- `orchestrate-dealer`: el trabajo de más de un paso, repartido a subagentes de contexto limpio.
- `docs/mapa-agente.md`: punto único para los encargos a subagentes.

## Costes conocidos

<!-- Lo que se ha visto que cuesta mucho en este proyecto (archivos grandes leídos enteros, salidas largas...). -->
- Sesión abierta fuera del repo: sin `.claude/settings.json` no hay compactación (2026-10-22: contexto medio 321k,
  0 compactaciones). Abrir desde el repo y `/clear` al cerrar cada fase.
- Encargos a subagentes que mandan leer muchos documentos: arranque de 52-60k. Apuntar a `docs/mapa-agente.md`.
- Herramientas que devuelven JSON largo (`list_sessions`, `list_events`): pedir lo mínimo (`limit`, `kinds`).
- Modelo: el grande se mantiene para ganchos, guardas y seguridad; el medio para guías y porte mecánico (bajar de
  modelo en guardas costaría calidad).

## Ajustes en vigor

- Ventana de compactación automática: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en `.claude/settings.json`.

## Referencias medidas

<!-- Cifras medidas con las que comparar: fecha, sesión, contexto medio, llamadas, total. -->
- 2026-10-22, sesión de creación (fases 0-4): principal 213 llamadas, contexto medio 321k, techo 534k, 0
  compactaciones, 68M de entrada; subagentes 16 (304 llamadas, 35M, arranque medio 52k).
