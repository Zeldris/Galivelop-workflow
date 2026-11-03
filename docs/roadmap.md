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
  calidad, G Management Center (MMC), H roadmap.
- Una tarea nueva toma el siguiente número libre de su bloque; un número nunca se reutiliza, ni el de una tarea
  descartada. Las tareas del bloque A que salen de sus apartados y no de una pregunta empiezan en `A7` (sus preguntas
  llegan a `A-6`).
- Las preguntas que solo decidían algo (por ejemplo, D1, D2 o D4) no son tareas y no salen aquí.
- Estados: `hecho`, `en curso`, `pendiente`. Al cerrar una tarea, su fila dice el commit.
- Los ids de los scripts y los ganchos se leen de esta versión en español; [`roadmap.en.md`](roadmap.en.md) la
  traduce.

## Regla de versiones

Solo la última menor publicada recibe parches; los evolutivos van a la siguiente menor (H14, plan §7). Se avanza por
la `0.x`, donde una menor puede romper: **todo lo que rompe va en la `0.5`**, para migrar una sola vez. La `1.0` es
el MMC. A lo sumo una publicación al día (A-6).

## `0.4.4` — parche

| Id | Tarea | Estado |
|---|---|---|
| D6 | `worktree.baseRef: "head"` en el `settings.json` que instala el flujo | pendiente |
| — | Retro `0.4.2` P5: la regla QUOTED del `pre-commit` sin falsos positivos en `.md` ([`pending.md`](records/pending.md)) | pendiente |
| — | Arreglos del CI de Ubuntu y macOS (rama `ccr-6dfbc880-ddr41g`, `4b7bf8a`..`66a4ecd`) | hecho |
| D32 | `harvest.py` reconoce las skills con el nombre anterior a A8 y una copia vieja de `writing-for-agents` (image-generator P1, P12) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D33 | `config-guard.py`: `settings.local.json`, worktrees y más órdenes que escriben; sin falso positivo en `touch -r` (portal P2, WMF P8) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D34 | `commit-msg` deja pasar un `WIP:` sin `gw.json` legible y no falla fuera de un árbol de trabajo (portal P4, WMF P11) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D35 | `/gw-update` en un clon de una sola rama usa las etiquetas (portal P3) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D36 | `reviewed.sh` sugiere `--footer` al fallar y pone `Siguiente:` por defecto con `commitNext` (WMF P2) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| E18 | Tests de las skills instaladas aislados del proyecto donde corren (WMF P3) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D37 | `pre-commit`: `KEY_FORMATS` con claves pegadas a una letra o dígito; sin falso positivo en diccionarios de tests (image-generator P2, P3) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D38 | La marca de subida en curso del `pre-push`, una por worktree (portal P5) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |
| D39 | `subagent-cap.py`: contador que se limpia y sin enlaces simbólicos (portal P7, WMF P9) | pendiente (se hace en la `0.5` y se lleva a la rama del parche) |

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
| B14 | `recover.py --state` avisa del presupuesto de compactaciones superado (private-project-1 P1) | pendiente |
| D40 | Aviso de ramas remotas con trabajo fuera de la protegida (WMF P1, private-project-1 P4) | pendiente |
| B15 | Aviso de un subagente lanzado sin `model` (portal P1) | pendiente |
| E19 | El check falla con una `TestCase` después de `unittest.main()` (private-project-1 P2) | pendiente |
| — | Lo de [`pending.md`](records/pending.md) marcado `0.5` | repartido en D18-D31 y E17 |

## `0.6` «Medir»

| Id | Tarea | Estado |
|---|---|---|
| B1 | Gancho `Stop` que lee los logs de sesión | pendiente |
| B2 | `docs/metrics/ledger.jsonl` en el repo | pendiente |
| B3 | Qué se guarda: tokens por modelo y tipo, fecha, rama, `Refs`, subagente; precios en tabla con fecha | pendiente |
| B4 | Informes por periodo: `metrics.py report --period …` y skill `gw-metrics` | pendiente |
| B5 | Comparaciones: `metrics.py compare` | pendiente |
| B6 | Aviso en el `SessionStart` cuando un modelo gasta 1,5× su media | pendiente |
| B7 | `models.disabled` en `gw.json`, con su gancho | pendiente |
| B8 | Señales de calidad junto al gasto (la tabla determinista, en «Después») | pendiente |
| B10 | El `gw-selector` recomienda modelo y esfuerzo de la sesión principal | pendiente |
| B11 | Modelo y esfuerzo por agente (palancas de Claude Code) | pendiente |

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
| — | Lo de [`pending.md`](records/pending.md) marcado `0.7` | pendiente |

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

## `0.9` «Estable»

| Id | Tarea | Estado |
|---|---|---|
| E8 | Repaso completo de la documentación, por subagentes | pendiente |
| G2 | Salidas JSON con versión en los scripts que use el MMC | pendiente |
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

## `1.2` — MMC 3: perfiles, entornos y roles

| Id | Tarea | Estado |
|---|---|---|
| G5 | Perfiles por capas | pendiente |
| G8 | Entornos y roles en el MMC | pendiente |
| D9 | Entornos configurables (`environments` en `gw.json`) y nuevos | pendiente |
| D10 | Etiquetas `rc` en `uat` | pendiente |
| D17 | Roles, con la comprobación del usuario de git por entorno | pendiente |

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
