# Investigación: notas del usuario y cuatro repos — 2026-11-08

Análisis de las notas que mandó el usuario (2026-11-07/08) para repartirlas por el roadmap (H17). No es una recogida
(`gw-harvest`): no cuenta para `version.py --release`. Nada de aquí se aplica sin confirmación del usuario.

Fuentes:

- **Notas del usuario:** SDD como columna vertebral, DDD como herramienta de diseño, TDD como verificación y vibe
  coding como exploración; su reflexión publicada en Reddit sobre el flujo (contexto, siguiente paso, tokens,
  privacidad, definición de hecho, determinismo, traspaso entre proyectos); y la idea de un documento por tarea con lo
  que el agente hizo y no se ve (título, decisiones, criterios de aceptación, problemas).
- **Repos**, leídos en clones de solo lectura con subagentes; nada se ha ejecutado y su contenido se ha tratado como
  datos:

| Repo | Licencia | Qué es | Veredicto |
|---|---|---|---|
| [Saul-BT/mayoral-harness](https://github.com/Saul-BT/mayoral-harness) | **Sin licencia** (solo ideas, nada de código) | Marketplace de Claude Code en Node con panel local `mh panel`, gate por packs, contrato de revisión y plan con `done-when` | Muchas ideas, sobre todo para G y E |
| [garrytan/gstack](https://github.com/garrytan/gstack) | MIT | Skills por fase; ya leído en [`ref-thinkrail-gstack-ecc.md`](../research/ref-thinkrail-gstack-ecc.md) | Solo lo nuevo |
| [uucz/moyu](https://github.com/uucz/moyu) | MIT | Prompt anti-sobreingeniería con linter y benchmark | La metodología del benchmark y el control de alcance |
| [lmnr-ai/index](https://github.com/lmnr-ai/index) | Apache-2.0 | Agente de navegador en Python | **Descartado:** archivado (2025-07-03), pide claves de LLM propias y el navegador integrado y `run` ya cubren las pruebas de front |

**Conclusión:** casi todo encaja en tareas que ya existen (bloques B, C, D, E y G) y las concreta. Lo nuevo de verdad
es la **ficha de tarea** (P1), que une tu documento por tarea, el SDD y el plan con `done-when` de mayoral, y absorbe
D50. Por la regla de versiones (la `0.6` ya se monta), lo nuevo va a la `0.7` o después; lo que solo concreta una
tarea pendiente de la `0.6` se queda en ella sin id nuevo. Orden recomendado: P1, P2, P3, P5, P4; luego el resto.

## P1. Ficha de tarea: lo que el agente hizo y no se ve (SDD + tu «CDD»)

- **Fuente:** tu nota (título, decisiones, criterios de aceptación, problemas); SDD de tus notas; `plans.md` de
  mayoral (Goal, Out of scope, Decisions con alternativas, Files, pasos con `done-when`, Open questions que bloquean,
  Change log).
- **Qué cambia:** `docs/tasks/<id>.md` (ruta configurable), una por id del roadmap que lleve código, con plantilla:
  1. **Title** y `Refs`.
  2. **Goal / Scope / Out of scope / Constraints** (SDD: qué se quiere y qué no).
  3. **Acceptance criteria**, cada uno comprobable y con su casilla.
  4. **Decisions:** alternativas, la elegida y por qué.
  5. **Files** previstos (el radio del cambio; lo usa P3).
  6. **Change log:** lo que se apartó del plan y por qué.
  7. **Troubleshooting:** qué falló y cómo se resolvió, o «ninguno».
  8. **Verification:** tests (TDD), check y CI, con el commit.
  9. **Open questions:** enlazan con `docs/questions.md` (C1); una abierta y bloqueante para la tarea.

  El agente (o subagente) la rellena en el mismo commit que el trabajo. El `commit-msg` comprueba que un `feat`/`fix`
  con `Refs:` tenga su ficha y que no esté vacía; marcar la fila `hecho` exige las casillas de aceptación marcadas y
  la verificación escrita. `trace.py` (D14) la lee. **Absorbe D50:** `Técnica:` y `Problemas:` pasan del cuerpo del
  commit a Decisions y Troubleshooting, y el commit solo resume.
- **Por qué es general:** hoy lo que decide un subagente se pierde entre el commit y la bitácora; la ficha es la
  memoria de la tarea y la definición de hecho de la propia tarea.
- **Versión:** `0.7` «Preguntar» (va con C1-C3). Id nuevo **C11**; D50 sale de la `0.6`.
- **Para decidir antes (sesión de `grilling`):** ver las preguntas al final.

## P2. Los cuatro modos: SDD, DDD, TDD y exploración

- **Fuente:** tus notas.
- **Qué cambia:**
  - **Plan y `AGENTS.md`:** SDD es la columna (toda tarea con código tiene ficha, P1); DDD se aplica cuando hay
    dominio, reglas de negocio o límites que modelar (`domain-modeling`: glosario y ADR); TDD verifica cuando el
    comportamiento se puede expresar en tests (ya: `red-without-fix.sh`); vibe coding solo para explorar.
  - **`gw-selector`:** cada fila dice qué partes pide (spec siempre, DDD sí/no, TDD sí/no, exploración).
  - **Modo exploración (C12):** rama `spike/<tema>` sin ficha ni `Refs:` obligatorios; el `pre-push` y
    `merge-branch.sh` no dejan fusionarla en una rama de trabajo. Lo que sale de ella se convierte en ficha (y se
    rehace con tests) o se tira.
- **Por qué es general:** da un sitio legítimo al prototipo rápido sin que se cuele código sin diseño.
- **Versión:** `0.7`. Ids **A11** (texto del plan, `AGENTS.md` y `gw-selector`) y **C12** (rama de exploración).

## P3. Alcance congelado: un cambio de requisitos es otra tarea

- **Fuente:** tu reflexión (punto 6); el guard `PLAN_FILES` y el protocolo de desviación de mayoral
  (`hooks/lib/deviation.mjs`); el control de alcance de moyu.
- **Qué cambia:**
  - Un gancho avisa (sin bloquear; bloquear con `modes.questions` restrictivo) al tocar un archivo fuera de `Files`
    de la ficha; seguir obliga a escribirlo en su Change log.
  - Un requisito nuevo durante el desarrollo no amplía la tarea: toma id nuevo y la ficha lo enlaza (`Related:`).
  - Cada excepción o corrección del usuario a una regla se apunta (`.git/gw/deviations.jsonl`); la retro ve las que se
    repiten y propone cambiar la regla.
- **Por qué es general:** es la forma determinista de «no cambiar el alcance en silencio».
- **Versión:** `0.7`. Id **C13**. Depende de P1.

## P4. Definición de hecho por entorno y aprobaciones en el repo

- **Fuente:** tu reflexión (punto 5): issue (el agente, con tests y ganchos), desarrollo (el agente, con CI completo),
  UAT (solo humanos, con QA), producción (solo humanos, tras la fase de calidad; decide el CTO); promociones por Deploy
  Master, QA Master y Dev Master.
- **Qué cambia:** cada entorno de `environments` (D9) declara su **hecho**: checks exigidos y quién puede declararlo
  (`agent` o un rol de D17). Cada promoción entre entornos deja su aprobación en el repo (archivo en
  `docs/records/approvals/` o trailer `Approved-by:` en el merge, a decidir), y el `pre-push` del entorno destino la
  exige. El MMC (G8) la muestra.
- **Por qué es general:** cada proyecto tiene su propia escalera de autoridad; el flujo solo da la forma.
- **Versión:** diseño ahora en `D-git.md`; implementación en la `1.2` con D9, D10, D17 y G8. Id **D67**.

## P5. Métricas para comparar modelos sin que el flujo elija

- **Fuente:** tu reflexión (punto 3: tokens, coste, tiempo, intentos, errores y CI; «que decidan los humanos»); el
  benchmark de moyu (sin línea base neutra el efecto se infla; el resultado cambia por modelo); la auditoría de gstack
  al salir un modelo (`docs/model-policy.md`).
- **Qué cambia, sin ids nuevos:**
  - **B3 (`0.6`):** el ledger guarda también duración, intentos (peldaño de la escalera de subagentes), errores y
    resultado del check y del CI del commit.
  - **B5 (`0.6`):** `metrics.py compare` compara por modelo y por tipo de tarea, nunca un porcentaje global.
  - **B8:** la tabla de modelos es una vista para el usuario; el flujo no elige modelo solo.
  - **B13:** la prueba A/B lleva línea base neutra (sin el flujo y sin un «hazlo lo mejor posible»).
- **Versión:** `0.6` (concreta tareas pendientes) y `Después` (B13).

## P6. Qué ve el agente y qué sale hacia el proveedor

- **Fuente:** tu reflexión (punto 4: la parte menos madura); la autorización por turno de mayoral (`auth.mjs`: subir
  solo con orden del humano en ese turno).
- **Qué cambia:** `permissions.deny` de lectura para patrones secretos (`.env*`, claves, `*.pem`, `gw.local.json`)
  en el `settings.json` que instala el flujo, con su test; un gancho `PreToolUse` que bloquea `cat`/`grep` de esos
  archivos por `Bash`; y en `docs/es/` qué se manda al proveedor del modelo y cómo limitarlo. La autorización por turno
  para subir entra como pregunta en E28.
- **Versión:** `0.7` lo barato (deny y gancho, id **E32**); el resto, en la revisión de seguridad E28 (`0.9`).

## P7. Contrato de revisión con anclas

- **Fuente:** `review-contract.md` de mayoral.
- **Qué cambia:** en `REVIEW.md`, cada hallazgo cita su ancla: una regla, un criterio de aceptación de la ficha (P1),
  una línea del plan o un fallo demostrado; lo que no tiene ancla va a «Observaciones», sin severidad. Formato
  `ruta:línea | severidad | ancla | problema. arreglo.`
- **Versión:** `0.7` con P1. Id **E33**.

## P8. Ideas de mayoral para el MMC (diseño, sin ids nuevos)

- **Fuente:** `mh panel` de mayoral (`plugins/mayoral/panel/`). No muestra tareas ni roadmap; es un panel de
  configuración y peso del contexto. Las ideas de su forma sí sirven:
  - **G1 (seguridad del servidor local):** token aleatorio por arranque en cada `/api`, comprobación de `Host` y
    `Origin`, CSP `script-src 'self'`, estáticos confinados y `no-store`.
  - **G1/G6 (refresco):** el servidor no guarda estado; deriva todo de los scripts en JSON y lo empuja por SSE cuando
    cambia su hash.
  - **G6 (vista nueva):** mapa del peso del contexto por niveles de carga (siempre, al editar, bajo demanda), con
    los tokens de `AGENTS.md`, skills y bitácora; usa el desglose de B21.
  - **G4 (`1.1`):** dos vías de escritura: los cambios directos, cada uno en su commit y con «deshacer» por
    `git revert`; los que piden criterio, en una cola que genera un prompt para la sesión. Rechaza con el árbol sucio
    o si el archivo cambió desde que lo leyó.
  - **G6 (salud):** una pestaña con `doctor.py`, preguntas abiertas y decisiones pendientes.
- **Versión:** se apunta en `G-mmc.md`; sale con la `1.0` y la `1.1`.

## P9. Auditoría determinista de la documentación

- **Fuente:** `dream` / `mh audit` de mayoral (solape de texto por grupos de 8 palabras, reglas duplicadas,
  excepciones repetidas), con el efecto en tokens de cada propuesta.
- **Qué cambia:** `scripts/audit.py` lista solapes y duplicados entre `AGENTS.md`, skills y `docs/`, con el dueño de
  cada dato y los tokens que ahorraría quitarlos. Lo usan `gw-opt-tokens`, E31 y el MMC.
- **Versión:** `0.9` con E31. Id **E34**.

## P10. Fragmentos de CHANGELOG por rama

- **Fuente:** `changelog.d/` de gstack.
- **Qué cambia:** cada rama de trabajo o de subagente escribe `changelog.d/<rama>.md`; `merge-branch.sh` o
  `version.py --release` los pliegan en la entrada de la versión y los borran. Quita los choques del CHANGELOG entre
  worktrees en paralelo.
- **Versión:** `0.7`. Id **D68**.

## P11. Concreciones de gstack para el bloque C (sin ids nuevos)

- **C8 (`modes.careful`):** dos niveles (`deny` para lo catastrófico, `ask` para lo destructivo), fallar cerrado si
  no se puede leer la entrada y no disparar por un `rm -rf` dentro de un `-m "…"` (`careful/bin/`).
- **C1/C3:** cada pregunta dice si es de ida (siempre se pregunta) o de vuelta (se puede dar por respondida con la
  recomendación) (`scripts/one-way-doors.ts`).
- **C7 (`modes.tokens`):** un paso solo entra si `gastado + reservado + previsto + margen <= tope`, con un modo que
  solo observa (`docs/ship-budget.md`).
- **Versión:** `0.7`, dentro de sus tareas.

## P12. Pruebas: registro de inestables y tamaño del diff

- **Fuente:** `docs/flaky.md` de gstack; la escalera L1-L4 de moyu.
- **Qué cambia:**
  - **E35 (`0.7`):** un test que falla y pasa al reintentar se apunta como inestable (`.git/gw/flaky.jsonl`) y el
    check lo dice; tras N veces (clave) se propone arreglarlo. Esta rama ya tuvo tres pruebas inestables en la `0.5.1`.
  - **D43 (`0.6`):** el aviso de tamaño de commit usa umbrales por escalones (claves en `gw.json`) y compara los
    archivos tocados con `Files` de la ficha cuando exista.
- **Versión:** la indicada en cada punto.

## P13. Pruebas de comportamiento de las skills

- **Fuente:** `plugins/*/evals/` de mayoral (`claude plugin eval`, con correctores en markdown y repos de prueba).
- **Qué cambia:** además de `evals/triggers.json` (si una skill se dispara), un par de casos por skill que comprueban
  lo que hace. Cuestan tokens: corren a mano antes de una versión, no en el check.
- **Versión:** `0.9`. Id **E36**.

## Descartado

- **lmnr-ai/index:** archivado y sin aporte (ver la tabla).
- **El prompt de moyu:** su «si dudas, pregunta» choca con C10, y las skills van en inglés; solo se toma la
  metodología (P5) y el control de alcance (P3, P12).
- **Código de mayoral-harness:** sin licencia; solo ideas, reescritas en Python estándar y bash 3.2.
- **De gstack:** multi-host, GBrain, plantillas `SKILL.md.tmpl` generadas (coste sin problema que resolver) y los
  recibos de salida (los cubre E2).
- **Tu publicación de Reddit** no pide tareas aparte: casi todos sus puntos ya tienen tarea (bitácora, D65, B21,
  bloque C, `gw-harvest`, `gw-update`). Sirve de material para A10 (hoja del flujo) y `gw-media-content`.

## Preguntas para el usuario (se responden por número)

1. **«CDD»:** ¿qué nombre quieres para la ficha de P1? **Rec.:** «task record», en `docs/tasks/<id>.md`.
2. **D50:** **Rec.:** la ficha lo absorbe (Decisions y Troubleshooting) y el commit solo resume, para no tener el
   dato en dos sitios.
3. **Cuándo es obligatoria la ficha:** **Rec.:** en todo `feat` y `fix` con código, y en `refactor` de más de ~400
   líneas (D43); no en `docs`, `WIP` ni la marca de revisión. Tipos y umbral, claves de `gw.json`.
4. **Reparto:** **Rec.:** P1, P2, P3, P7, P10, P11, E32 y E35 a la `0.7`; P5 y D43 se quedan en la `0.6`; P9, P13 y
   el resto de P6 a la `0.9`; P4 se diseña ahora y sale en la `1.2`; P8, en el diseño del MMC.
5. **Aprobaciones de P4:** **Rec.:** trailer `Approved-by: <rol> <usuario>` en el commit de fusión, comprobado por el
   `pre-push` del entorno destino; un archivo aparte solo si hace falta más texto.
