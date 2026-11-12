# Roadmap

[English](roadmap.en.md)

Qué va en cada versión, con un identificador por tarea. Es la **única fuente de ids** (D13): los commits los citan en
`Refs:` (D12, desde la `0.5`), el CHANGELOG los nombra y `trace.py <id>` (D14) junta todo lo de uno. El diseño de cada
tarea está en [`docs/design/`](design/README.md); el reparto, en [`H-roadmap.md`](design/H-roadmap.md) (mapa nuevo,
aprobado el 2026-11-01). Los evolutivos que trajeron las recogidas siguen en [`pending.md`](records/pending.md),
con su versión en cada línea (H12).

## Identificadores

- Cada tarea lleva la letra de su bloque de diseño y un número sin guion: `B3` es la pregunta 3 de
  [`B-measurement.md`](design/B-measurement.md). Los bloques: A marco, B medición y modelos, C preguntas y modos, D git, E
  calidad, G Management Center (MMC), H roadmap, I ciclo de vida y autoridad ([`I-lifecycle.md`](design/I-lifecycle.md)).
- Una tarea nueva toma el siguiente número libre de su bloque (`handoff.py next-id <letra>`, que mira también las
  demás ramas); un número nunca se reutiliza, ni el de una tarea
  descartada. Las tareas del bloque A que salen de sus apartados y no de una pregunta empiezan en `A7` (sus preguntas
  llegan a `A-6`).
- Las preguntas que solo decidían algo (por ejemplo, D1, D2 o D4) no son tareas y no salen aquí.
- Estados: `hecho`, `en curso`, `pendiente`. Al cerrar una tarea, su fila dice el commit.
- Los ids de los scripts y los ganchos se leen de esta versión en español; [`roadmap.en.md`](roadmap.en.md) la
  traduce.

## Regla de versiones

Solo la última menor publicada recibe parches; los evolutivos van a la siguiente menor (H14, plan §7) que aún no esté en obra: con la `0.6` ya montándose, los de una
recogida van a la `0.7` (usuario, 2026-11-05). Se avanza por
la `0.x`, donde una menor puede romper: **todo lo que rompe va en la `0.5`**, para migrar una sola vez. La `1.0` es
el MMC: cada parche deja configurable lo que toca (umbrales, rutas, comportamientos) para que el MMC lo edite (G4;
usuario, 2026-11-04). A lo sumo una publicación al día (A-6).

## `0.4.4` — parche (no se publica)

El usuario decidió el 2026-11-03 publicar directamente la `0.5.0`: sus arreglos salen en ella y lo pendiente
pasa a la `0.5.1`.

| Id | Tarea | Estado |
|---|---|---|
| D6 | `worktree.baseRef: "head"` en el `settings.json` que instala el flujo | hecho en la `0.5.1` |
| — | Retro `0.4.2` P5: la regla QUOTED del `pre-commit` sin falsos positivos en `.md` ([`pending.md`](records/pending.md)) | pendiente (pasa a la `0.5.1`) |
| — | Arreglos del CI de Ubuntu y macOS (rama `ccr-6dfbc880-ddr41g`, `4b7bf8a`..`66a4ecd`) | hecho |
| D32 | `harvest.py` reconoce las skills con el nombre anterior a A8 y una copia vieja de `writing-for-agents` (image-generator P1, P12) | hecho (`0.5.0`, `c8681f4`) |
| D33 | `config-guard.py`: `settings.local.json`, worktrees y más órdenes que escriben; sin falso positivo en `touch -r` (portal P2, WMF P8) | hecho (`0.5.0`, `cfd8f55`) |
| D34 | `commit-msg` deja pasar un `WIP:` sin `gw.json` legible y no falla fuera de un árbol de trabajo (portal P4, WMF P11) | hecho (`0.5.0`, `df55355`) |
| D35 | `/gw-update` en un clon de una sola rama usa las etiquetas (portal P3) | hecho (`0.5.0`, `ea6195a`) |
| D36 | `reviewed.sh` sugiere `--footer` al fallar y pone `Siguiente:` por defecto con `commitNext` (WMF P2) | hecho (`0.5.0`, `b0b7fbf`) |
| E18 | Tests de las skills instaladas aislados del proyecto donde corren (WMF P3) | hecho (`0.5.0`, `fd6b6cc`) |
| D37 | `pre-commit`: `KEY_FORMATS` con claves pegadas a una letra o dígito; sin falso positivo en diccionarios de tests (image-generator P2, P3) | hecho (`0.5.0`, `c57d5b4`) |
| D38 | La marca de subida en curso del `pre-push`, una por worktree (portal P5) | hecho (`0.5.0`, `eccbad8`) |
| D39 | `subagent-cap.py`: contador que se limpia y sin enlaces simbólicos (portal P7, WMF P9) | hecho (`0.5.0`, `bdaef9d`) |

## `0.5` «Base» — lo que rompe

En este orden, porque cada paso usa el anterior.

| Id | Tarea | Estado |
|---|---|---|
| H14 | Regla de versiones nueva en `AGENTS.md` y el plan §7 | hecho (`a1ac1e3`) |
| D13 | Este roadmap, con los ids, en español e inglés | hecho |
| H12 | `pendiente-1.0.0.md` → `pending.md`, con la versión en cada línea | hecho |
| H15 | Recogida de la `0.5` (`gw-harvest`) y sus propuestas, al usuario | hecho (D32-D40, E18, E19, B14, B15) |
| A7 | Plan reescrito según la tabla de A1 (§1, §2, §7, §9, §10): repo público, cada versión se publica aquí | hecho |
| A8 | Nombres (A2, A-3, A-4): `gw-` en las skills propias, scripts en inglés, rutas del proyecto en inglés y configurables en `gw.json`; `gw-update` renombra y los ganchos aceptan los dos nombres durante la `0.x` | hecho |
| A9 | `schemaVersion` en `gw.json` y su migración en `gw-update` (A3.2) | hecho |
| D11 | Conventional Commits en la primera línea (`fix(B1): …`); `version.py` sugiere el salto | hecho |
| D12 | Trailer `Refs: <id>` obligatorio en `commit-msg` (salvo merges), validado contra este archivo | hecho |
| D15 | Trailer `Agent:` opcional, sin nombre de modelo | hecho |
| D16 | Ramas de subagente `agent/<id>-…`; `merge-branch.sh` copia `Refs:` | hecho |
| E2 | Check de datos privados en el `pre-push` (lista en `.claude/gw.local.json`); el CI, solo claves y correos | hecho (`8ffc4f5`) |
| E3 | Recogidas publicadas anonimizadas (`private-project-1`) | hecho (`d11153f`) |
| D3 | Repaso de las recogidas ya publicadas con el check de E2 | hecho (`0cb929b`) |
| E1 | Auditoría de `AGENTS.md` y `CLAUDE.md`, con check de tope de líneas | hecho (`d0dfed3`, `e02859e`) |
| E6 | Cada regla de `REVIEW.md` nombra su check o dice «criterio» | hecho |
| D18 | `scripts/ci-status.py`: estado de Actions de una rama o commit (private-project-2 P6) | hecho (`32e7f8f`) |
| D19 | Clave `ciPython`: versiones de Python de la matriz de la plantilla del CI (private-project-2 P7) | hecho (`364966d`) |
| D20 | Clave `ciIgnore`: estados de CI ajenos que no bloquean la fusión (private-project-1 P1) | hecho (`b2dd04c`) |
| D21 | Sin firmas del agente en PR, issues y comentarios; aviso de un `user.email` `noreply@anthropic.com` (private-project-1 P2) | hecho (`84580cc`) |
| E17 | El check en una orden con resumen y la salida recortada (INS P12, WMF P4) | hecho (`bb1f47a`) |
| D22 | `handoff.py own-row --staged`: la propia fila comprobada al hacer el commit (INS P9) | hecho (`08bc6b6`) |
| D23 | `handoff.py set-row` (private-project-1 P7) | hecho (`0403f2b`) |
| D24 | `reviewed.sh` avisa del código sin revisar desde la última marca (private-project-1 P6) | hecho (`e93a941`) |
| D25 | `red-without-fix.sh --fix-at <commit>`; rojo de compilación frente a rojo de aserción (private-project-1 P5) | hecho (`4c6527f`) |
| D26 | `doctor.py` avisa de worktrees ya fusionados (INS P10) | hecho (`e3a7789`) |
| D27 | `doctor.py` avisa de `cd <carpeta> && …` sin `worktreeLinks` (private-project-1 P8) | hecho (`b8926e7`) |
| D28 | `doctor.py` avisa de un `core.hooksPath` absoluto al `.githooks` del checkout principal (retro `0.4.2` P3) | hecho (`204c735`) |
| D29 | `related-tests.sh` con archivos borrados (private-project-1 P11) | hecho (`a4798a0`) |
| D30 | `version.py`: existe cada ruta citada en la entrada nueva del CHANGELOG (retro `0.4.3` R1) | hecho (`785062f`) |
| D31 | `commit-msg` exige `Siguiente:`, también en las fusiones de `merge-branch.sh`; escape `GW_NO_NEXT=1` (retro `0.4.2` P4) | hecho (`7561ebf`) |
| B14 | `recover.py --state` avisa del presupuesto de compactaciones superado (private-project-1 P1) | hecho (`0.5.0`, `e1f312f`) |
| D40 | Aviso de ramas remotas con trabajo fuera de la protegida (WMF P1, private-project-1 P4) | hecho (`0.5.0`, `e1f312f`) |
| B15 | Aviso de un subagente lanzado sin `model` (portal P1) | hecho (`0.5.0`, `bdaef9d`) |
| E19 | El check falla con una `TestCase` después de `unittest.main()` (private-project-1 P2) | hecho (`0.5.0`, `a4ab81c`) |
| — | Lo de [`pending.md`](records/pending.md) marcado `0.5` | repartido en D18-D31 y E17 |

## `0.5.1` — parche

| Id | Tarea | Estado |
|---|---|---|
| D6 | `worktree.baseRef: "head"` en el `settings.json` que instala el flujo (de la `0.4.4`) | hecho |
| E25 | Retro `0.4.2` P5: la regla QUOTED del `pre-commit` sin falsos positivos en `.md` (de la `0.4.4`) | hecho |
| E20 | `check.sh`: registro fijo `.git/gw/check-<sha>.log`, cerrojo con pid y línea final con las secciones que fallaron; `merge-branch.sh` lo usa y apunta el verde (retro `0.5.0` R1) | hecho |
| D44 | Marcar como revisado no cuesta otro check: el `pre-push` da por verde un commit que solo añade la marca de revisión a uno ya en verde, o rama y `main` se suben en un solo `git push` (usuario, 2026-11-04: la subida de la `0.5.0` corrió tres checks casi iguales) | hecho |
| D41 | El gancho `Stop` avisa en una línea, sin pedir subir, mientras corre un check o un push (retro `0.5.0` R5; depende de E20) | hecho |
| D45 | `apply.py --update` no borra los pasos propios del CI del proyecto: por qué el `.gw-new` no salvó el `check.yml` del portal al pasar a la `0.5.0`, con su test (recogida `0.5.1`, portal P2) | hecho |
| B17 | `gw-orchestrate-dealer`: un subagente que escribe en segundo plano trabaja siempre en un worktree, aunque sea uno solo (recogida `0.5.1`, image-generator P1) | hecho |
| E23 | La caché del check se invalida al cambiar un archivo ignorado que el check lee (`.claude/gw.local.json`), o el verde reutilizado lo avisa (recogida `0.5.1`, portal P3) | hecho |
| D46 | Tras migrar nombres (A8), `apply.py --update` o `doctor.py` listan los usos de rutas viejas en los archivos propios del proyecto (recogida `0.5.1`, portal P1) | hecho |
| D47 | El `pre-push` que para datos privados dice que los commits aún no están subidos y propone `--amend` o `rebase -i` solo sobre ellos (recogida `0.5.1`, portal P4) | hecho |
| E24 | Lo probado con un doble lleva una prueba de humo con lo real: nota en `patterns.md` y regla `(criterio)` en `REVIEW.md` (recogida `0.5.1`, world-maker-fantasy P3) | hecho |
| D51 | `apply.py --update` no siembra la plantilla de la bitácora en el destino de una carpeta que mueve (con `log` dentro de ella, se perdía la bitácora al pasar a la `0.5`), con su test (recogida de cierre `0.5.1`, world-maker-fantasy P1) | hecho |
| D52 | `apply.py` decide si conserva un script viejo por su ruta entera (`.claude/gw/scripts/<nombre>`), no por un nombre igual en otra ruta, con su test (recogida de cierre `0.5.1`, world-maker-fantasy P2) | hecho |
| E26 | `red-without-fix.sh` no busca código de test en textos y datos (`.md`, `.json`, `.yml`, `.properties`, `.txt`, `.csv`): la prosa casaba con `it(`, con su test (recogida de cierre `0.5.1`, private-project-1 P1) | hecho |

## `0.5.2` — parche

| Id | Tarea | Estado |
|---|---|---|
| B20 | `measure.py` mide el registro de un subagente (`subagents/agent-*.jsonl`, todas sus líneas con `isSidechain`), con su test (recogida `0.6`, image-generator P1) | hecho |
| D57 | `harvest.py` sigue los renombrados (`-M`) y no repite las ideas de un archivo movido; una idea recortada dice «… (truncated)» (recogida `0.6`, image-generator P2) | hecho |
| D58 | La plantilla de la bitácora solo explica `logRows` si está encendido; `handoff.py close-row` avisa y sale con 1 si está apagado, como `set-row` (recogida `0.6`, image-generator P3) | hecho |
| D59 | `commitNext: true` por defecto en `templates/gw.json`, como pide la plantilla de `AGENTS.md` (recogida `0.6`, image-generator P4) | hecho |
| D60 | Las plantillas de `AGENTS.md` nombran `handoff.py set-row` y `close-row` para la fila propia de la bitácora (recogida `0.6`, private-project-1 P2) | hecho |
| D64 | `gw-selector`: la línea del modelo separa sesión y subagentes y da el actual (`Sesión: <recomendado> (actual: <X>; /model para cambiarlo) · Subagentes: <peldaño> · Skill: <y>`); si la sesión orquesta con `gw-orchestrate-dealer`, su modelo es el de la fila de más riesgo que reparte, como mínimo medio (usuario, 2026-11-05) | hecho |
| B21 | Guarda del contexto de arranque y del bucle de compactaciones: tras un `/clear` o una compactación, `measure.py` lee del registro el uso del primer turno (`input` + `cache_read` + `cache_creation`) y lo compara con el **punto de corte de la compactación** (clave en `.claude/gw.json`; por defecto, el del modelo), no con la ventana. El `SessionStart` avisa por encima del 25 % y da la alarma por encima del 50 % (claves); si tras una compactación el arranque vuelve a pasar el umbral, es un bucle: alarma y para, con el «Presupuesto de compactaciones». El aviso nombra al culpable con un desglose determinista (bitácora, `AGENTS.md`/`CLAUDE.md`, salida de los ganchos, skills y herramientas, resto del sistema) y la orden que lo arregla. Caso real: un proyecto con corte a 140k entró en bucle porque releer el contexto ocupaba el 70 %; aquí, ~82k de 200k tras `/clear` con la bitácora en ~9k (usuario, 2026-11-05) | hecho |
| D65 | Historizar la bitácora: tope de tamaño total de `docs/handoff.md` (clave en `.claude/gw.json`) que `handoff.py check` avisa y que B21 usa como culpable; `handoff.py archive` mueve los «Pendiente» y leves de versiones ya publicadas a `docs/records/handoff-archive.md` (que no se lee al empezar), dejando una línea con el enlace; tras compactar, `recover.py` y el `SessionStart` releen solo el estado y el siguiente paso (usuario, 2026-11-05) | hecho |
| D69 | Tipo `hotfix` en `commitFormat` y en `version.py` (cuenta como parche), con su test, para que los proyectos en `0.5` acepten el tipo antes de la ficha de tarea (C11) ([`I-lifecycle.md`](design/I-lifecycle.md) Q11; usuario, 2026-11-08) | hecho |
| D66 | Cada versión repasa la documentación para personas (`README.md` ↔ `README.es.md`, `docs/es/` ↔ `docs/en/`, roadmap) contra su CHANGELOG antes de la subida a `main` (`AGENTS.md`); `version.py --release` falla si un archivo de `releaseDocs` (clave en `.claude/gw.json`; por defecto `[]`, aquí los dos README) no nombra la versión que se publica. Caso real: la `0.5.1` salió con el README en «Estado: `0.4.3`» (usuario, 2026-11-06) | hecho |
| D70 | `measure.py --since` elige la sesión correcta, no la del registro más nuevo (recogida de cierre `0.6`, private-project-1 P2) | hecho (2026-11-11) |
| D71 | `handoff.py close-row` y `set-row` toman la rama del mismo modo (recogida de cierre `0.6`, private-project-1 P3) | hecho (2026-11-11) |
| D72 | El encargo de `gw-orchestrate-dealer` dice quién sube (en la rama de trabajo, el subagente; en un worktree, no) y qué hace con su commit (sin commitear, o con su fila de la bitácora en el mismo commit); la principal mira `git status -sb` al volver (recogida de cierre `0.6`, image-generator P2, world-maker P1) | hecho (2026-11-11) |
| D73 | `gw-update` termina abriendo el PR de la rama de actualización a la protegida (recogida de cierre `0.6`, instalador P1) | hecho (2026-11-11) |
| D74 | `related-tests.sh` dice cuántos archivos y la ruta de un temporal con la orden, no la lista entera (recogida de cierre `0.6`, world-maker P2) | hecho (2026-11-11) |
| D75 | Paso de cierre de una ronda de pruebas: llamar al script del proyecto que para lo levantado (servidores, modelos, inhibidores de suspensión) (recogida de cierre `0.6`, world-maker P7) | hecho (2026-11-11) |
| D88 | El gancho `Stop` no pide subir mientras hay subagentes en segundo plano (amplía D41); primero se comprueba aquí cómo lo detecta world-maker (recogida de cierre `0.6`, world-maker P4) | hecho (2026-11-11) |
| B22 | `measure.py` muestra el `action` de las llamadas a Artifact en HEAVIEST RESULTS (recogida de cierre `0.6`, portal P4) | hecho (2026-11-11) |
| B23 | `prototype` publica el Artifact (con su `quickstart`) desde un subagente que devuelve solo la URL (recogida de cierre `0.6`, portal P3) | hecho (2026-11-11) |
| B24 | La revisión de la fase 1 empieza tras `/clear` o en un subagente limpio (`AGENTS.md`, `gw-selector`) (recogida de cierre `0.6`, portal P2) | hecho (2026-11-11) |
| B25 | `gw-scout-updates` con 2 subagentes (recogida de cierre `0.6`, private-project-1 P4) | hecho (2026-11-11) |
| D76 | Candado de `check-green.sh`: el mismo pid actualiza sha y registro, un `check.lock.steal` sin pid no bloquea, un proceso de otro usuario se trata igual que en `before-stop.py`; `before-stop.py` compara el sha completo de `check.sh` con HEAD (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgos 1-4) | hecho (2026-11-11) |
| D77 | `merge-branch.sh` valida `check` y `checkWrapper` antes de fusionar (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgo 5) | hecho (2026-11-11) |
| D78 | `pre-push`: vuelve a mirar la caché de verdes tras esperar el candado; con el mismo árbol en una ref protegida y en una rama, la rama también se comprueba; `lock_wait` local (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgos 6-8) | hecho (2026-11-11) |
| D79 | `private-check.py amend_advice`: sin `rebase -i` sobre una etiqueta o `HEAD`, sin `git add -A` y sin el `cfg` que no usa (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgos 11 y 14) | hecho (2026-11-11) |
| E38 | `pre-commit`: `PROSE_ASSIGN` no deja pasar un secreto de una palabra en mayúscula entre comillas en un `.md`; `md_prose_dropped` sin un proceso por línea (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgos 12-13) | hecho (2026-11-11) |
| E39 | `check.sh` sin `--quiet` conserva TTY y colores (regresión de E17; se reproduce con un test antes) (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgo 10) | hecho (2026-11-11) |
| E40 | Poda de los `check-<sha>.log` de `.git/gw`: se guardan los últimos `checkLogKeep` (20) (recogida de cierre `0.6`, revisión `0.5.1` del instalador, hallazgo 9) | hecho (2026-11-11) |

## `0.6` «Medir»

| Id | Tarea | Estado |
|---|---|---|
| H16 | Recogida de la `0.6` (`gw-harvest`) y sus propuestas, al usuario | hecho (B20, D57-D60 a la `0.5.2`; D61-D63 a la `0.7`) |
| H17 | Notas del usuario (SDD, DDD, TDD, exploración, ficha de tarea, hecho por entorno) y cuatro referencias externas, repartidas en propuestas: [`2026-11-08-notes-and-references.md`](proposals/2026-11-08-notes-and-references.md); aprobadas las 13 y las 5 preguntas (usuario, 2026-11-08); el diseño que las une, [`I-lifecycle.md`](design/I-lifecycle.md), cerrado con su `grilling` (12 respuestas, 2026-11-08) | hecho |
| H18 | Recogida de cierre de la `0.6` (`gw-harvest`) antes de publicarla: los arreglos, al siguiente parche de la `0.5`; los evolutivos, repartidos entre las versiones (usuario, 2026-11-11) | hecho (2026-11-11; 28 propuestas y 14 hallazgos de la revisión `0.5.1` del instalador: D70-D79, D88, B22-B25 y E38-E40 a la `0.5.2`; B26-B29, D82, D84-D86 y E43 a la `0.6`; D80, D81, D83, D87 y E41 a la `0.7`; E42 a la `0.8`; portal P6 descartada) |
| A10 | Hojas de presentación del flujo, de una página A4: para quien contrata desarrollo, `docs/es/mkt-workflow.md` ↔ `docs/en/mkt-workflow.md` (qué resuelve, cómo se trabaja, qué garantiza), y para equipos que lo instalan, `docs/es/mkt-adoption.md` ↔ `docs/en/mkt-adoption.md` (usuario, 2026-11-09), con su HTML y su PDF final generados desde el `.md` por un script, para que no se desfasen; se repasa en cada versión (D66) (usuario, 2026-11-06) | hecho (`scripts/mkt-sheet.py`, estilo del portal) |
| B1 | Gancho `Stop` que lee los logs de sesión | hecho (`scripts/metrics.py record`, clave `metrics`) |
| B2 | `docs/metrics/ledger.jsonl` en el repo | hecho (`merge=union` en `.gitattributes`; falta que `apply.py` lo ponga en los proyectos) |
| B3 | Qué se guarda: tokens por modelo y tipo, fecha, rama, `Refs`, subagente; precios en tabla con fecha | hecha (2026-11-09; campos con B1, `metrics.prices` y `metrics.py price`) |
| B4 | Informes por periodo: `metrics.py report --period …` y skill `gw-metrics` | hecho (2026-11-09; `metrics.reports`, `--write`) |
| B5 | Comparaciones: `metrics.py compare` | hecho (2026-11-09; anterior o `--against`) |
| B6 | Aviso en el `SessionStart` cuando un modelo gasta 1,5× su media | hecho (2026-11-09; `metrics.alert`, hoy y ayer) |
| B7 | `models.disabled` en `gw.json`, con su gancho | hecho (2026-11-09; `subagent-cap.py` deniega, `models.py`) |
| B8 | Señales de calidad junto al gasto (la tabla determinista, en «Después») | hecho (2026-11-09; `metrics.py quality`, trailers `Findings`/`Retries`, `metrics.quality`) |
| B10 | El `gw-selector` recomienda modelo y esfuerzo de la sesión principal | hecho (2026-11-09; columna de esfuerzo, línea `Session: <modelo> <esfuerzo> (current: …)` y `sessionEffort` en `selector.cases`) |
| B11 | Modelo y esfuerzo por agente (palancas de Claude Code) | hecho (2026-11-09; `models.agentFields` en `subagent-cap.py`, `models.checkLevers` en `doctor.py`, regla en `gw-selector` y `gw-orchestrate-dealer`) |
| E21 | `scripts/tests-for.py <archivos>` (clave `testMap`; no `related-tests.py`: chocaba con `related-tests.sh` y su test): los tests de un cambio, citado en el encargo de `gw-orchestrate-dealer`; en `REVIEW.md`, un script que hace commits se prueba con los ganchos instalados (retro `0.5.0` R2) | hecha (2026-11-09) |
| B16 | `gw-orchestrate-dealer`: los hallazgos aprobados de un `/code-review` se reparten a subagentes por grupo de archivos (retro `0.5.0` R3) | hecha (2026-11-10; regla «Approved review findings are dealt by group of files») |
| D42 | `gw-orchestrate-dealer`: carpeta `scratchpad/<id>/` por agente, comprobar la base del worktree y cortar con `TaskStop` (retro `0.5.0` R4) | hecha (2026-11-10; carpeta `{scratch}/<id>-<topic>/`, como la rama; `{head}` en el encargo) |
| E22 | `tests/check.sh` corre también, con el Python más viejo disponible (3.8+, más viejo que `python3`), la compilación de todo y los tests del cambio (`tests/old-python.sh` con `tests-for.py`; las suites de ganchos, solo si cambiaron), o avisa si no hay (retro `0.5.0` R6) | hecha (2026-11-10) |
| B18 | Revisión por bloques en una rama larga: `/code-review` del diff nuevo en cada bloque cerrado, en `gw-selector` y la plantilla de `AGENTS.md` (recogida `0.5.1`, world-maker-fantasy P1) | hecha (2026-11-10; fila «Closing a block or phase» y fase 1 de las plantillas y de `AGENTS.md`) |
| D48 | `handoff.py next-id <prefijo>`: el siguiente id libre mirando las ramas remotas antes de numerar, con `free_id` (recogida `0.5.1`, world-maker-fantasy P2) | hecha (2026-11-10; mira copia, índice y todas las ramas locales y remotas; `--fetch`; `clash` ya sugiere bien los ids sin guion) |
| D43 | Tamaño de commit y de revisión: avisar, sin bloquear, de un commit de más de ~400 líneas cambiadas (LOC); la unidad de revisión es el bloque o tarea de ~1000 líneas, revisado al cerrarse (B18), y el PR a `main` suma bloques ya revisados. No cuentan los documentos emparejados, las copias instaladas de `.claude/gw/` ni lo generado; los umbrales, en `.claude/gw.json` (usuario, 2026-11-04) | hecha (2026-11-10; `change-size.py` desde el `commit-msg`, clave `changeSize`; el bloque empieza tras el último commit con `Findings:`) |
| D49 | El `pre-push` de una rama que no es `main` exige solo los tests relacionados (`related-tests.sh`); el check completo pasa a la subida a `main` y a los cambios de entorno. El CI de GitHub sigue completo en cada push, sin bloquear, y se mira al cerrar cada bloque con `ci-status.py`; absorbe parte de D44 (usuario, 2026-11-04) | hecha (2026-11-10; claves `branchCheck` y `fullCheckPaths`, `config.py push-scope`; sin `relatedTests`, el completo) |
| D50 | Commits con traza: los `feat`/`fix` (y un `refactor` grande) llevan en el cuerpo `Técnica:` (la decisión y lo descartado) y `Problemas:` (qué falló y cómo se resolvió, o «ninguno»). El `commit-msg` comprueba que estén, con los tipos en `.claude/gw.json`; `REVIEW.md` pide su calidad como regla de criterio y la retro la repasa. Quedan fuera `docs`, `WIP` y la marca de revisión (usuario, 2026-11-04). **Absorbida por C11** (usuario, 2026-11-08): el razonamiento va a la ficha y el commit solo resume | absorbida por C11 |
| D53 | `ownedFiles` en `.claude/gw.json`: archivos del flujo que el proyecto hizo suyos; `apply.py --check` no los da por desviados y `doctor.py` no recomienda `/gw-update` por ellos (recogida de cierre `0.5.1`, world-maker-fantasy P3) | hecha (2026-11-10; patrones `fnmatch`, `config.owned`; aviso si queda un `.gw-new`) |
| D54 | `ciOnPush` en `.claude/gw.json`: `check.yml` corre en cada push o solo en los PR, sin editarlo (recogida de cierre `0.5.1`, world-maker-fantasy P4) | hecha (2026-11-10; `branches-ignore: ['**']` al aplicar; pista en `ci-status.py`) |
| B19 | `gw-update` reparte la reconciliación de cada `.gw-new` a un subagente que devuelve la tabla de desvíos; el `/code-review` de la rama de actualización deja fuera las copias idénticas del flujo (recogida de cierre `0.5.1`, world-maker-fantasy P5) | hecha (2026-11-10; pasos 3-5 de la skill: tabla «desvío · arriba · decisión» por subagente ligero y `/code-review` sin las copias idénticas) |
| E27 | `shellcheckVersion` en `.claude/gw.json`: el CI instala esa versión y `tests/shellcheck.sh` avisa, con la orden para instalarla, si la local es otra (retro `0.5.1` R1) | hecha (2026-11-11; el CI la instala con `pip install shellcheck-py==X.Y.Z.*`; en el CI una versión distinta falla) |
| D55 | `roadmap.py show <id>` y `roadmap.py done <id>`: ver o marcar una fila del roadmap en los dos idiomas sin leerlo entero (retro `0.5.1` R4) | hecho (2026-11-11; `scripts/roadmap.py`, clave `roadmapFiles` (la `roadmap` reservada sigue siendo booleana); marca los dos idiomas o ninguno) |
| D56 | `ci-status.py --failed`: de cada job en rojo, solo el paso que falló y sus líneas de error, con tope en una clave y la URL del registro entero (retro `0.5.1` R5) | hecho (2026-11-11; `--failed`: el paso de la API de jobs y, del registro, de su cabecera `Run …` a su última línea `##[error]`, sin la orden plegada; tope `ciFailedLines` (40) o `--lines`) |
| B26 | Aviso al leer entera la bitácora o un registro de más de `wholeReadWarnBytes` (20000) (recogida de cierre `0.6`, private-project-1 P1) | hecho (2026-11-11) |
| B27 | Diffs triviales revisados sin subagente; los arreglos de la fase 1, a `sonnet` (recogida de cierre `0.6`, private-project-1 P7) | hecho (2026-11-11) |
| B28 | Tipo de subagente ligero (`gw-worker`, en `.claude/agents/`) con solo las herramientas del encargo; lo crea `gw-init` y lo nombra el encargo del dealer (recogida de cierre `0.6`, private-project-3 P1) | hecho (2026-11-11) |
| B29 | `measure.py` mide la sesión anterior de la misma rama si la actual tiene menos de `measure.minCalls` (5) llamadas (tras un `/clear`) (recogida de cierre `0.6`, world-maker P5) | hecho (2026-11-11) |
| D82 | Lo copiado tal cual del flujo (`vendored`) queda fuera del `/code-review` de la fase 1 (vecino de D53 y B19) (recogida de cierre `0.6`, instalador P2) | hecho (2026-11-11) |
| D84 | `templates/github/check.yml` lee de `.claude/gw.json` los directorios de Node y Rust y usa `Swatinem/rust-cache` (recogida de cierre `0.6`, instalador P5) | hecho (2026-11-11) |
| D85 | `recover.py --state` avisa de una revisión atrasada (umbral `changeSize.block`) (recogida de cierre `0.6`, world-maker P3) | hecho (2026-11-11) |
| D86 | `merge-branch.sh` reconoce el conflicto en la bitácora y da la orden para resolverlo, con su test (recogida de cierre `0.6`, portal P5) | hecho (2026-11-11) |
| E43 | `doctor.py` avisa de carpetas con `test_*.py` que ningún comando del check corre; carpetas excluidas configurables (recogida de cierre `0.6`, instalador P3) | hecho (2026-11-11) |
| E44 | El check corre `version.py --release` también en las ramas `version/*` (clave `releaseCheckBranches`), no solo en el `pre-push` a `main` (retro `0.5.2` R2) | pendiente |
| D81 | `scripts/backport.sh <sha>...`: cherry-pick en orden topológico (`-m 1 -x`), bitácora y roadmap con la versión del parche, vacíos saltados, para en un conflicto de código y comprueba con `git cherry`; trae también los archivos de recogida de la rama; en la guía de parches y `docs/agent-map.md` (recogida de cierre `0.6`, image-generator P1; retro `0.5.2` R3) | pendiente |
| D89 | `handoff.py`: `published_version` usa la etiqueta más alta también cuando hay `plugin.json` en el repo del flujo, para que `archive` no se adelante a una versión sin publicar (retro `0.5.2` R4) | pendiente |
| E45 | Check rápido: `scripts/test-run.py` corre la suite de Python en paralelo, una clase de test por proceso, las más lentas primero, entre `testJobs` procesos (por defecto, uno por núcleo) y la pasada E22 va a la vez que la principal; mismos tests en local y en el CI; objetivo, el check completo en 10-15 min (usuario, 2026-11-12: tardaba 50-80 min) | hecho (2026-11-12) |
| E46 | Los archivos de test más caros según `test-run.py --times` montan sus repos de prueba una vez por clase, con estado limpio en cada test (sigue a E45): `Snapshot` de `tests/test_hooks.py` (`build()` una vez, copia de la carpeta en la misma ruta por test) en las tres `Base`, `Hook` y `Doctor`; la suite, de 556 s a 352 s con 4 núcleos | hecho (2026-11-12) |
| E47 | El `pre-push` pide el check completo solo por las claves de `.claude/gw.json` que cambian lo que corre el check; las demás, con los tests del cambio (sigue a E45): `config.py push-scope --commits` compara las claves de cada commit nuevo con sus padres y solo cuentan las que no están en `fullCheckSkipKeys` (nueva; por defecto, las que no lee ningún script del check); un config roto o ausente a cualquier lado, completo | hecho (2026-11-12) |
| A13 | Repaso de todo lo hecho hasta la `0.6` para que `.claude/gw.json` esté lo más completo posible: cada umbral, ruta, aviso o comportamiento que aún va fijo en el código pasa a ser una clave activable o configurable, con su valor por defecto, su entrada en `config.py`, el esquema y `docs/es/config.md` (regla «Todo configurable»; usuario, 2026-11-12) | pendiente |

## `0.7` «Preguntar»

| Id | Tarea | Estado |
|---|---|---|
| C1 | `docs/questions.md`, una entrada por pregunta | pendiente |
| C2 | Lista numerada con recomendación; respuestas por número, que un script pasa al archivo | pendiente |
| C3 | Sin repetir preguntas ya respondidas | pendiente |
| C4 | Modo restrictivo activo, con su gancho | pendiente |
| C5 | Modo restrictivo inactivo: aviso y «riesgo aceptado» | pendiente |
| C6 | Valor por defecto: inactivo en los proyectos, activo en este repo | pendiente |
| C7 | Un solo interruptor: skill `gw-mode` | pendiente |
| C8 | `modes.careful` (antes de una orden destructiva), activo por defecto | pendiente |
| C10 | Un subagente no pregunta al usuario: devuelve la pregunta | pendiente |
| D14 | `trace.py <id>` | pendiente |
| D61 | `handoff.py preflight`: lo que el `pre-push` comprueba en la bitácora (fecha de «Actualizado», ids que chocan con `main`), sin subir; en el `check` de la plantilla (recogida `0.6`, private-project-1 P1) | pendiente |
| D62 | El `pre-push` avisa, sin bloquear, si el último CI de la rama está en rojo (`ci-status.py`, si hay `gh`) (recogida `0.6`, image-generator P5) | pendiente |
| D63 | `templates/github/check.yml` con `workflow_call`: un `release.yml` lo llama con `uses:` y `needs:` en vez de copiar sus pasos; el del flujo también (recogida `0.6`, image-generator P6) | pendiente |
| A11 | Los cuatro modos de trabajo en el plan, `AGENTS.md` y `gw-selector`: SDD siempre (ficha), DDD con dominio, TDD con comportamiento testeable, exploración acotada (H17 P2; usuario, 2026-11-08) | pendiente |
| C11 | Ficha de tarea (`docs/tasks/<id>.md`, `taskRecord`): SDD, criterios de aceptación, archivos previstos y decision log por agente en la carpeta `docs/tasks/<id>/` (un archivo por entrada, `post-commit` rellena el sha); obligatoria en `feat`/`fix`/`hotfix` con código, comprobada por el `commit-msg`; `close-row <id>` exige casillas con test o check nombrado; absorbe D50 (H17 P1; [`I-lifecycle.md`](design/I-lifecycle.md) Q1-Q4; usuario, 2026-11-08) | pendiente |
| C12 | Rama de exploración `spike/<tema>` sin ficha ni `Refs:`, que el `pre-push` y `merge-branch.sh` no dejan fusionar en una rama de trabajo (H17 P2) | pendiente |
| C13 | Alcance congelado (`scopeGuard`): aviso o bloqueo al tocar un archivo fuera de `Files` de la ficha, `pre-commit` como respaldo, requisito nuevo = tarea nueva, registro de desviaciones para la retro (H17 P3) | pendiente |
| D68 | Fragmentos de CHANGELOG por rama (`changelog.d/`), plegados por `merge-branch.sh` o `version.py --release` (H17 P10) | pendiente |
| E32 | `permissions.deny` de lectura para secretos y gancho `PreToolUse` sobre `cat`/`grep` de esos archivos, con test; en `docs/es/`, qué sale hacia el proveedor (H17 P6) | pendiente |
| E33 | Contrato de revisión con anclas en `REVIEW.md`: `ruta:línea | severidad | ancla | problema. arreglo.`; sin ancla, observación (H17 P7) | pendiente |
| E35 | Registro de pruebas inestables (`flaky`): el check apunta lo que falla y pasa al reintentar y propone arreglarlo tras N veces (H17 P12) | pendiente |
| A12 | Idiomas configurables en un bloque `languages` de `.claude/gw.json`: `code` (código, nombres y comentarios; sustituye la regla fija de A8), `docs.primary` y `docs.others` (doc interna, bitácora, roadmap y commits; el emparejado `docs/es` ↔ `docs/en` los lee), `public.primary` y `public.others` (README, release, publicaciones) y `ui` (hoy `visibleLanguages`); el idioma del agente (en el que hablan usuario y agente) va por usuario en `~/.claude/gw.json`, identificado por `git config user.email`, con el principal de la doc como respaldo; `language` y `visibleLanguages` migran con `apply.py --update`; el MMC lo edita en la `1.1` (usuario, 2026-11-08) | pendiente |
| — | Lo de [`pending.md`](records/pending.md) marcado `0.7` | pendiente |
| D80 | Aviso automático de un sello de `gw-scout-updates` caducado (recogida de cierre `0.6`, private-project-1 P5) | pendiente |
| D83 | `apply.py --update` añade al `staleRefs` del proyecto los nombres que renombra su migración (amplía D46) (recogida de cierre `0.6`, instalador P4) | pendiente |
| D87 | `gw-init` ofrece licencia doble: MIT para el código y CC BY-NC-SA 4.0 para el contenido, con la nota de terceros (recogida de cierre `0.6`, world-maker P6) | pendiente |
| E41 | El `pre-commit` rechaza un autor de la lista `authorDeny` (vacía por defecto en los proyectos; con Claude en este repo); cambia la línea de `AGENTS.md` que dice que ningún gancho comprueba el autor (recogida de cierre `0.6`, private-project-1 P6) | pendiente |

## `0.8` «Front y otros agentes»

| Id | Tarea | Estado |
|---|---|---|
| E4 | Perfiles de instalación (minimal/core/full, `core` por defecto) en `gw-init` y `gw-update` | pendiente |
| E5 | Pruebas de front según la investigación | pendiente |
| E7 | Guía de pruebas de front en `docs/es/patterns.md` y plantilla de config | pendiente |
| E9-E16 | Los checks de front decididos en [`E-quality.md`](design/E-quality.md) (capturas, cuándo corren, tokens, preprocesadores, accesibilidad, referencias, sin servicios de pago, matriz) | pendiente |
| D7 | `AGENTS.md` legible sin `@include`; skills también en `.agents/skills` (opencode, Codex) | pendiente |
| B9 | Modelos de fuera de Anthropic vía opencode | pendiente |
| — | Lo de [`pending.md`](records/pending.md) marcado `0.8` | pendiente |
| E42 | Skill `gw-seo` (SEO y vistas previas de webs estáticas) traída del portal: sin rutas del portal, nombres en inglés, tests en el check, docs es/en y la LICENSE MIT de su fuente (recogida de cierre `0.6`, portal P1) | pendiente |

## `0.9` «Estable»

| Id | Tarea | Estado |
|---|---|---|
| E8 | Repaso completo de la documentación, por subagentes | pendiente |
| E28 | Revisión de seguridad: ganchos y scripts (entradas, rutas, `eval`), permisos de `settings.json`, CI y secretos; ideas de [`cloudflare/security-audit-skill`](https://github.com/cloudflare/security-audit-skill), leído con un subagente y con su licencia mirada antes de copiar nada (usuario, 2026-11-05) | pendiente |
| E29 | Revisión de anonimización: datos privados en el historial y en los documentos, y si `private-check` y sus `EXCEPTIONS` siguen bastando (usuario, 2026-11-05) | pendiente |
| E30 | Revisión de valores configurables: umbrales, rutas y comportamientos fijos en el código pasan a `.claude/gw.json` y `docs/es/config.md` (regla «Todo configurable», G4; usuario, 2026-11-05) | pendiente |
| E31 | Refactorización y mantenimiento de los `.md`: duplicados, un dato en un solo sitio, tamaños y texto obsoleto, con `writing-for-agents` (usuario, 2026-11-05) | pendiente |
| G2 | Salidas JSON con versión en los scripts que use el MMC | pendiente |
| E34 | `scripts/audit.py`: solapes y duplicados entre `AGENTS.md`, skills y `docs/`, con el dueño del dato y los tokens que ahorra; lo usan `gw-opt-tokens`, E31 y el MMC (H17 P9) | pendiente |
| E36 | Pruebas de comportamiento de las skills (un par de casos por skill, a mano antes de cada versión) (H17 P13) | pendiente |
| E37 | Citas de repos: en `docs/design` y `docs/research` quedan solo repos públicos con enlace y los proyectos privados del usuario pasan a «proyecto piloto A/B»; la regla en una línea de `AGENTS.md` y la clave `privateNames` de `.claude/gw.json` comprobada por `names-check.py` ([`I-lifecycle.md`](design/I-lifecycle.md) Q8 y Q12; usuario, 2026-11-08) | pendiente |
| — | Lo de [`pending.md`](records/pending.md) marcado `0.9` | pendiente |

## `1.0` — MMC 1, solo lectura

| Id | Tarea | Estado |
|---|---|---|
| G1 | `mmc.py` en `127.0.0.1` | pendiente |
| G3 | `mmc.py --static` para la nube | pendiente |
| G6 | Vistas de datos | pendiente |
| G7 | Vista de git: ramas, entornos, etiquetas, check y CI | pendiente |

## `1.1` — MMC 2, config

| Id | Tarea | Estado |
|---|---|---|
| G4 | Config desde el MMC a través de `config.py`, con el diff y sin commit | pendiente |
| G11 | Instrucciones renderizadas desde el config: las fuentes (`templates/`, `skills/`) llevan las dos ramas de cada interruptor (`<!-- gw:if clave -->…<!-- gw:else -->…<!-- gw:end -->`) y `apply.py` deja en la copia instalada solo la que toca; cambiar una clave (un botón del MMC) re-renderiza lo afectado y `doctor.py` avisa si una copia no coincide con el config. Solo interruptores de comportamiento (booleanos y enums); los documentos para personas siguen con las dos ramas. Antes: prueba con un interruptor (el modo restringido de B11) y medida del ahorro; decidir qué hacen las skills del plugin (Fase 9), que no se renderizan por proyecto (usuario, 2026-11-11) | pendiente |

## `1.2` — MMC 3: perfiles, entornos y roles

| Id | Tarea | Estado |
|---|---|---|
| G5 | Perfiles por capas | pendiente |
| G8 | Entornos y roles en el MMC | pendiente |
| D9 | Entornos configurables (`environments` en `gw.json`) y nuevos | pendiente |
| D10 | Etiquetas `rc` en `uat` | pendiente |
| D17 | Roles, con la comprobación del usuario de git por entorno (capa de aviso; la autoridad la da la protección de ramas; reabierta en [`I-lifecycle.md`](design/I-lifecycle.md)) | pendiente |
| D67 | Hecho por entorno y aprobaciones: `environments[].done/approvers/requires`, `promote.py` (mismo sha, trailer `Approved-by: <rol> <usuario>`, etiqueta), `pre-push` del destino que lo exige; fusionar fuera del entorno de desarrollo lo hace una persona con rol (H17 P4; usuario, 2026-11-08) | pendiente |
| I1 | `riskPaths`: rutas de riesgo que exigen plan de vuelta atrás en la ficha y aprobador humano en cualquier entorno | pendiente |
| I2 | Declaraciones del proyecto para `prod` (`environments[].requires`: vuelta atrás, observabilidad, humo) en `docs/records/declarations/`, con fecha y caducidad | pendiente |

## Después, sin versión

Se le pone versión al abrir la menor en que quepa, cuando exista lo que necesita.

| Id | Tarea | Necesita |
|---|---|---|
| B8 | Tabla determinista de modelos por necesidad (segunda parte) | Cuatro semanas de ledger |
| B13 | Tendencia publicada y una prueba A/B con el flujo y sin él | Ledger |
| B12 | Patrón «scouts» en `gw-orchestrate-dealer`, medido antes y después | Ledger |
| C9 | `modes.freeze <carpeta>` | C7 |
| G10 | MMC multiproyecto | `1.0` |
| — | OpenTelemetry como opción de B1 | B1 |
| — | Recogida de los repos privados (R3) | Acceso de lectura |
