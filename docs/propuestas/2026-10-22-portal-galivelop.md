# Harvest portal-galivelop — 2026-10-22

De `e3f305811ffb` a `673602b` (`scripts/recoger.py`, 14 commits). Es la primera aplicación de la versión empaquetada
(v0.1.0, con `aplicar.py`) a un proyecto que ya tenía su copia del flujo; el flujo nació en Tarkor (el piloto de
v0.1.0): 26 fricciones (F1-F26) en
`docs/registros/piloto-galivelop-workflow.md` y una retro con 4 ideas más
(`docs/registros/retro-2026-10-22-piloto-galivelop-workflow.md`). Cada una se ha comprobado contra nuestro código
actual (`b994f99`); lo ya resuelto o no reproducible va a «Ya está aquí», lo del portal a «Se queda en el proyecto».
No se repite nada de las recogidas anteriores ni de `2026-10-21-reparto.md`.

Hallazgos de la propia recogida:

- **Una guardia falla abierta (P1), reproducido.** En un repo de prueba con `aplicar.py --init`, un commit que añade
  `".*"` a `content` y toca `src/a.js` se subió con `git push origin HEAD:main` sin marca de revisión: «pre-push: all
  green», `main` avanzó. No es un caso teórico: es la regla que protege `main`.
- **Los «cambios locales» de `opt-tokens` y `orchestrate-dealer` no son ediciones del portal** (P2). `git log` del portal
  solo las toca en la copia (`84b27d1`). Son una **copia más vieja con la misma etiqueta `0.1.0`**: el portal copió de
  `603ca36` y desde entonces `main` cambió esas skills (`7112486`, `d01091e`, `cd4b4cd`) sin subir la versión. Lo que el
  diff muestra como «lo que el portal quitó» (revisión del código que un subagente sube en la rama, tandas de 6-8,
  `SendMessage`, estado intermedio fuera de git, `recuperar.py --estado` en el encargo) es lo que el portal aún **no
  tiene**; nada suyo hay que subir. `recoger.py` lo informa como «skills changed in the project» y `aplicar.py --check`
  como «v0.1.0 with local edits»: las dos lecturas engañan.
- **`recoger.py` no vio `piloto-galivelop-workflow.md`** (P21): solo busca `## For Galivelop-workflow` en `retro-*.md`;
  la mayor lista de fricciones del piloto estaba en otro archivo.

## P1. `pre-push` y el gancho de PR leen la política de la base, no del commit que se sube (F18)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F18, «Fase 1» hallazgo 1 y «Fase 3») @ 673602b (retro); verificado en `templates/githooks/pre-push` (`cfg_at "$local_sha"`, líneas 97-98 y 168) y `scripts/es-codigo.sh` (lee `content` de `$rev` = el commit que se sube) y reproducido (arriba)
- **What changes:** `content`, `check`, `protectedBranch` y `reviewMark` se leen del commit **remoto** de la rama protegida (la base; en el primer push, del commit subido con un aviso) y `.claude/gw.json` cuenta siempre como código. El mismo criterio en `revision-antes-de-main.sh` (marca y `content`). Un cambio legítimo de la política entra con marca como cualquier código. Caso en los tests: commit que amplía `content` o pone `check` a `true` y toca código, rechazado; el mismo cambio con marca, aceptado.
- **Why it is general:** hoy quien puede subir un commit puede apagar la regla en ese mismo commit; también lo hace sin querer una tarea que publica sola (el portal tiene una). Contradice la regla «gancho de subida comprueba el commit que se sube» solo en su letra: se comprueba el commit, pero con la política de la base. Dejar de leer del árbol de trabajo (lo que ya se hace) no basta.
- **Version bump:** minor (cambia qué se rechaza)
- **Status:** propuesta

## P2. Mismo número de versión con contenido distinto: `--check`, `doctor` y `recoger` no lo distinguen de una edición local

- **Source:** `python3 scripts/recoger.py --diff opt-tokens|orchestrate-dealer /home/user/zeldris/portal-galivelop` @ 673602b; `scripts/aplicar.py` (`differs: v0.1.0 with local edits`) y `scripts/doctor.py` (`check_skills`, solo compara `metadata.version`) (skill, script)
- **What changes:** (a) regla de la fase de publicación: todo cambio en un archivo copiable entre dos subidas a `main` sube la versión (aunque sea patch); `version.py` lo comprueba contra la última etiqueta (`git diff <tag> -- skills templates scripts` sin cambio de versión → exit 1). (b) `aplicar.py --check` y `recoger.py` dicen «difiere de la v0.1.0 del flujo: ediciones locales **o** una copia anterior de esa versión» y, con `--diff`, el comando para verlo; `recoger.py` no lista como «cambiada en el proyecto» una skill cuyo cuerpo coincide con una versión anterior del flujo (`git log --follow`). (c) `doctor.py` compara el contenido de las copias con el del flujo (hash en una línea de `gw.json` o en la cabecera) y avisa de **deriva** en archivos copiados, que `/gw-update --update` sobrescribiría: «tus cambios a `X` se pierden; pásalos a las notas del proyecto o propónlos con `gw-harvest`».
- **Why it is general:** cualquier proyecto que copió entre dos subidas con la misma versión ve «ediciones locales» que no hizo, y una edición local real (que `doctor` da por buena: «skills OK» solo por la versión) se pierde en silencio al actualizar. El resultado de este harvest estuvo a punto de proponer como mejora del portal lo que era texto viejo del flujo.
- **Version bump:** minor
- **Status:** propuesta

## P3. `aplicar.py` y `doctor.py` comprueban con `git check-ignore` que lo del flujo no está ignorado (F3)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F3; retro «Qué costó») @ 673602b (retro); `scripts/doctor.py` y `scripts/aplicar.py` no llaman a `check-ignore`
- **What changes:** `doctor.py` hace `git check-ignore -q` sobre `.claude/gw.json`, `.claude/gw/scripts/config.py`, `.claude/settings.json`, `.claude/skills/<una skill del flujo>/SKILL.md` y `.githooks/pre-push`; si alguno está ignorado, FAIL con la línea `!…` a añadir al `.gitignore`. `aplicar.py` hace lo mismo tras escribir y lo imprime en el resumen (antes de la orden de commit sugerida).
- **Why it is general:** un `.gitignore` con `.claude/*` es habitual; el primer commit sale sin config ni scripts y el `pre-push` lo rechaza tarde. En el portal solo se vio a ojo.
- **Version bump:** minor
- **Status:** propuesta

## P4. La `retro` del flujo la puede lanzar el agente que la necesita (F24)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F24) @ 673602b (retro); `skills/retro/SKILL.md` (`disable-model-invocation: true`), `skills/selector/SKILL.md` («Claude runs it»), `templates/es/AGENTS.md` fase 2 y `scripts/revisado.sh:61`
- **What changes:** o se quita `disable-model-invocation` de `retro` (es lo que el portal tenía antes y cuadra con `AGENTS.md`, `selector` y `revisado.sh` con `requireRetro`), o se cambian esos tres textos para decir «la persona escribe `/retro`; el agente se lo pide al cerrar la fase 1». Recomendado lo primero: sus propuestas ya pasan siempre por la persona.
- **Why it is general:** hoy el flujo se contradice: tres piezas cuentan con que Claude la lance y la skill lo impide. El portal tuvo que anotar la diferencia en su `AGENTS.md`.
- **Version bump:** patch
- **Status:** propuesta

## P5. `recuperar.py --estado` se cuelga con la entrada estándar abierta sin datos (F17)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F17) @ 673602b (retro); `scripts/recuperar.py` `hook_transcript()` (solo mira `isatty()`); reproducido: `sleep 3 | python3 …/recuperar.py --estado` pasa de 2 s (exit 124) y con `| head` da `BrokenPipeError`
- **What changes:** leer la entrada estándar solo con `select` de timeout corto (0,2 s) o con una bandera explícita (`--estado --hook` en la plantilla de `settings.json`); capturar `BrokenPipeError` al imprimir (sale 0 en silencio). El caso, en los tests.
- **Why it is general:** `isatty()` cubre la terminal, no la herramienta Bash de un agente (tubería abierta) ni un `| head`; `CLAUDE.md` manda correrlo a mano al compactar. Un `--estado` colgado en el momento de la compactación es justo cuando más falta hace.
- **Version bump:** patch
- **Status:** propuesta

## P6. Dónde van las notas del proyecto para cada skill copiada (F8)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F8; «For Galivelop-workflow») @ 673602b (retro); hoy solo `opt-tokens` (`.claude/gw/opt-tokens.md`), `opt-ai` (`.claude/gw/opt-ai.md`), `selector` (`selector.cases`) y `grilling` (`designReferences`) tienen dónde
- **What changes:** convención única: `.claude/gw/skills/<nombre>.md`, del proyecto (nunca se sobrescribe, como las notas existentes), y cada skill con criterio local (`research`, `pr`, `prototype`, `retro`, `domain-modeling`…) empieza con «si existe `.claude/gw/skills/<nombre>.md`, léelo antes de seguir». `gw-update` no lo toca; `aplicar.md` §3 lo dice al migrar notas «En este repositorio» de una copia anterior.
- **Why it is general:** el portal tenía nota propia en 9 skills; al pasar a las copias del flujo las pasó a `AGENTS.md`, que la skill no lee al usarla. Cualquier proyecto con skills del flujo tiene notas locales y hoy o edita la copia (deriva, P2) o las pierde.
- **Version bump:** minor
- **Status:** propuesta

## P7. `doctor.py` cuenta los `*.gw-nuevo` pendientes y las entradas duplicadas de `settings.json` (F4, F5)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F4, F5) @ 673602b (retro); `scripts/doctor.py` `check_skills` («skills OK» con 14 `.gw-nuevo` sin revisar) y `check_settings`
- **What changes:** (a) `doctor.py` busca `*.gw-nuevo` (`git ls-files -o --exclude-standard`) y da WARN con la lista y la orden `git diff --no-index`; sin «skills OK» mientras haya alguno. (b) en `check_settings`, WARN si un evento del flujo (`SessionStart`, `PreToolUse`) tiene entradas que apuntan a scripts fuera de `.claude/gw/scripts/` (posible copia anterior que corre dos veces); `aplicar.py` las lista al fusionar `settings.json`.
- **Why it is general:** todo proyecto existente deja `.gw-nuevo` y casi todos traen ganchos propios o de una copia anterior; el criterio de fin del paso 3 de `aplicar.md` («no queda ningún `.gw-nuevo`») es justo lo que `doctor` no comprueba. En el portal «hooks look right» con dos `session-start` y dos ganchos de PR.
- **Version bump:** minor
- **Status:** propuesta

## P8. `aplicar.py --adopt`: reconocer una copia anterior del flujo sin versión (F2)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F2) @ 673602b (retro); `scripts/aplicar.py` (propiedad por `galivelop-workflow vX` o `metadata.version`) y `docs/es/aplicar.md` «Proyectos existentes» (no lo cubre)
- **What changes:** `--adopt` (o `--adopt <skill>...`): una skill del mismo nombre que una del flujo, sin versión, se sustituye tras imprimir el diff y lo que tuviera de más se lista para llevarlo a las notas del proyecto (P6). Sin `--adopt`, el plan los agrupa en una sola línea («14 skills sin versión que coinciden por nombre; `--adopt` para sustituirlas») en vez de 14 `.gw-nuevo`. Un párrafo en «Proyectos existentes» de `aplicar.md`.
- **Why it is general:** los proyectos que tomaron el flujo de otro repo antes de existir `Galivelop-workflow` (Tarkor, VeriNews, el portal) son exactamente los primeros usuarios.
- **Version bump:** minor
- **Status:** propuesta

## P9. `content` por defecto demasiado ancho (F19)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F19, «Fase 1» hallazgos 2, 3 y 5) @ 673602b (retro); `templates/gw.json:14` (`["^docs/", "\\.md$", "^\\.claude/skills/"]`)
- **What changes:** valor por defecto `["^docs/", "^(README|GLOSSARY|REVIEW|CLAUDE|AGENTS)\\.md$", "^\\.claude/skills/.*\\.md$"]` (`\.md$` acotado a documentación y a los `.md` de la raíz; solo los `.md` de las skills, no sus scripts ni `agents/*.yaml`); `aplicar.md` §1 lo explica en una línea («lo que sea `content` sube sin marca: no pongas lo que un agente lee como instrucciones ni scripts»); con `docs/es/config.md` y `docs/es/patrones.md` alineados.
- **Why it is general:** con el valor actual `.claude/skills/opt-tokens/scripts/medir.py` es «contenido» y un `AGENTS.md` en cualquier carpeta también (instrucciones de agentes = código a efectos de riesgo). La revisión lo cazó en el portal; un check no.
- **Version bump:** minor
- **Status:** propuesta

## P10. `--init` con las claves que el proyecto decide; `requireRetro` entra en la tabla del paso 1 (F6, F7)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F6, F7) @ 673602b (retro); `scripts/aplicar.py` (sin esas banderas), `templates/gw.json:13` (`requireRetro: true`) y `docs/es/config.md:39` (dice que el valor por defecto es `false` y que `--init` pone `true`)
- **What changes:** banderas `--visible-language` (repetible), `--design-reference` (repetible), `--require-retro true|false` en `--init`; la tabla del paso 1 de `aplicar.md` pregunta «¿`/retro` en cada subida a la rama protegida o solo en cambios grandes?» y apunta `requireRetro`; el mismo valor en `templates/gw.json` y en el esquema (hoy dos «valores por defecto» distintos).
- **Why it is general:** `requireRetro: true` bloquea cualquier cambio pequeño de código en un proyecto cuya regla es «retro solo en cambios grandes»; hoy se descubre al primer `revisado.sh`. Las otras claves obligan a editar `gw.json` a mano tras `--init`.
- **Version bump:** minor
- **Status:** propuesta

## P11. Aplicar o actualizar el flujo se lee con un subagente (F1, F25 y las ideas de la retro)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F1, F25) y `retro-2026-10-22-piloto-galivelop-workflow.md` («For Galivelop-workflow», «Cómo rindieron las skills») @ 673602b (retro); `skills/gw-init/SKILL.md` y `skills/selector/SKILL.md` (fila «Bring something from another repo» existe, `gw-init` no la cita), `skills/opt-tokens/SKILL.md`
- **What changes:** (a) `gw-init` y `aplicar.md` §0: el repo del flujo se lee con un subagente ligero vía `orchestrate-dealer`, que devuelve la tabla de decisiones del paso 1 y los conflictos con el proyecto, con rutas; la sesión principal solo decide. (b) `selector`: fila «Aplicar o actualizar el flujo» (`gw-init`, `gw-update`, `gw-doctor`) con modelo grande para decidir y ligero para leer. (c) `opt-tokens`: si el contexto medio pasa de ~150k (umbral de `orchestrate-dealer`) el informe lo dice y lista las lecturas grandes que debió hacer un subagente. (d) `aplicar.md` §0 y `problemas.md`: leer el flujo en la nube sin que `add_repo` lo deje como carpeta de trabajo y cargue su `CLAUDE.md` (p. ej. `git clone` directo si es público, o `register_repo_root` no; `add_repo` puede dar una ruta en minúsculas que no existe).
- **Why it is general:** medido: 62 llamadas, 171k de contexto medio, ~30k solo de guía y scripts leídos enteros; la fila que lo habría evitado existía y nadie la citó desde `gw-init`.
- **Version bump:** patch
- **Status:** propuesta

## P12. Paso 6 de `aplicar.md`: `git push --dry-run` y dos mensajes posibles (F15, F16)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F15, F16; «Qué fue bien») @ 673602b (retro); `docs/es/aplicar.md` §6 (líneas 156-169)
- **What changes:** la orden pasa a `git push --dry-run origin HEAD:<protectedBranch>` (el `pre-push` corre igual y no hay riesgo si fallara; el modo automático de Claude Code bloquea el push real como «Production Deploy»), y el criterio de fin acepta los dos rechazos: «the pushed commit has no review mark» (sin marca) o «code changed after the review mark» (con marca y código posterior). Mismo cambio en `docs/en/`.
- **Why it is general:** un proyecto con `reviewMark` previo nunca verá el mensaje que la guía exige, y el push real es lo que un agente en modo automático no puede lanzar.
- **Version bump:** patch
- **Status:** propuesta

## P13. `comprobar.yml` con la cadena de herramientas sin editar el archivo del flujo (F9)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F9) @ 673602b (retro); `templates/github/comprobar.yml` (cabecera pide añadir `setup-node`…) y `docs/es/aplicar.md` §5
- **What changes:** claves `ci.setup` y `ci.after` (listas de pasos de GitHub Actions como YAML en `gw.json`, o un `.github/gw-ci.yml` incluido por el workflow) que el proyecto rellena; `comprobar.yml` queda sin tocar y `aplicar.py --check` deja de dar «local edits» para siempre. Como mínimo, elegir `setup-node`/`setup-python`/`setup-java` según `package.json`, `pyproject.toml` o `pom.xml`.
- **Why it is general:** casi todo proyecto necesita su cadena de herramientas en CI; hoy toca editar un archivo del flujo, `--check` sale 1 para siempre y `/gw-update --update` borraría el cambio.
- **Version bump:** minor
- **Status:** propuesta

## P14. Patrones de test de `content` y de tareas programadas; un test que espera fallo comprueba el motivo (F14, F26 y la retro)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F14, F26) y `retro-2026-10-22-piloto-galivelop-workflow.md` (propuestas 1, 2 y 4; «Qué costó») @ 673602b (retro); `docs/es/patrones.md` (§ «Tarea semanal programada»), `templates/es/REVIEW.md`
- **What changes:** (a) `es-codigo.sh --explicar <ruta>...`: dice si cada ruta es código o contenido y qué regex la casa. (b) en `patrones.md`: ejemplo de test que fija `content`/`reviewMark` y clasifica rutas (defensa hasta P1; solo frena un cambio accidental) y que una tarea que publica sola reciba un prompt que sea «sigue `docs/runbooks/tarea-<nombre>.md`»: el prompt real se cambia con un commit revisado, no desde la conversación de la tarea (`update_trigger` lo rechaza desde otra sesión). (c) `REVIEW.md` y `AGENTS.md`: «un test que espera un fallo comprueba el motivo, no solo el código de salida» (el del portal pasaba sin esquema por la razón equivocada).
- **Why it is general:** cualquier proyecto con una tarea que publica sin revisión necesita las tres cosas; la tercera es un fallo típico de tests de ganchos.
- **Version bump:** patch
- **Status:** propuesta

## P15. `recuperar.py --estado` con las secciones que diga la config; `session-start.sh` reinstala si falta la carpeta (F20, F22)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F20, F22) @ 673602b (retro); `scripts/recuperar.py` `first_section()` y `scripts/session-start.sh` (sello `gw-install.sha`, líneas 120-143)
- **What changes:** (a) `logSections` en `gw.json` (lista de encabezados) o, por defecto, la primera sección y la que se llame «Pendiente»/«Pending»; (b) con `CLAUDE_CODE_REMOTE=true`, reinstalar si el sello coincide pero falta la carpeta de dependencias (`node_modules`, `.venv`, `vendor`, `target` según el archivo de bloqueo).
- **Why it is general:** el estado tras compactar es lo único que ve la sesión: si lo pendiente no está en la primera sección, no lo ve. Y un sello sin dependencias deja sin instalar en silencio.
- **Version bump:** patch
- **Status:** propuesta

## P16. `pre-push` busca marcadores de conflicto en `base..local`, no solo en lo nuevo (F21)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F21) @ 673602b (retro); `templates/githooks/pre-push` línea 104 (`rev-list … --not --remotes`) y 137-149
- **What changes:** al subir a la rama protegida, la búsqueda de marcadores y de `*.rej`/`*.orig` cubre `base..local_sha` (lo que gana la rama protegida), no solo los commits que ninguna remota tiene. Caso en los tests: `git push origin <rama>:main` con un marcador en un commit que ya estaba en otra rama remota.
- **Why it is general:** es la forma de subir de una tarea que publica sola, justo la que se salta la comprobación.
- **Version bump:** patch
- **Status:** propuesta

## P17. `aplicar.py` copia `LICENSE-mattpocock-skills` (F10)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F10) @ 673602b (retro); `skills/research|retro|prototype|to-questionnaire|improve-codebase-architecture/SKILL.md` dicen «MIT (see LICENSE-mattpocock-skills)» y `scripts/aplicar.py` no copia ese archivo
- **What changes:** copiar `LICENSE-mattpocock-skills` a `.claude/skills/` junto con esas skills (propiedad del flujo, con cabecera de versión si procede); `version.py` y `doctor.py` lo conocen.
- **Why it is general:** todo proyecto nuevo queda con la referencia de licencia rota.
- **Version bump:** patch
- **Status:** propuesta

## P18. `REVIEW.md` y `GLOSSARY.md` ya existentes: `aplicar.py` imprime el diff con la plantilla (F12)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F12) @ 673602b (retro); `scripts/aplicar.py` (`("REVIEW.md", "seeded")`: se crea si falta y nunca más)
- **What changes:** si existen, `aplicar.py` imprime `diff --no-index <archivo> <plantilla>` sin escribir nada y `aplicar.md` §3 dice que el agente pase a mano lo que falte (reglas «bash 3.2», «traído de otro repo: contratos de este», «idiomas visibles»).
- **Why it is general:** los archivos «sembrados» no reciben mejoras del flujo en proyectos que ya tenían uno; el portal comparó a mano.
- **Version bump:** patch
- **Status:** propuesta

## P19. La plantilla de `CLAUDE.md` nombra `.claude/hooks/` (F13)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F13) @ 673602b (retro); `templates/es/CLAUDE.md:16` (y `templates/en/`)
- **What changes:** «`.claude/hooks/`» pasa a «`.claude/gw/scripts/`» en las dos plantillas; un caso de `tests/comprobar.sh` que busca en las plantillas rutas que el flujo ya no usa.
- **Why it is general:** referencia a una ruta que el flujo no crea, en todos los proyectos nuevos.
- **Version bump:** patch
- **Status:** propuesta

## P20. Aviso de sesión fuera del repo, en la nube (F11)

- **Source:** `docs/registros/piloto-galivelop-workflow.md` (F11) @ 673602b (retro); `scripts/doctor.py:307-313` y `scripts/registro_sesion.py:64,99` (proponen `cd <repo> && claude`)
- **What changes:** con `CLAUDE_CODE_REMOTE=true` el aviso explica que la carpeta la pone la plataforma y qué comprobar a mano (`echo $CLAUDE_CODE_AUTO_COMPACT_WINDOW`; los ganchos de `settings.json` no corren con varios repos: ver `problemas.md`) en vez de la orden `cd`; y detectar si `settings.json` cargó (la variable de compactación en el entorno) antes que mirar la carpeta del registro.
- **Why it is general:** un WARN que se repite sin arreglo posible se aprende a ignorar.
- **Version bump:** patch
- **Status:** propuesta

## P21. `recoger.py` recorre todo Markdown cambiado, no solo `retro-*.md`

- **Source:** esta misma recogida (la sesión del flujo, 2026-10-22): `scripts/recoger.py` (`RETRO_NAME = (^|/)retro-[^/]*\.md$`) no listó `docs/registros/piloto-galivelop-workflow.md`, que traía las 26 fricciones y el `## For Galivelop-workflow` principal; solo salió la retro, con «lo nuevo»
- **What changes:** `recoger.py` busca el encabezado `## For|Para Galivelop-workflow` en **todos los `.md` rastreados cambiados desde la última recogida** (`git diff --name-only <last>..HEAD -- '*.md'`) y los lista bajo «Ideas for Galivelop-workflow»; los `retro-*.md` siguen saliendo como «Retro files». `gw-harvest` lo dice en el paso 2. Caso en los tests con una nota fuera de `retro-*`.
- **Why it is general:** cada proyecto nombra sus registros a su manera; la regla del flujo («For Galivelop-workflow» en la retro) no obliga al nombre.
- **Version bump:** patch
- **Status:** propuesta

## Se queda en el proyecto

- `tools/qa/tests/test-ganchos.sh` (`8674ca0`, `67c12a8`): sus 11 casos de la regla de `main`, la clasificación de rutas y el `pre-commit` con un commit tipo de la tarea semanal usan el `content` real del portal. Lo general es P14.
- Propuestas 1, 3, 4 y 6-8 de la retro (`.claude/gw/opt-tokens.md`, `AGENTS.md`, `CLAUDE.md`, bitácora): ajustes del portal; algunas son parche de P1, P3, P4 y P5 y se quitan cuando entren.
- Propuesta 2 de la retro (prompt de la tarea «Tarkor semanal», pendiente del usuario): decisión del portal sobre su tarea; lo general es el patrón de P14.
- `selector.cases` y `designReferences` del portal (SEO, rutas indexadas, tres idiomas, Ink & Switch, WCAG 2.2), `visibleLanguages: es, gl, en`, `taskId` y `roadmap: false`: configuración del proyecto.
- `tools/generar-marca.mjs`, `.github/workflows/pages.yml`, `.claude/skills/README.md`, `LICENSE-mattpocock-skills` del portal (créditos propios), `REVIEW.md` y `GLOSSARY.md` ampliados: del portal.
- `tools/qa/__pycache__/recuperar.cpython-311.pyc` de la copia anterior se borró en `84b27d1`; no es del flujo.
- Nada que subir de las dos skills «cambiadas»: no hay ediciones del portal (P2). `.claude/settings.json` y `.claude/gw.json` del portal coinciden con las plantillas salvo lo decidido a mano (`visibleLanguages`, `selector.cases`, `designReferences`, `requireRetro: false`, `content`); el `.githooks/pre-push` del portal es el de `603ca36` (mensaje de «nothing new to push» anterior a `d01091e`).

## Ya está aquí

- F23 (gancho de PR en cada `Bash`, bloquea si falla `python3`): **no se reproduce**. `scripts/revision-antes-de-main.sh` (líneas 534-545) sale con 0 sin lanzar `python3` salvo que el texto nombre `gh` y `pr` o una herramienta de PR; la copia del portal es idéntica. Lo que queda (una invocación de `bash` por cada llamada a Bash, con `pushToProtected: direct`) es barato; no se propone nada.
- F17, parte: la lectura sin terminal ya devuelve `None` con `isatty()` (`scripts/recuperar.py:223`); queda el caso de la tubería abierta (P5).
- Fila «Traer algo de otro repo → `orchestrate-dealer`» en `skills/selector/SKILL.md` (L22) y escalera de subagentes: existen; falta citarlas desde `gw-init` (P11).
- Revisión corta del código que un subagente sube en la propia rama, tandas de 6-8, `SendMessage` al subagente cortado, estado intermedio fuera de git y `recuperar.py --estado` en el encargo: ya están en nuestro `orchestrate-dealer` y `opt-tokens` desde `7112486`; el portal tiene aún la copia anterior (P2).
- Rechazo del modo automático al editar ganchos y `settings.json`: `problemas.md` y `aplicar.md` (Instalador P3 de la recogida anterior).
