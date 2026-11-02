# Roadmap

[English](roadmap.en.md)

Qué va en cada versión, con un identificador por tarea. Es la **única fuente de ids** (D13): los commits los citan en
`Refs:` (D12, desde la `0.5`), el CHANGELOG los nombra y `trace.py <id>` (D14) junta todo lo de uno. El diseño de cada
tarea está en [`docs/diseno/`](diseno/README.md); el reparto, en [`H-roadmap.md`](diseno/H-roadmap.md) (mapa nuevo,
aprobado el 2026-11-01). Los evolutivos que trajeron las recogidas siguen en [`pendiente.md`](registros/pendiente.md),
con su versión en cada línea (H12).

## Identificadores

- Cada tarea lleva la letra de su bloque de diseño y un número sin guion: `B3` es la pregunta 3 de
  [`B-medicion.md`](diseno/B-medicion.md). Los bloques: A marco, B medición y modelos, C preguntas y modos, D git, E
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
| — | Retro `0.4.2` P5: la regla QUOTED del `pre-commit` sin falsos positivos en `.md` ([`pendiente.md`](registros/pendiente.md)) | pendiente |
| — | Arreglos del CI de Ubuntu y macOS (rama `ccr-6dfbc880-ddr41g`, `4b7bf8a`..`66a4ecd`) | hecho |

## `0.5` «Base» — lo que rompe

En este orden, porque cada paso usa el anterior.

| Id | Tarea | Estado |
|---|---|---|
| H14 | Regla de versiones nueva en `AGENTS.md` y el plan §7 | hecho (`a1ac1e3`) |
| D13 | Este roadmap, con los ids, en español e inglés | hecho |
| H12 | `pendiente-1.0.0.md` → `pendiente.md`, con la versión en cada línea | hecho |
| A7 | Plan reescrito según la tabla de A1 (§1, §2, §7, §9, §10): repo público, cada versión se publica aquí | pendiente |
| A8 | Nombres (A2, A-3, A-4): `gw-` en las skills propias, scripts en inglés, rutas del proyecto en inglés y configurables en `gw.json`; `gw-update` renombra y los ganchos aceptan los dos nombres durante la `0.x` | pendiente |
| A9 | `schemaVersion` en `gw.json` y su migración en `gw-update` (A3.2) | pendiente |
| D11 | Conventional Commits en la primera línea (`fix(B1): …`); `version.py` sugiere el salto | pendiente |
| D12 | Trailer `Refs: <id>` obligatorio en `commit-msg` (salvo merges), validado contra este archivo | pendiente |
| D15 | Trailer `Agent:` opcional, sin nombre de modelo | pendiente |
| D16 | Ramas de subagente `agent/<id>-…`; `fusionar.sh` copia `Refs:` | pendiente |
| E2 | Check de datos privados en el `pre-push` (lista en `.claude/gw.local.json`); el CI, solo claves y correos | pendiente |
| E3 | Recogidas publicadas anonimizadas (`private-project-1`) | pendiente |
| D3 | Repaso de las recogidas ya publicadas con el check de E2 | pendiente |
| E1 | Auditoría de `AGENTS.md` y `CLAUDE.md`, con check de tope de líneas | pendiente |
| E6 | Cada regla de `REVIEW.md` nombra su check o dice «criterio» | pendiente |
| — | Lo de [`pendiente.md`](registros/pendiente.md) marcado `0.5` | pendiente |

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
| B10 | El `selector` recomienda modelo y esfuerzo de la sesión principal | pendiente |
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
| — | Lo de [`pendiente.md`](registros/pendiente.md) marcado `0.7` | pendiente |

## `0.8` «Front y otros agentes»

| Id | Tarea | Estado |
|---|---|---|
| E4 | Perfiles de instalación (minimal/core/full, `core` por defecto) en `gw-init` y `gw-update` | pendiente |
| E5 | Pruebas de front según la investigación | pendiente |
| E7 | Guía de pruebas de front en `docs/es/patrones.md` y plantilla de config | pendiente |
| E9-E16 | Los checks de front decididos en [`E-calidad.md`](diseno/E-calidad.md) (capturas, cuándo corren, tokens, preprocesadores, accesibilidad, referencias, sin servicios de pago, matriz) | pendiente |
| D7 | `AGENTS.md` legible sin `@include`; skills también en `.agents/skills` (opencode, Codex) | pendiente |
| B9 | Modelos de fuera de Anthropic vía opencode | pendiente |
| — | Lo de [`pendiente.md`](registros/pendiente.md) marcado `0.8` | pendiente |

## `0.9` «Estable»

| Id | Tarea | Estado |
|---|---|---|
| E8 | Repaso completo de la documentación, por subagentes | pendiente |
| G2 | Salidas JSON con versión en los scripts que use el MMC | pendiente |
| — | Lo de [`pendiente.md`](registros/pendiente.md) marcado `0.9` | pendiente |

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
| B12 | Patrón «scouts» en `orchestrate-dealer`, medido antes y después | Ledger |
| C9 | `modes.freeze <carpeta>` | C7 |
| G10 | MMC multiproyecto | `1.0` |
| — | OpenTelemetry como opción de B1 | B1 |
| — | Recogida de los repos privados (R3) | Acceso de lectura |
