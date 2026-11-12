<!-- galivelop-workflow v0.5.1 -->
# gw-opt-tokens — notas del proyecto

Las lee la skill `gw-opt-tokens` antes de proponer nada, y se actualizan cuando la persona aprueba un cambio. El flujo
las crea una vez; desde entonces son del proyecto.

## Herramientas que ya ahorran

<!-- Una línea cada una, con cómo se corre. -->
- `python3 .claude/gw/scripts/recover.py --state` y `--search "<texto>"`: recuperar lo que se llevó una
  compactación.
- `gw-orchestrate-dealer`: el trabajo de más de un paso, repartido a subagentes de contexto limpio.
- `docs/agent-map.md`: punto único para los encargos a subagentes.
- `python3 scripts/doctor.py`: en la nube avisa (`compaction`) si falta `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en el entorno.
- `bash tests/check.sh` tarda más de 2 min: se lanza en segundo plano y se espera su aviso (no un bucle con
  `pgrep -f`, que se encuentra a sí mismo).
- `gw-orchestrate-dealer`, regla «A batch of approved rows is dealt»: filas de una propuesta, una por subagente, o
  `/clear` cada 4-5 filas en la principal.
- Bitácora corta (retro 2026-10-25, P1/P2): `handoff.py check --strict` en el check (celdas de estado de 800
  caracteres como mucho, «Hecho» con 5 entradas) y `python3 scripts/handoff.py done "<texto>"` para añadir a «Hecho».
- Encargo de `gw-orchestrate-dealer` con el tope (~30 llamadas, commit y MISSING) y fetch + merge si se rechaza el push
  (P3). Medida de la sesión e9650d36: 4 subagentes por encima de 35 llamadas, ~4,2M de entrada de más. Desde la
  `0.4.1`, el encargo corta a las ~25 llamadas y el tope es ~30 (9 de los 10 subagentes más caros pasaron de 33).
- `gw-harvest` (`0.4.1`): los proyectos se clonan solo para lectura en una carpeta temporal, sin registrarlos
  (`register_repo_root`), y su verificación va con un subagente por proyecto en paralelo.

- `python3 scripts/roadmap.py show <id>` y `done <id> [--note ES --note EN]` (retro `0.5.1` R4, D55): ver o marcar
  una fila del roadmap en los dos idiomas sin leerlo entero ni editarlo con `sed`.
- `gw-orchestrate-dealer` (retro `0.5.1` R3 y R6): los ids del roadmap se commitean antes de repartir; en un
  worktree, solo los tests de lo tocado, y un solo check completo tras fusionar la oleada, sin tocar el árbol.
- `AGENTS.md` (retro del parche 0.4.3): push y check largo en segundo plano, esperando el aviso (R2); al empezar,
  de `traspaso.md` solo lo que el gancho `SessionStart` recortó (R4).

## Costes conocidos

<!-- Lo que se ha visto que cuesta mucho en este proyecto (archivos grandes leídos enteros, salidas largas...). -->
- Sesión abierta fuera del repo: sin `.claude/settings.json` no hay compactación (2026-10-22: contexto medio 321k,
  0 compactaciones). Abrir desde el repo y `/clear` al cerrar cada fase.
- En la nube, la sesión arranca en `/home/user` con varios repos y tampoco carga `.claude/settings.json`: la
  compactación va en las variables del entorno de la nube (retro de la Fase 5, R1).
- Encargos a subagentes que mandan leer muchos documentos: arranque de 52-60k. Apuntar a `docs/agent-map.md`.
- Herramientas que devuelven JSON largo (`list_sessions`, `list_events`): pedir lo mínimo (`limit`, `kinds`).
- Repos hermanos adjuntos a la sesión (recogida del 2026-10-26): sus `CLAUDE.md`, `AGENTS.md` y skills entraban en
  cada llamada, ~19M (17 %). Clonarlos aparte (`gw-harvest`, paso 1).
- Sesión que arrastra repos hermanos de una recogida anterior a la `0.4.1` (medida del 2026-10-27): suelo de 108k,
  ~18-20k por llamada solo de su contexto fijo (16 %) y una compactación cada 24 llamadas. Cada versión nueva, en una
  sesión nueva con solo este repo.
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
- 2026-10-27, parche `0.4.2` (la misma sesión, últimas 24 h): principal 938 llamadas, 123k de media, suelo 108k y
  techo 141k, 39 compactaciones, 115M; subagentes 16 (332 llamadas, 35M). Cambio: la `1.0.0`, en sesión nueva (P1 de
  la retro del 2026-10-27).
- 2026-11-05, parche `0.5.1` (una sesión en la nube, entera): principal 796 llamadas, 125k de media, suelo 93k y
  techo 161k, 12 compactaciones (presupuesto 2), 100M; subagentes 25 (492 llamadas, 45M, arranque 54k; tres por
  encima de 35 llamadas). Arrastre mayor: `docs/handoff.md` 45 lecturas y `docs/roadmap.md` 57 (~1,3M) y
  `get_job_logs` 8 (624k). Cambios: retro `0.5.1` R3 y R6; R4 y R5 (D55, D56) a la `0.6`.
- 2026-11-12, parche `0.5.2` (separación desde la rama de la `0.6`, últimas 10 h): principal 125 llamadas, 122k de
  media, suelo 96k y techo 165k, 2 compactaciones, 15M; un subagente de revisión (30 llamadas, arranque 64k, 2,9M).
  Arrastre mayor: `docs/handoff.md` 14 lecturas (326k) con 27.860 caracteres sobre el tope de 20.000. Cambios: retro
  `0.5.2` R4 (archivar la bitácora tras publicar) a la `0.6`.
