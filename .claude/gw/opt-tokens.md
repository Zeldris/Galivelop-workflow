<!-- galivelop-workflow v0.4.1 -->
# opt-tokens — notas del proyecto

Las lee la skill `opt-tokens` antes de proponer nada, y se actualizan cuando la persona aprueba un cambio. El flujo
las crea una vez; desde entonces son del proyecto.

## Herramientas que ya ahorran

<!-- Una línea cada una, con cómo se corre. -->
- `python3 .claude/gw/scripts/recuperar.py --estado` y `--buscar "<texto>"`: recuperar lo que se llevó una
  compactación.
- `orchestrate-dealer`: el trabajo de más de un paso, repartido a subagentes de contexto limpio.
- `docs/mapa-agente.md`: punto único para los encargos a subagentes.
- `python3 scripts/doctor.py`: en la nube avisa (`compaction`) si falta `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en el entorno.
- `bash tests/comprobar.sh` tarda más de 2 min: se lanza en segundo plano y se espera su aviso (no un bucle con
  `pgrep -f`, que se encuentra a sí mismo).
- `orchestrate-dealer`, regla «A batch of approved rows is dealt»: filas de una propuesta, una por subagente, o
  `/clear` cada 4-5 filas en la principal.
- Bitácora corta (retro 2026-10-25, P1/P2): `bitacora.py check --strict` en el check (celdas de estado de 800
  caracteres como mucho, «Hecho» con 5 entradas) y `python3 scripts/bitacora.py done "<texto>"` para añadir a «Hecho».
- Encargo de `orchestrate-dealer` con el tope (~30 llamadas, commit y MISSING) y fetch + merge si se rechaza el push
  (P3). Medida de la sesión e9650d36: 4 subagentes por encima de 35 llamadas, ~4,2M de entrada de más. Desde la
  `0.4.1`, el encargo corta a las ~25 llamadas y el tope es ~30 (9 de los 10 subagentes más caros pasaron de 33).
- `gw-harvest` (`0.4.1`): los proyectos se clonan solo para lectura en una carpeta temporal, sin adjuntarlos a la
  sesión, y su verificación va con un subagente por proyecto en paralelo.

## Costes conocidos

<!-- Lo que se ha visto que cuesta mucho en este proyecto (archivos grandes leídos enteros, salidas largas...). -->
- Sesión abierta fuera del repo: sin `.claude/settings.json` no hay compactación (2026-10-22: contexto medio 321k,
  0 compactaciones). Abrir desde el repo y `/clear` al cerrar cada fase.
- En la nube, la sesión arranca en `/home/user` con varios repos y tampoco carga `.claude/settings.json`: la
  compactación va en las variables del entorno de la nube (retro de la Fase 5, R1).
- Encargos a subagentes que mandan leer muchos documentos: arranque de 52-60k. Apuntar a `docs/mapa-agente.md`.
- Herramientas que devuelven JSON largo (`list_sessions`, `list_events`): pedir lo mínimo (`limit`, `kinds`).
- Repos hermanos adjuntos a la sesión (recogida del 2026-10-26): sus `CLAUDE.md`, `AGENTS.md` y skills entraban en
  cada llamada, ~19M (17 %). Clonarlos aparte (`gw-harvest`, paso 1).
- Comprobar una release: `get_latest_release` o `list_releases` (`perPage` pequeño), no `get_release_by_tag` a
  ciegas con etiquetas que quizá no existen.
- Modelo: el grande se mantiene para ganchos, guardas y seguridad; el medio para guías y porte mecánico (bajar de
  modelo en guardas costaría calidad).

## Ajustes en vigor

- Ventana de compactación automática: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en `.claude/settings.json`.

## Referencias medidas

<!-- Cifras medidas con las que comparar: fecha, sesión, contexto medio, llamadas, total. -->
- 2026-10-22, sesión de creación (fases 0-4): principal 213 llamadas, contexto medio 321k, techo 534k, 0
  compactaciones, 68M de entrada; subagentes 16 (304 llamadas, 35M, arranque medio 52k).
- 2026-10-22, Fase 5 (tres sesiones en la nube): S1 67 llamadas, 110k de media, 1 compactación, 7,4M; S2 157
  llamadas, 191k de media, techo 294k, 0 compactaciones, 30M (18 filas en la principal, 0 subagentes); S3 48
  llamadas, 124k, 6,0M.
- 2026-10-23, Fase 6 (una sesión en la nube, 4 compactaciones): principal 236 llamadas, 106k de media, techo 144k,
  25M; subagentes 20 (457 llamadas, 43M, ~100k de media, arranque 50k). Cambios: tope de ~35 llamadas por subagente
  y «Hecho» de 5 entradas cortas.
- 2026-10-26, parche `0.4.1` (una sesión en la nube, últimas 24 h): principal 369 llamadas, 125k de media, suelo
  108k y techo 142k, 46M; subagentes 30 (616 llamadas, 64M, arranque 69k). Cambios: P1-P4 de arriba.
