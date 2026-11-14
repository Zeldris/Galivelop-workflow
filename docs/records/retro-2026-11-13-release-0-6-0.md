# Retro de la versión 0.6.0 (2026-11-13)

Sesión de la `0.6.0`: recogida H19 sobre los seis proyectos de H18, arreglos D90-D93 y B30 en un `gw-worker`, versión
y CHANGELOG, repaso de documentación y revisión de la fase 1 en un subagente limpio (11 hallazgos, arreglados en
`71fe36e`). Incluye la medida de `/gw-opt-tokens`.

**Estado:** decidida por el usuario (2026-11-14): R1, R2 y R4 aprobadas, para aplicar en la `0.6.0` (B33, B34, B35); R3 aplazada: no elegida para la `0.6.0` (sigue como error de proceso en la bitácora).

R5 queda como medida para la próxima versión.

## Medida (`gw-opt-tokens`, sesión entera)

- Sesión principal: 126 llamadas, 2 compactaciones, contexto medio 127.692 (suelo 92k, techo 145k): bajo el umbral de
  150k del dealer.
- Subagentes: la revisión de la fase 1 (Opus, 52 llamadas, 121k de media, 6,3M de entrada) y los arreglos de H19
  (Sonnet, 14 llamadas, 0,4M). La revisión es casi un tercio del gasto total (22,8M).
- Lo que más se arrastra: `docs/roadmap.md`, leído 16 veces (453k arrastrados), casi siempre para listar las filas de
  una versión con `awk`; `docs/handoff.md`, 8 veces (135k).
- Fuera de los tokens: la subida de `2ba6335` tardó 26 min porque el `pre-push` corrió en serie los tests
  relacionados de 172 archivos aunque el check ya estaba en verde en caché sobre ese mismo árbol.

## Propuestas, de más a menos grave

- **R1 (`pre-push`, general).** Con el check completo en verde en caché sobre el mismo árbol, el `pre-push` no
  vuelve a correr los tests relacionados; y, cuando los corre, lo hace con `scripts/test-run.py` en paralelo
  (`testJobs`), no con `unittest` en serie. Ahorro: 26 min de pared por subida grande. Riesgo: ninguno, porque es el
  mismo árbol con los mismos comandos; un test del caso lo cubre.
- **R2 (`version.py`, este repo).** `version.py` (o `apply.py .`) actualiza también `"version"` en
  `.claude/gw.json` al subir de versión. El check completo falló por eso en la `0.6.0` (RepoItself). Riesgo: ninguno.
- **R3 (rama del parche, general; el error de proceso del 2026-11-11).** Los arreglos de la `0.5.2` se hicieron en
  la rama de la `0.6`. Propuesta: aviso en `commit-msg` cuando un commit cierra una fila de parche (la tabla de un
  `X.Y.Z` en el roadmap) en una rama que tiene commits de filas de la menor siguiente, con la orden para crear la rama
  del parche desde `main`. Riesgo: falsos avisos en la rama de la menor tras fusionar un parche (solo aviso, no
  bloquea).
- **R4 (`roadmap.py list`, general; tokens).** `roadmap.py list <versión> [--status pendiente]` da ids y estado de
  las filas de una versión, sin el texto entero. Ahorro estimado: unos 400k por sesión de versión. Riesgo: ninguno;
  `show <id>` sigue dando la fila completa.
- **R5 (revisión de la fase 1, para medir).** La revisión en Opus gastó 6,3M. No se propone bajarla de modelo, porque
  encontró 11 hallazgos reales. Se mide en la próxima versión si dividirla por grupos (código / documentación) reduce
  el contexto medio sin perder hallazgos.
- **Ya cubierto:** el subagente que no esperó a su trabajo de fondo es D92, que ya está en el dealer. Las fechas
  dobles de `handoff.py done` se arreglaron en la fase 1.

## For Galivelop-workflow

Este repo es el flujo: R1, R3 y R4 se aplican aquí mismo si se aprueban.
