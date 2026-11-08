# I. Ciclo de vida y autoridad: ficha de tarea, hecho por entorno y aprobaciones

**Estado:** cerrado (2026-11-08). Las decisiones de base las aprobó el usuario este día («Apruebo todo lo que
comentas») y las diez preguntas del final se respondieron en la sesión de `grilling` del mismo día (sección
«Respuestas del `grilling`»): nada del bloque se implementa sin pasar por ellas. Las referencias externas que
inspiraron partes de esto se leyeron como ideas, sin copiar código. **Regla de citas** (usuario, 2026-11-08, Q8):
se citan, con enlace, los repos **públicos** que ayudaron; nunca nombres de empresa ni datos de repos privados (E37
limpia los documentos anteriores y `names-check.py` lo vigila con `privateNames`).

Fuentes: las notas del usuario repartidas en [`2026-11-08-notes-and-references.md`](../proposals/2026-11-08-notes-and-references.md)
(H17) y el análisis de tres partes de esa sesión: prácticas clásicas de «hecho» y control de calidad, principios de
desarrollo con agentes (`docs/research/ref-*.md`), y lo que el flujo ya tiene ([`agent-map.md`](../agent-map.md)).

## Por qué un bloque nuevo

El flujo de la `0.5` es un flujo de **relevos y disciplina de subida**: no perder trabajo, no subir sin revisar ni en
rojo, medir, repartir a subagentes. Es un flujo de una persona con agentes y un solo entorno real (`main` y ramas).
Los bloques C (preguntas y modos), D (entornos D9, `rc` D10, roles D17) y G (MMC G8) ya diseñaron piezas sueltas de
lo que falta. Este bloque **une esas piezas** con lo nuevo (ficha de tarea, hecho por entorno, aprobaciones) y reabre
D9, D17 y G8 desde aquí. Sin él, cada pieza se implementaría con su propia idea de «hecho».

## Principio que cambia

**«Hecho» lo declara un script o un rol, nunca el autor.** Con autores humanos, el autor sabía cuándo había
acabado; un agente dice «hecho» y «todos los tests pasan» con facilidad y su sesión desaparece con el razonamiento.
Por eso:

- lo que se quiere se escribe antes y de forma comprobable (ficha con criterios de aceptación);
- el razonamiento se persiste (decision log por agente), no se recuerda;
- cada entorno dice qué exige para dar algo por hecho y quién puede declararlo;
- la autoridad es técnica (protección de ramas, sin credenciales de entornos altos para el agente), no textual.

Las prácticas clásicas (riesgo = probabilidad × radio × detección × recuperación, autor ≠ aprobador, mismo sha
promovido entre entornos, vuelta atrás ensayada, observabilidad, postmortems sin culpa) siguen valiendo: controlan el
producto. Lo de arriba controla además al autor. El flujo hace las dos cosas.

## Decisiones tomadas (usuario, 2026-11-08)

1. **Ficha de tarea («task record»):** `docs/tasks/<id>.md`, una por id del roadmap que lleve código. Reúne el SDD
   (qué se quiere y qué no, criterios de aceptación comprobables, archivos previstos) y el **decision log** por agente
   (lo que el usuario llamó «CDD»): cada agente que toca la tarea añade su entrada con por qué ese código para esos
   criterios, qué camino tomó, qué cambió y por qué. Absorbe **D50**: `Técnica:` y `Problemas:` salen del cuerpo del
   commit a la ficha; el commit solo resume. (Q4 bis: el decision log es una carpeta `docs/tasks/<id>/` con un archivo
   por entrada, no una sección del archivo del contrato.)
2. **Obligatoria** en `feat`, `fix` y `hotfix` con código (tipos configurables); no en `docs`, `WIP:` ni la marca de
   revisión. El `commit-msg` comprueba que el commit toque la ficha con una entrada nueva.
3. **Cuatro modos de trabajo:** SDD siempre (toda tarea con código tiene ficha); DDD cuando hay dominio que modelar
   (`domain-modeling`); TDD cuando el comportamiento se puede expresar en tests (`red-without-fix.sh`); exploración en
   rama `spike/<tema>` sin ficha ni `Refs:`, que no se fusiona en una rama de trabajo: se convierte en ficha o se tira.
4. **Alcance congelado:** tocar un archivo fuera de `Files` de la ficha avisa (bloquea con `modes.questions`
   restrictivo) y obliga a apuntarlo en el change log; un requisito nuevo es otra tarea.
5. **Hecho por entorno:** cada entorno de `environments` (D9) declara qué exige y quién lo declara. **Fusionar en
   cualquier entorno que no sea el de desarrollo lo hace una persona con rol**, nunca el agente.
6. **Aprobaciones en el repo:** trailer `Approved-by: <rol> <usuario>` en el commit de promoción; el `pre-push` del
   entorno destino lo exige. Un archivo aparte solo si hace falta más texto.
7. **Entornos como opción:** sin `environments` declarados, todo sigue como hoy (`main` y ramas, rol `ADMIN`, marca
   de `reviewed.sh`). El flujo ofrece la escalera, no la impone.
8. **Lo clásico del proyecto** (observabilidad, banderas, copias, vuelta atrás) no es del flujo: el entorno de
   producción **exige que se declare**, con fecha, antes de admitir una promoción.
9. **Todo configurable desde el MMC:** cada umbral, ruta y comportamiento de este bloque es una clave de `gw.json`
   con valor por defecto, leída por `config.py` y explicada en `docs/es/config.md`.
10. **Orden:** se diseña este bloque entero (preguntas de abajo) antes de implementar nada de la `0.7` que lo toque
    (`commit-msg`, D50, D43, `trace.py`).

## Las cinco capas del diseño destino

| Capa | Qué hace | Sección de `gw.json` |
|---|---|---|
| 1. Contratos | roadmap con ids → ficha (SDD, criterios, archivos, riesgo) → decision log → preguntas persistidas (C1) | `taskRecord`, `questions`, `riskPaths` |
| 2. Guardas deterministas | ganchos y scripts: alcance, formato de commit, secretos, check en verde, marca, hecho de cada paso; fallan cerrados | `modes`, `scopeGuard`, `check`, `protectedPaths` |
| 3. Entornos y autoridad | rama, desde dónde se promueve (mismo sha), qué exige, quién declara, qué declaraciones del proyecto necesita; aprobaciones como trailers; GitHub pone la barrera dura | `environments`, `roles`, `approvals` |
| 4. Medición | ledger por modelo, skill, tarea y entorno: tokens, coste, duración, intentos, errores, CI y fallos en producción atribuibles; el flujo informa, el humano elige | `metrics` |
| 5. MMC | ve y edita las cuatro capas por `config.py`; nunca aprueba ni fusiona | `mmc` |

## Claves nuevas (borrador; valores por defecto = comportamiento de hoy)

Ninguna existe aún en `config.py` ni en `docs/es/config.md` (comprobado el 2026-11-08); `environments`, `roles` y
`modes` estaban previstas por D9, D17 y C4 y se concretan aquí.

```json
{
  "taskRecord": { "path": "docs/tasks", "requiredFor": ["feat", "fix", "hotfix"], "refactorMinLines": 400,
                  "sections": ["Goal", "Scope", "Acceptance", "Files", "Change log", "Verification"],
                  "logSections": ["Por qué", "Alternativas", "Cambió porque"] },
  "scopeGuard": { "mode": "warn" },
  "riskPaths": [],
  "environments": [],
  "roles": [],
  "approvals": { "trailer": "Approved-by", "requireFrom": "uat", "maxAgeDays": 90 },
  "flaky": { "path": ".git/gw/flaky.jsonl", "proposeFixAfter": 3 },
  "changelogFragments": { "dir": "changelog.d" },
  "privateNames": []
}
```

Tras el `grilling`: el decision log no es una sección de `sections` sino la carpeta `docs/tasks/<id>/` (un archivo
por entrada, con los apartados de `logSections`); `approvals.maxAgeDays` caduca las declaraciones de `prod` (Q7);
`privateNames` lista los nombres de proyectos privados que `names-check.py` no deja aparecer en `docs/design`,
`docs/research` ni en lo que entra en la release (Q12). Fragmento del ejemplo anterior con la clave vieja:

```json
{ "taskRecord": { "sections": ["…", "Decision log", "…"] } }
```

Forma de un entorno (ejemplo con tres; con la lista vacía el flujo se comporta como hoy):

```json
{ "name": "prod", "branch": "main", "promoteFrom": "uat", "sameSha": true,
  "done": ["check", "ci", "review-mark", "acceptance"], "approvers": ["deploy-master"],
  "requires": ["rollbackPlan", "observability", "smokeTest"] }
```

## Fricciones encontradas al contrastar (para que no sorprendan al implementar)

1. **El botón de fusión de GitHub no pasa por ningún gancho.** Un trailer `Approved-by:` solo puede exigirlo el
   `pre-push` si la promoción se hace **en local** por la persona con rol (`promote.py`, que crea el merge con el
   trailer y sube). Consecuencia: la fusión por GitHub solo se permite en el entorno de desarrollo; en los demás, la
   barrera dura es la protección de ramas (revisores requeridos, `CODEOWNERS`), y el flujo genera y comprueba esa
   configuración en modo lectura (G8 ya lo decía: el MMC dice cómo ponerla, no la toca).
2. **El usuario de git es falsificable.** D17 comprueba `user.name`/`user.email` por entorno: es una capa de aviso,
   no de autoridad. La autoridad real es la cuenta de GitHub que empuja (protección de ramas). Hay que decirlo así en
   D17 y en `docs/es/`.
3. **La sesión en la nube no puede subir etiquetas (403 del proxy)** ni, por lo anterior, promover: las promociones
   y los `rc` (D10) son siempre de una sesión local o de una persona.
4. **Una ficha, varios agentes en paralelo:** los worktrees `agent/<id>-<tema>` de la misma tarea chocarían en
   `docs/tasks/<id>.md` si el decision log viviera ahí. Trabajar cada agente en su rama aísla el trabajo pero no evita
   el choque (aparece al fusionar); lo evita que no haya archivo compartido: el decision log es una carpeta con un
   archivo por entrada que cada agente crea y nunca edita (Q4 bis). Un conflicto en el archivo del contrato es real y
   para la fusión, como cualquier otro.
5. **La ficha y la bitácora no pueden repetir el dato** («un dato, un sitio»): la fila de la bitácora (`logRows`)
   guarda estado y siguiente paso; la ficha, contenido (criterios, decisiones, verificación); `trace.py` (D14) los
   junta. D43 (tamaño de commit) compara con `Files` cuando la ficha exista.
6. **El guard de alcance por `PreToolUse` solo existe en Claude Code.** Otros agentes (D7, `0.8`) no lo tienen; el
   respaldo determinista es el `pre-commit`, que compara los archivos del commit con `Files`.
7. **`hotfix` no es tipo de `commitFormat` hoy** (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
   `build`, `ci`, `chore`, `revert`): hay que añadirlo a la lista y a `version.py` (parche).
8. **Los merges están exentos de `Refs:`** (D12) y el `commit-msg` exige que el último párrafo solo tenga trailers:
   `Approved-by:` encaja ahí; `merge-branch.sh` ya copia `Refs:` al merge y copiará el trailer de aprobación.
9. **`reviewed.sh` ya es la aprobación del rol `ADMIN` para `main`** cuando no hay entornos: en el modelo nuevo la
   marca debería apuntar quién la puso (D17), sin cambiar su uso.
10. **`AGENTS.md` tiene tope de líneas** (`instructionLines`: aviso 150, fallo 250; hoy 117): el principio nuevo
    entra, pero lo que sea comprobable va a un gancho, no a prosa.
11. **Los documentos de diseño y la investigación anteriores nombran repos externos.** Contrastado el 2026-11-08:
    `docs/design`, `docs/research` y `docs/proposals` citan 33 repos de GitHub, todos públicos (se quedan, con su
    enlace); lo que no puede salir son los nombres de los proyectos privados del usuario en `A-framework.md`,
    `D-git.md`, `E-quality.md`, `H-roadmap.md`, `real-cases.md` y `social-media.md`. Limpiarlos es E37 (pregunta 8).

## Respuestas del `grilling` (usuario, 2026-11-08: «todo aprobado» en las tres rondas)

1. **Plantilla:** seis secciones obligatorias y en orden en `docs/tasks/<id>.md`: `Goal`, `Scope`, `Acceptance`,
   `Files`, `Change log`, `Verification` (`taskRecord.sections`); una sección vacía lleva «—»; sin sección de preguntas
   abiertas propia (una línea con enlace a `docs/questions.md`, C1). El decision log va aparte (4 bis).
2. **Entrada del decision log:** un archivo `docs/tasks/<id>/<fecha>-<agente>-<sha7>.md` con cabecera
   `# <fecha> · <skill o "session"> · <commit>` y tres apartados fijos (`taskRecord.logSections`): «Por qué»,
   «Alternativas», «Cambió porque» (o «—»). El `commit-msg` comprueba solo forma (archivo nuevo, id en la cabecera,
   los tres apartados); el sha lo rellena un gancho `post-commit`; la calidad la pide `REVIEW.md` al revisor.
3. **Cierre de tarea:** `handoff.py close-row <id>` (hoy toma una rama; pasa a aceptar el id) exige todas las casillas
   de `Acceptance` marcadas y `Verification` con el commit y la orden; se niega a marcar una casilla que no nombre un
   test (`tests/test_X.py::Caso`) o una sección `== …` de `check.sh`. Lo corre el agente; lo declara el script.
4. **Conflictos:** sin `merge=union` ni resolución propia en `merge-branch.sh`. **4 bis:** contrato en
   `docs/tasks/<id>.md`, decision log en la carpeta `docs/tasks/<id>/`, un archivo por entrada que nadie edita;
   `trace.py` concatena la carpeta por fecha; el `commit-msg` solo comprueba que el commit **añada** un archivo ahí.
5. **Promoción:** `promote.py <env>` como orden única (hecho del destino, mismo sha desde `promoteFrom`, aprobadores
   con rol, merge con `Approved-by:`, etiqueta `rc`/final, subida) con `--dry-run`; el botón de GitHub solo para el
   entorno de desarrollo; toda promoción es local o de una persona.
6. **Rutas de riesgo** (`riskPaths`): tocar una exige en la ficha una sección `Rollback` rellena, un aprobador humano
   (`Approved-by:`) aunque el entorno sea el de desarrollo y un test nombrado en `Verification` por ruta tocada; lo
   comprueba el `pre-push`. La lista empieza vacía.
7. **Declaraciones de `prod`:** un archivo por declaración en `docs/records/declarations/<nombre>.md` con fecha,
   responsable y texto libre; `promote.py` exige que exista y no haya caducado (`approvals.maxAgeDays`, 90).
8. **Repos externos:** se citan los públicos que ayudaron, con enlace; nunca nombres de empresa ni datos de repos
   privados. **8 bis (E37, `0.9`):** quitar de `docs/design` y `docs/research` los nombres de los proyectos privados
   del usuario (→ «proyecto piloto A/B») y dejar las citas públicas; bitácora y propuestas se quedan como están (trabajo
   interno); en esa tarea se decide si `AGENTS.md` los nombra por la clave `privateNames` en vez de en texto. La regla,
   en una línea de `AGENTS.md`; lo comprobable, en `names-check.py` con `privateNames`.
9. **D50:** «absorbida por C11», `hecho` cuando C11 lo esté; el id no se reutiliza.
10. **Versiones:** `0.7`: C11 (primero: toca `commit-msg`, D43 y `trace.py`), luego C13 y C12 (dependen de la ficha),
    A11, D68, E32, E33, E35; `1.2`: D67, I1, I2 con D9, D10, D17 y G8 (I1 necesita el `Approved-by:` y el `pre-push`
    por entorno de D67); `0.9`: E34, E36, E37.
11. **Tipo `hotfix`** (fricción 7): D69, en la `0.5.2`: entra en `commitFormat` y `version.py` (parche) para que los
    proyectos en `0.5` acepten el tipo antes de C11.
12. **E37** apuntada en la `0.9` (8 bis).

## Preguntas para el `grilling` (respondidas arriba; se conservan como registro)

1. **Plantilla de la ficha:** ¿las siete secciones de arriba, o menos? **Rec.:** las siete; `Open questions` enlaza
   con `docs/questions.md` (C1) en vez de duplicarlo.
2. **Entrada del decision log:** ¿qué campos mínimos? **Rec.:** `### <fecha> <skill o "session"> <commit>` y debajo
   «Por qué», «Alternativas», «Cambió porque»; el `commit-msg` solo comprueba que haya una entrada nueva con el sha
   pendiente (`HEAD` se rellena en el gancho), no su calidad; `REVIEW.md` pide la calidad como regla de criterio.
3. **Qué cierra una tarea:** ¿quién marca la fila `hecho`? **Rec.:** `handoff.py close-row` exige todas las casillas
   de aceptación marcadas y la sección de verificación con commit; lo corre el agente, pero no puede marcar casillas
   que no tengan test o check nombrado.
4. **Conflictos de la ficha** entre worktrees (fricción 4). **Rec.:** secciones por agente y `merge=union` solo para
   `docs/tasks/*.md`, con test.
5. **Promoción:** ¿`promote.py <env>` como orden única (comprueba hecho, mismo sha, aprobadores, crea el merge con
   el trailer y la etiqueta `rc`/final, sube)? **Rec.:** sí; el botón de GitHub queda para el entorno de desarrollo.
6. **Rutas de riesgo** (`riskPaths`: migraciones, auth, pagos): ¿qué añaden? **Rec.:** la ficha exige «plan de vuelta
   atrás» y un aprobador humano aunque el entorno sea el de desarrollo.
7. **Declaraciones de `prod`** (`requires`): ¿archivo por declaración con fecha en `docs/records/`? **Rec.:** sí,
   `docs/records/declarations/<nombre>.md` con fecha y responsable; `promote.py` exige que exista y no caduque
   (`maxAgeDays`, clave).
8. **Repos externos en los documentos anteriores** (fricción 11): ¿se limpian ahora (una tarea E, renombrando el
   archivo de investigación) o se dejan como historia? **Rec.:** una tarea en la `0.9` con E31.
9. **Qué queda en D50:** ¿se cierra como absorbida o se renumera? **Rec.:** su fila dice «absorbida por C11» y D50
   no se reutiliza.
10. **Versión del bloque:** **Rec.:** `0.7`: C11 (ficha), A11 (modos), C12 (`spike/`), C13 (alcance), D68
    (fragmentos de changelog), E32, E33, E35; `1.2`: D67 (hecho por entorno, `promote.py`), I1 (`riskPaths`), I2
    (declaraciones de `prod`), con D9, D10, D17 y G8; `0.9`: E34, E36.
