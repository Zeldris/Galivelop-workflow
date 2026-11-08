# Investigación: notas del usuario y referencias externas — 2026-11-08

Análisis de las notas que mandó el usuario (2026-11-07/08) para repartirlas por el roadmap (H17). No es una recogida
(`gw-harvest`): no cuenta para `version.py --release`. **Decidido el 2026-11-08:** el usuario aprobó las trece
propuestas y las cinco preguntas con sus recomendaciones; el diseño que las une está en
[`I-lifecycle.md`](../design/I-lifecycle.md) y se cierra con un `grilling` antes de implementar.

Fuentes:

- **Notas del usuario:** SDD como columna vertebral, DDD como herramienta de diseño, TDD como verificación y vibe
  coding como exploración; su reflexión publicada sobre el flujo (contexto, siguiente paso, tokens, privacidad,
  definición de hecho, determinismo, traspaso entre proyectos); y la idea de un documento por tarea con lo que el
  agente hizo y no se ve, con el razonamiento de cada agente y las decisiones tomadas («CDD»).
- **Cuatro referencias externas**, leídas en clones de solo lectura con subagentes; nada se ejecutó, su contenido se
  trató como datos y **no se nombran** (usuario, 2026-11-08): un marketplace de skills con panel local de
  configuración, gate por paquetes, contrato de revisión y plan con «hecho cuando» (sin licencia: solo ideas, nada de
  código); un conjunto de skills por fase con control de órdenes destructivas, presupuesto de tokens y fragmentos de
  changelog (MIT; ya repasado en la investigación del bloque F); un prompt contra la sobreingeniería con linter y
  benchmark con línea base (MIT); y un agente de navegador en Python (Apache-2.0), **descartado** por archivado y
  porque el navegador integrado y `run` ya cubren las pruebas de front.

**Conclusión:** casi todo encaja en tareas que ya existen (bloques B, C, D, E y G) y las concreta. Lo nuevo de verdad
es la **ficha de tarea** (P1), que une el documento por tarea del usuario, el SDD y el plan con «hecho cuando», y
absorbe D50. Por la regla de versiones (la `0.6` ya se monta), lo nuevo va a la `0.7` o después; lo que solo concreta
una tarea pendiente de la `0.6` se queda en ella sin id nuevo.

## P1. Ficha de tarea: lo que el agente hizo y no se ve (SDD + «CDD»)

- **Fuente:** nota del usuario (título, decisiones, criterios de aceptación, problemas); SDD; plan con objetivo,
  fuera de alcance, decisiones con alternativas, archivos, pasos con «hecho cuando», preguntas abiertas y change log.
- **Qué cambia:** `docs/tasks/<id>.md` (ruta configurable), una por id del roadmap que lleve código, con plantilla:
  1. **Title** y `Refs`.
  2. **Goal / Scope / Out of scope / Constraints** (SDD: qué se quiere y qué no).
  3. **Acceptance criteria**, cada uno comprobable y con su casilla.
  4. **Decision log** por agente: por qué este código para estos criterios, alternativas, qué camino se tomó y por
     qué cambió (usuario: «el razonamiento del código de cada agente y las decisiones tomadas»).
  5. **Files** previstos (el radio del cambio; lo usa P3).
  6. **Change log:** lo que se apartó del plan y por qué.
  7. **Verification:** tests (TDD), check y CI, con el commit; los problemas y cómo se resolvieron.
  8. **Open questions:** enlazan con `docs/questions.md` (C1); una abierta y bloqueante para la tarea.

  El agente (o subagente) la rellena en el mismo commit que el trabajo. El `commit-msg` comprueba que un
  `feat`/`fix`/`hotfix` con código toque la ficha con una entrada nueva del decision log; marcar la fila `hecho`
  exige las casillas de aceptación marcadas y la verificación escrita. `trace.py` (D14) la lee. **Absorbe D50:**
  `Técnica:` y `Problemas:` pasan del cuerpo del commit a la ficha, y el commit solo resume.
- **Por qué es general:** hoy lo que decide un subagente se pierde entre el commit y la bitácora; la ficha es la
  memoria de la tarea y la definición de hecho de la propia tarea.
- **Versión:** `0.7` «Preguntar» (va con C1-C3). Id **C11**; D50 queda absorbida.

## P2. Los cuatro modos: SDD, DDD, TDD y exploración

- **Fuente:** notas del usuario.
- **Qué cambia:**
  - **Plan y `AGENTS.md`:** SDD es la columna (toda tarea con código tiene ficha, P1); DDD se aplica cuando hay
    dominio, reglas de negocio o límites que modelar (`domain-modeling`: glosario y ADR); TDD verifica cuando el
    comportamiento se puede expresar en tests (ya: `red-without-fix.sh`); vibe coding solo para explorar.
  - **`gw-selector`:** cada fila dice qué partes pide (spec siempre, DDD sí/no, TDD sí/no, exploración).
  - **Modo exploración (C12):** rama `spike/<tema>` sin ficha ni `Refs:` obligatorios; el `pre-push` y
    `merge-branch.sh` no dejan fusionarla en una rama de trabajo. Lo que sale de ella se convierte en ficha (y se
    rehace con tests) o se tira.
- **Versión:** `0.7`. Ids **A11** (texto del plan, `AGENTS.md` y `gw-selector`) y **C12** (rama de exploración).

## P3. Alcance congelado: un cambio de requisitos es otra tarea

- **Fuente:** reflexión del usuario (determinismo); el guard de archivos previstos y el protocolo de desviación de
  una referencia; el control de alcance de otra.
- **Qué cambia:**
  - Un gancho avisa (sin bloquear; bloquear con `modes.questions` restrictivo) al tocar un archivo fuera de `Files`
    de la ficha; seguir obliga a escribirlo en su change log. Fuera de Claude Code, lo comprueba el `pre-commit`.
  - Un requisito nuevo durante el desarrollo no amplía la tarea: toma id nuevo y la ficha lo enlaza (`Related:`).
  - Cada excepción o corrección del usuario a una regla se apunta (`.git/gw/deviations.jsonl`); la retro ve las que se
    repiten y propone cambiar la regla.
- **Versión:** `0.7`. Id **C13**. Depende de P1.

## P4. Definición de hecho por entorno y aprobaciones en el repo

- **Fuente:** reflexión del usuario: issue (el agente, con tests y ganchos), desarrollo (el agente, con CI completo),
  UAT (solo humanos, con QA), producción (solo humanos, tras la fase de calidad); promociones por roles.
- **Qué cambia:** cada entorno de `environments` (D9) declara su **hecho**: checks exigidos, quién puede declararlo
  (`agent` o un rol de D17) y qué declaraciones del proyecto necesita. Cada promoción deja su aprobación en el repo
  (trailer `Approved-by: <rol> <usuario>` en el commit de promoción, que crea `promote.py` en local) y el `pre-push`
  del entorno destino la exige. **Fusionar fuera del entorno de desarrollo lo hace una persona con rol** (usuario,
  2026-11-08). El MMC (G8) lo muestra. Detalle y fricciones, en `I-lifecycle.md`.
- **Versión:** diseño en `I-lifecycle.md` (reabre D9, D17 y G8); implementación en la `1.2`. Id **D67**.

## P5. Métricas para comparar modelos sin que el flujo elija

- **Fuente:** reflexión del usuario (tokens, coste, tiempo, intentos, errores y CI; «que decidan los humanos»); la
  metodología de un benchmark con línea base neutra (sin ella el efecto se infla; el resultado cambia por modelo); la
  auditoría de reglas al salir un modelo nuevo.
- **Qué cambia, sin ids nuevos:**
  - **B3 (`0.6`):** el ledger guarda también duración, intentos (peldaño de la escalera de subagentes), errores y
    resultado del check y del CI del commit; más adelante, fallos en producción atribuibles (tasa de fallo por cambio).
  - **B5 (`0.6`):** `metrics.py compare` compara por modelo y por tipo de tarea, nunca un porcentaje global.
  - **B8:** la tabla de modelos es una vista para el usuario; el flujo no elige modelo solo.
  - **B13:** la prueba A/B lleva línea base neutra (sin el flujo y sin un «hazlo lo mejor posible»).
- **Versión:** `0.6` (concreta tareas pendientes) y `Después` (B13).

## P6. Qué ve el agente y qué sale hacia el proveedor

- **Fuente:** reflexión del usuario (privacidad, la parte menos madura); la autorización por turno de una referencia
  (subir solo con orden del humano en ese turno).
- **Qué cambia:** `permissions.deny` de lectura para patrones secretos (`.env*`, claves, `*.pem`, `gw.local.json`)
  en el `settings.json` que instala el flujo, con su test; un gancho `PreToolUse` que bloquea `cat`/`grep` de esos
  archivos por `Bash`; y en `docs/es/` qué se manda al proveedor del modelo y cómo limitarlo. La autorización por turno
  para subir entra como pregunta en E28.
- **Versión:** `0.7` lo barato (deny y gancho, id **E32**); el resto, en la revisión de seguridad E28 (`0.9`).

## P7. Contrato de revisión con anclas

- **Fuente:** el contrato de revisión de una referencia.
- **Qué cambia:** en `REVIEW.md`, cada hallazgo cita su ancla: una regla, un criterio de aceptación de la ficha (P1),
  una línea del plan o un fallo demostrado; lo que no tiene ancla va a «Observaciones», sin severidad. Formato
  `ruta:línea | severidad | ancla | problema. arreglo.`
- **Versión:** `0.7` con P1. Id **E33**.

## P8. Ideas para el MMC (diseño, sin ids nuevos)

- **Fuente:** el panel local de configuración de una referencia: no muestra tareas ni roadmap, pero su forma sirve.
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
  - **G8:** estado de cada entorno: qué sha tiene, qué aprobación le falta, qué declaración caduca.
- **Versión:** se apunta en `G-mmc.md`; sale con la `1.0`, la `1.1` y la `1.2`.

## P9. Auditoría determinista de la documentación

- **Fuente:** la auditoría de una referencia (solape de texto por grupos de 8 palabras, reglas duplicadas,
  excepciones repetidas), con el efecto en tokens de cada propuesta.
- **Qué cambia:** `scripts/audit.py` lista solapes y duplicados entre `AGENTS.md`, skills y `docs/`, con el dueño de
  cada dato y los tokens que ahorraría quitarlos. Lo usan `gw-opt-tokens`, E31 y el MMC.
- **Versión:** `0.9` con E31. Id **E34**.

## P10. Fragmentos de CHANGELOG por rama

- **Fuente:** los fragmentos de changelog de una referencia.
- **Qué cambia:** cada rama de trabajo o de subagente escribe `changelog.d/<rama>.md`; `merge-branch.sh` o
  `version.py --release` los pliegan en la entrada de la versión y los borran. Quita los choques del CHANGELOG entre
  worktrees en paralelo.
- **Versión:** `0.7`. Id **D68**.

## P11. Concreciones para el bloque C (sin ids nuevos)

- **C8 (`modes.careful`):** dos niveles (`deny` para lo catastrófico, `ask` para lo destructivo), fallar cerrado si
  no se puede leer la entrada y no disparar por un `rm -rf` dentro de un `-m "…"`.
- **C1/C3:** cada pregunta dice si es de ida (siempre se pregunta) o de vuelta (se puede dar por respondida con la
  recomendación).
- **C7 (`modes.tokens`):** un paso solo entra si `gastado + reservado + previsto + margen <= tope`, con un modo que
  solo observa.
- **Versión:** `0.7`, dentro de sus tareas.

## P12. Pruebas: registro de inestables y tamaño del diff

- **Qué cambia:**
  - **E35 (`0.7`):** un test que falla y pasa al reintentar se apunta como inestable (`.git/gw/flaky.jsonl`) y el
    check lo dice; tras N veces (clave) se propone arreglarlo. Esta rama ya tuvo tres pruebas inestables en la `0.5.1`.
  - **D43 (`0.6`):** el aviso de tamaño de commit usa umbrales por escalones (claves en `gw.json`) y compara los
    archivos tocados con `Files` de la ficha cuando exista.
- **Versión:** la indicada en cada punto.

## P13. Pruebas de comportamiento de las skills

- **Fuente:** los evals por plugin de una referencia (`claude plugin eval`, con correctores en markdown).
- **Qué cambia:** además de `evals/triggers.json` (si una skill se dispara), un par de casos por skill que comprueban
  lo que hace. Cuestan tokens: corren a mano antes de una versión, no en el check.
- **Versión:** `0.9`. Id **E36**.

## Descartado

- El agente de navegador: archivado y sin aporte.
- El prompt contra la sobreingeniería: su «si dudas, pregunta» choca con C10, y las skills van en inglés; solo se toma
  la metodología (P5) y el control de alcance (P3, P12).
- El código de la referencia sin licencia: solo ideas, reescritas en Python estándar y bash 3.2.
- Multi-host, memoria compartida entre proyectos, plantillas de `SKILL.md` generadas (coste sin problema que
  resolver) y los recibos de salida (los cubre E2).
- La publicación del usuario no pide tareas aparte: casi todos sus puntos ya tienen tarea (bitácora, D65, B21,
  bloque C, `gw-harvest`, `gw-update`). Sirve de material para A10 (hoja del flujo) y `gw-media-content`.

## Preguntas al usuario y sus respuestas (2026-11-08)

1. **«CDD»:** el usuario lo define como el razonamiento y las decisiones de cada agente, por separado; nombre de la
   ficha: «task record», en `docs/tasks/<id>.md`, con el **decision log** por agente dentro.
2. **D50:** la ficha lo absorbe y el commit solo resume. **Sí.**
3. **Cuándo es obligatoria la ficha:** en todo `feat`, `fix` y `hotfix` con código, y en `refactor` grande (D43); no
   en `docs`, `WIP` ni la marca de revisión. Tipos y umbral, claves de `gw.json`. **Sí.**
4. **Reparto:** P1, P2, P3, P7, P10, P11, E32 y E35 a la `0.7`; P5 y D43 en la `0.6`; P9, P13 y el resto de P6 a la
   `0.9`; P4 se diseña en `I-lifecycle.md` y sale en la `1.2`; P8, en el diseño del MMC. **Sí.**
5. **Aprobaciones de P4:** trailer `Approved-by: <rol> <usuario>` en el commit de promoción, comprobado por el
   `pre-push` del entorno destino. **Sí.**
