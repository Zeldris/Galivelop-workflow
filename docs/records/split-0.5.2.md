# Separar la `0.5.2` de la rama de la `0.6` (2026-11-11)

Decisión del usuario (2026-11-11): publicar primero la `0.5.2` en `main` y después la `0.6.0`. Los arreglos de la
`0.5.2` se hicieron por error en `ccr-d1e2d496-0vzck8`, mezclados con los evolutivos de la `0.6`; hay que sacarlos a
una rama desde `main` (`eeec886`, `0.5.1`).

## Plan

1. Rama `version/0.5.2` desde `origin/main`. Esta sesión en la nube solo puede subir a `ccr-d1e2d496-0vzck8`:
   probar la subida y, si el proxy da 403, hacerlo en una sesión local o en una sesión en la nube abierta sobre
   `version/0.5.2` (`read_documentation`, tema `github.access`).
2. `git cherry-pick -m 1` de las fusiones marcadas **P** (y `cherry-pick` de los commits sueltos **P**), en orden.
   Las **M** mezclan `0.5.2` y `0.6`: llevar solo su parte de la `0.5.2` a mano. Las fusiones del 2026-11-11 (D70 en
   adelante) se hicieron después de B1-B11, E21, D49… y pueden apoyarse en código de la `0.6`: resolver cada
   conflicto sin traer evolutivos, o devolver la fila a la `0.6` con el usuario.
3. `plugin.json` a `0.5.2`, entrada del CHANGELOG (ES y EN), repaso de `releaseDocs`, recogida que pide
   `version.py --release` (H16 o H18), check completo y fases 1-3; `main`, con confirmación del usuario.
4. Fusionar `main` en `ccr-d1e2d496-0vzck8` y preparar la `0.6.0` (a lo sumo una publicación al día).

## Commits de `origin/main..0219d42` (primer padre)

`P` = solo `0.5.2` · `M` = mezcla · `.` = `0.6` u otra cosa.

```text
. 45b46c2 docs(E28): 0.5.1 en main, release pendiente desde local y revisiones de la 0.9
. d013a07 docs(H14): release v0.5.1 publicada
. 5b937bf docs(H16): recogida de la 0.6, 8 propuestas al usuario
. 134c46b docs(H16): propuestas de la recogida aprobadas, reparto 0.5.2 y 0.7
P 0c4054e chore(B20): fusiona agent/B20-subagent-log
P 3a2e308 docs(D64): fila D64 en la 0.5.2 y B20 hecho
P fb4828f chore(D57): fusiona agent/D57-harvest-renames
P 7ab0cb4 chore(D58): fusiona agent/D58-logrows-off (close-row)
P 33d7c67 docs(D64): fila D64 y B20 hecho también en roadmap.en.md
P 17d40ba chore(D59): fusiona agent/D59-commitnext-agents (D59 y D60)
P 7eabe2d docs(D60): close-row va en el último commit antes del PR; D57, D59 y D60 hechos
P 2568a11 fix(D58): test de close-row con logRows apagado espera el aviso y el 1
P 8f9ec33 chore(D58): fusiona agent/D58-logrows-off (bloques condicionales)
P 19b323d docs(D58): D58 hecho en el roadmap y bitácora al día
P 167ca5e fix(D58): ConditionalBlocks va antes de unittest.main() en test_apply
P bf56b30 docs(B21): apunta B21 y D65 en la 0.6 (contexto de arranque y bitácora)
P 53dd96e docs(B21): B21 y D65 pasan a la 0.5.2 (bucle de compactaciones)
M fd70e87 docs(D66): repaso de docs en cada versión; README al día y A10 en la 0.6
P 3aba517 docs(D66): README al día con la 0.5 (skills, ganchos, scripts)
P 8b7d0e3 feat(D66): clave releaseDocs y comprobación en version.py --release
. 96c8493 docs(H17): notas del usuario y cuatro repos repartidos en propuestas
. 7b3aafa docs(H17): propuestas aprobadas y bloque I de diseño (ciclo de vida y autoridad)
M ff2644d docs(H17): bloque I cerrado con el grilling (ficha, decision log, promoción, citas)
P 4b17f93 fix(D69): tipo hotfix en commitFormat y en version.py
. bd17009 docs(A12): idiomas configurables apuntados en el roadmap
P f19b95b docs(D64): la línea del modelo de gw-selector separa sesión y subagentes
P 94d62f5 feat(B21): guarda del contexto de arranque y del bucle de compactaciones
P dc322c0 feat(D65): historizar la bitácora con tope de tamaño y archivo de versiones publicadas
. 8596ec0 feat(A10): hojas de presentación del flujo para clientes y para equipos
. a57bb8e Merge remote-tracking branch 'origin/agent/A10-mkt-sheet' into ccr-d1e2d496-0vzck8
. f02a5dd WIP: feat(A10): hojas encendidas en marketingSheets, HTML y PDF generados
. 4f0c202 feat(A10): corrige la revisión de mkt-sheet y aplica el estilo del portal a las hojas
. d79209c feat(A10): hojas con el estilo del portal y A10 marcada hecha
. 0e3994d fix(A10): mkt-sheet falla cerrado si falta una fuente de la CSS
. 44c8086 feat(B1): gancho Stop que apunta los tokens de la sesión en el ledger
. b7286b4 feat(B3): tabla de precios con fecha en la config de metrics
. 382832b fix(B3): los tests de precios corren antes de unittest.main()
. c9e7c46 feat(B4): informes de tokens por periodo y skill gw-metrics
. 19af095 feat(B5): metrics.py compare, un periodo junto al anterior o a otro elegido
. df971c0 feat(B6): aviso en el SessionStart cuando un modelo gasta 1,5× su media
. 9050ace feat(B7): models.disabled en gw.json y el gancho que deniega el subagente
. ca2fe8d feat(B8): metrics.py quality, señales de calidad por id junto al gasto
. 6367c48 docs(B8): bitácora bajo el tope de logSize
. 271eca3 feat(B10): el gw-selector recomienda modelo y esfuerzo de la sesión
. 0d1c0dd feat(B11): modelo y esfuerzo por agente, sin variables globales
. b457dc4 WIP: feat(E21): tests-for.py, los tests de un cambio desde testMap
. 354b797 WIP: chore(E21): copia instalada de config.py, esquema y tests-for.py
. 6452be5 WIP: test(E21): nombre de test en inglés para names-check
. 667b99b feat(E21): tests-for.py, los tests de un cambio desde testMap
. acbdf29 feat(B16): reparto por grupo de archivos de los hallazgos de una revisión
. 4259a6a feat(D42): base del worktree, carpeta propia y TaskStop en el reparto
. 5d2305e feat(E22): el check corre los tests del cambio con el Python más viejo
. 8d3d069 fix(E22): test_old_python toma la versión de python3, no la del intérprete
. 5d52246 feat(B18): revisión por bloques en una rama larga
. 894cea5 feat(D48): handoff.py next-id da el siguiente id libre antes de numerar
. 62ecfee feat(D43): aviso de tamaño de commit y de bloque de revisión en el commit-msg
. cb071d6 fix(D43): changeSize en la muestra templates/gw.json
M f00a5e6 fix(D65): arreglos de la revisión del bloque abierto
. 6b3ac44 feat(D49): pre-push de rama solo con tests relacionados
. bf30adf docs(D49): bitácora bajo su tope (archivo de lo publicado)
. ca4498a fix(D49): templates/gw.json muestra branchCheck y fullCheckPaths
. ae42f11 feat(D53): ownedFiles, archivos del flujo que el proyecto hizo suyos
. ea58fd8 docs(D53): bitácora bajo su tope
. 5b93678 WIP: feat(D54): ciOnPush, check.yml solo en los pull request
. a157a4d fix(D54): las plantillas aceptan el marcador calculado ciPushIgnore
. 63c524d fix(D54): test_ci_local rellena el marcador ciPushIgnore de la plantilla
. c832f6d fix(E22): old-python.sh sin «A && B 
. 0080355 feat(B19): gw-update reparte la lectura de diffs y la revisión salta copias
. 773bcb5 feat(E27): shellcheckVersion fija la versión de shellcheck del CI y avisa si la local es otra
. 5f83db6 fix(E27): templates/gw.json no muestra shellcheckVersion; H18, recogida de cierre de la 0.6
. c28212e feat(D55): roadmap.py show/done ve o marca una fila del roadmap en los dos idiomas
. 2a36731 fix(D55): templates/gw.json muestra roadmapFiles
. 295b95f feat(D56): ci-status.py --failed lee el paso en rojo sin el registro entero del job
. b47e94e docs(G11): roadmap, instrucciones renderizadas desde el config
. 03cf8a0 docs(H18): recogida de cierre de la 0.6 sobre los 8 proyectos
. d7dc74e docs(H18): reparto de la recogida de cierre de la 0.6 en el roadmap
. 81e3ba9 fix(D49): arreglos de la revisión del bloque f00a5e6..d7dc74e
. 66e202a fix(D49): los tests relacionados «fast» corren tras un check completo aunque no haya archivos
P 1ee3029 merge(D70): agent/D70-measure
P 7980f71 merge(D72): agent/D72-skills-docs
P 5f2e427 merge(D77): agent/D77-merge-private
P 29521a6 merge(D78): agent/D78-pre-push
P 72b966b merge(D76): agent/D76-check-lock
P e99632f merge(D71): agent/D71-handoff-related
P 3929633 merge(E38): agent/E38-pre-commit-check
P d316210 fix(E40): check-green.sh recorre los logs sin iterar sobre la salida de ls
P 7e4ab01 merge(E39): agent/E38-pre-commit-check (arreglos de la revisión)
P 25a8097 merge(D88): agent/D88-stop-subagents
P 91b4531 fix(D88): la plantilla gw.json muestra stopTranscriptBytes y stopSubagentMaxAge; filas de la 0.5.2 c
P da58aa3 fix(D77): test de merge-branch.sh con check o checkWrapper ilegibles; el encargo de arreglos dice qu
. c1dfddd merge(D85): agent/D85-review-overdue
. c953a3c merge(D86): agent/D86-merge-handoff-conflict
. 75c6c9e merge(B28): agent/B28-gw-worker
. 1fc8bed merge(B26): aviso de lectura entera de bitácora y registros
. 27bb9cf docs(B26): bitácora al día con la primera ola de evolutivos de la 0.6
. 2af0103 merge(D82): review-scope.py deja fuera de la fase 1 las copias del flujo
. 34693e3 docs(D82): fila D82 del roadmap marcada como hecha
. 7e1f080 merge(B29): measure.py mide la sesión anterior de la rama tras un /clear
. 873fd3b docs(B29): fila B29 del roadmap marcada como hecha
. 9dcab7b merge(B27): clave reviewTrivialLines y review-scope.py --trivial
. e034443 docs(B27): fila B27 del roadmap marcada como hecha
. 636a7dd merge(D84): check.yml lee del config las carpetas de Node y Rust y cachea Rust
. d6c0b2d docs(D84): fila D84 del roadmap marcada como hecha
. 92bb1e7 merge(E43): doctor avisa de carpetas de tests que el check no corre
. 8b19893 docs(E43): fila E43 del roadmap marcada como hecha
. 0219d42 docs(E43): cierre de la ola de evolutivos de la 0.6 en la bitácora y el mapa
```
