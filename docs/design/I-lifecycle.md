# I. Ciclo de vida y autoridad: ficha de tarea, hecho por entorno y aprobaciones

**Estado:** abierto (2026-11-08). Las decisiones de base las aprobó el usuario este día («Apruebo todo lo que
comentas»); las preguntas del final se responden en una sesión de `grilling` antes de implementar nada del bloque
(regla de la sesión de diseño: el diseño se cierra antes del desarrollo). Las referencias externas que inspiraron
partes de esto se leyeron como ideas, sin copiar código, y no se nombran aquí (usuario, 2026-11-08).

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
   commit a la ficha; el commit solo resume.
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
                  "sections": ["Goal", "Scope", "Acceptance", "Files", "Decision log", "Change log", "Verification"] },
  "scopeGuard": { "mode": "warn" },
  "riskPaths": [],
  "environments": [],
  "roles": [],
  "approvals": { "trailer": "Approved-by", "requireFrom": "uat" },
  "flaky": { "path": ".git/gw/flaky.jsonl", "proposeFixAfter": 3 },
  "changelogFragments": { "dir": "changelog.d" }
}
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
4. **Una ficha, varios agentes en paralelo:** los worktrees `agent/<id>-<tema>` de la misma tarea chocan en
   `docs/tasks/<id>.md`. El decision log es de solo añadir, con una sección por agente y commit; `merge-branch.sh`
   resuelve ese archivo por unión de secciones (o `merge=union` solo para esa ruta). A decidir en el `grilling`.
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
11. **Los documentos de diseño y la investigación anteriores nombran repos externos** (`design/README.md`,
    `A-framework.md`, `C-questions.md`, `D-git.md`, `docs/research/ref-*.md`, uno en el propio nombre de archivo). La
    regla de no nombrarlos (usuario, 2026-11-08) se aplica desde ahora a lo nuevo; limpiar lo anterior es una tarea
    aparte (pregunta 8).

## Preguntas para el `grilling` (se responden por número)

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
