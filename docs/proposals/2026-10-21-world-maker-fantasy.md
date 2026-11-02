# Harvest world-maker-fantasy — 2026-10-21

De `never` a `9cb05e50a063` (`scripts/recoger.py`). Primera recogida real. Los diffs de las 15 skills copiadas son,
casi todos, cabecera de licencia y notas «En este repositorio»: su copia es más antigua que la nuestra (les faltan
dos líneas de `diagnosing-bugs` y una de `grilling`), no mejor. Las rutas de skills son `.claude/skills/<nombre>/SKILL.md`.
Lo que ya trae `casos-reales.md` (ganchos, `revisado.sh`, `bitacora.py`, `prepush-ramas.sh`, `fusionar.sh`…) no se repite.

## P1. Referencias de diseño configurables para `grilling`

- **Source:** `CLAUDE.md` § «Diseño» y `.claude/skills/grilling/SKILL.md` (nota de verinews_ai, la versión genérica) @ 9cb05e50a063 (skill + regla)
- **What changes:** `gw.json` admite `designReferences` (lista de productos o marcos); `grilling` y `selector` las leen y cada recomendación cita de cuál sale. `/gw-init` las pregunta.
- **Why it is general:** los cuatro proyectos tienen la misma regla con referencias distintas (juegos, instaladores, marcos de verificación); hoy vive en prosa de `CLAUDE.md` y se pierde.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P2. `retro` revisa también las skills del proyecto y propone cambiarlas

- **Source:** `.claude/skills/retro/SKILL.md` («Las skills propias, también») @ 9cb05e50a063 (skill)
- **What changes:** en la sección de proyecto de `retro`: mirar cómo rindieron `opt-tokens`, `orchestrate-dealer`, `selector`, `pr`, el `/code-review` y la propia `retro`; leer la tabla de skills antes de proponer; si falló una skill, la propuesta cambia esa skill, no añade una regla suelta a `CLAUDE.md`.
- **Why it is general:** portal, instalador y verinews la tienen igual; evita que las reglas se acumulen en `CLAUDE.md`.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P3. «Fusiona directamente» no se salta la retro; la marca exige la decisión

- **Source:** `docs/registros/retro-2026-10-17-ronda-pr60.md:22` y `retro-2026-10-17-hallazgos-qa27.md:23` @ 9cb05e50a063 (retro)
- **What changes:** regla en la plantilla de `CLAUDE.md`: «directamente» quita esperar revisiones, no la retro ni presentarla. `requireRetro` de `revisado.sh` exige un `**Estado` que diga lo decidido, no solo «distinto de pendiente»; una retro «sin propuestas» escrita sin presentar no vale.
- **Why it is general:** pasó dos veces seguidas: sin la comprobación la retro llega con el PR ya creado.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P4. Tests que comprueban `settings.json`

- **Source:** `docs/registros/retro-2026-10-19-proceso-pruebas.md:66` @ 9cb05e50a063 (retro)
- **What changes:** `doctor.py` (y un caso de `tests/`) comprueba que cada `SessionStart` lleva `matcher`, que `compact` solo dispara `recuperar.py --estado` y que cada orden apunta a un archivo que existe.
- **Why it is general:** un gancho sin `matcher` reinyectaba la instalación del entorno tras cada compactación; es un fallo de configuración que ningún test de scripts ve.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## P5. El `pre-push` dice qué sube, no «todo en verde»

- **Source:** `docs/registros/retro-2026-10-12-qa27-tercera.md:12` @ 9cb05e50a063 (retro, script)
- **What changes:** el `pre-push` imprime los commits que sube por rama («sube 2: …»); si no sube ninguno, lo dice. En los ejemplos de la bitácora, nada de `grep -c` para contar errores (devuelve 1 con 0 coincidencias y corta cadenas con `&&`).
- **Why it is general:** un `git push` sin nada que subir imprimió «todo en verde» y dos tareas parecieron subidas.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## P6. Tests relacionados: segunda orden más lenta, por archivo cambiado

- **Source:** `docs/registros/retro-2026-10-19-p189-p205.md:9` y `retro-2026-10-15-hallazgos-qa27.md:10` @ 9cb05e50a063 (retro, script)
- **What changes:** `tests-relacionados.sh` lee del config una orden de «relacionados rápidos» y otra opcional «relacionados lentos» (p. ej. `foo.ts` → `foo.integration.test.ts`), que solo corre para los archivos cambiados.
- **Why it is general:** subieron dos veces en rojo por tests de integración que el pre-push no corría; la suite entera es demasiado lenta para el pre-push.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P7. `fusionar.sh` limpia la rama y el worktree del subagente

- **Source:** `docs/registros/retro-2026-10-20-lote-1.md:27` @ 9cb05e50a063 (retro, script)
- **What changes:** tras fusionar bien, `git worktree remove` y `git branch -d` (que solo borra lo fusionado), con su test.
- **Why it is general:** 26 ramas muertas; el `pre-push` que atribuye cada commit a la rama local que lo contiene tomó una de ellas como dueña de commits sin subir y los rechazó.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## P8. `pre-commit` con rutas protegidas para agentes

- **Source:** `docs/registros/retro-2026-10-20-pruebas-local.md:58` @ 9cb05e50a063 (retro, script)
- **What changes:** `gw.json` `protectedPaths`; el `pre-commit` rechaza archivos preparados bajo ellas cuando `CLAUDECODE=1`. Fuera de Claude Code no corre.
- **Why it is general:** un `git add docs/` metió los borradores sin commitear de la persona; cualquier repo con trabajo humano en curso en una carpeta tiene el mismo riesgo.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P9. `bitacora.py`: aviso de tarea `🚧` sin tocar su línea y fila cerrada al fusionar

- **Source:** `docs/registros/retro-2026-10-21-banco-narrador.md:111` y `retro-2026-10-21-la-linea.md:27` @ 9cb05e50a063 (retro, script)
- **What changes:** aviso (no bloqueo) cuando los commits nombran una tarea `🚧` y su línea del roadmap no cambia en el diff contra la base; el último commit antes del PR deja la fila como «al fusionarse, rama terminada».
- **Why it is general:** filas y roadmaps seguían diciendo «Siguiente/Falta: X» con X ya hecho, y `main` heredaba el estado viejo; lo cazó el `/code-review`, no la sesión.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P10. Presupuesto de compactaciones en `selector`

- **Source:** `.claude/skills/selector/SKILL.md` («Presupuesto de compactaciones») @ 9cb05e50a063 (skill)
- **What changes:** al empezar, estimar de 0 a 5 compactaciones, apuntarlo en la fila de la bitácora junto a las que lleva la sesión (`recuperar.py --estado`); si se pasa, repartir más. Depende de `recuperar.py` (Fase 3).
- **Why it is general:** convierte el contexto medio de `opt-tokens` en una señal durante la tarea, no solo después.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P11. `prototype`: entrega y archivo del veredicto

- **Source:** `.claude/skills/prototype/SKILL.md` (los cuatro proyectos, mismo texto) @ 9cb05e50a063 (skill)
- **What changes:** sección «In a Galivelop-workflow project»: con la herramienta `Artifact`, publicar y poner el enlace en la ronda; si no, `SendUserFile`; la lógica se guarda en una carpeta del repo y las variantes de UI se borran al elegir; el veredicto va al plan o bitácora.
- **Why it is general:** los cuatro proyectos añadieron lo mismo; el usuario revisa desde el móvil.
- **Version bump:** patch
- **Status:** aprobada (2026-10-21)

## P12. `opt-ai` como skill opcional (módulo de IA local)

- **Source:** `.claude/skills/opt-ai/` (`SKILL.md`, `medir.py`, `motores.md`, `proyecto.md`, `test_medir.py`) @ 9cb05e50a063 (new skill)
- **What changes:** skill opcional, `disable-model-invocation`, con la separación que ya usa `opt-tokens` (cuerpo genérico + `proyecto.md` del repo + `motores.md`), activada con `ai.local: true` en el config. Solo propone; si no hay registro de la tanda, para.
- **Why it is general:** cualquier proyecto con Ollama o motor local (instalador, verinews si añade IA local) necesita medir latencia y recuerdo por perfil; el instalador ya la copia. Costaría una skill más: no se incluye por defecto.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## P13. `to-questionnaire` como skill del conjunto upstream

- **Source:** `.claude/skills/to-questionnaire/SKILL.md` @ 9cb05e50a063 (new skill)
- **What changes:** es de `mattpocock/skills` (sin notas locales, 54 líneas): añadirla al port con licencia y `source`, `disable-model-invocation`, opcional.
- **Why it is general:** sirve para cualquier decisión que depende de otra persona; no toca ganchos ni config.
- **Version bump:** minor
- **Status:** aprobada (2026-10-21)

## Se queda en el proyecto

- `.claude/skills/orchestrate-dealer/SKILL.md`: `escenario.sh`, `mapa-agente.md`, rondas de pruebas jugando, P-números y `QA-n`; lo general (revisión por rama, registros compartidos, worktrees, TOOLS) ya está en nuestra versión.
- `.claude/skills/pr/SKILL.md`, `domain-modeling`, `research`, `improve-codebase-architecture`: solo notas de idioma y rutas.
- `retro-2026-10-21-banco-narrador.md:78` (`git push` y `host.sh` desde el sandbox) y `retro-2026-10-20-pruebas-local.md:26` (`arrancar-juego.sh`): entorno de su Steam Deck.
- Retros de contenido, reglas de juego, `nombrarOferta`, claves de React en tests (`retro-2026-10-17-ronda-pr60.md:10`): producto.

## Ya está aquí

- `opt-tokens` con curva primero, `POR SUBAGENTE`, arranque y salida no fiable bajo 100 tokens, ejecutar no es leer (`retro-2026-10-20-scout-updates.md:49`, `retro-2026-10-21-banco-narrador.md:67`).
- `orchestrate-dealer`: revisión por rama contra el contrato, registros compartidos solo la principal, WIP en worktrees, TOOLS (`retro-2026-10-20-opt-ai.md:17`, `retro-2026-10-20-p223-p237.md:18`).
- `scout-updates` con búsquedas en `sonnet` (`retro-2026-10-20-scout-updates.md:39`); escalera de subagentes del `selector`.
- Filas por rama y una rama por sesión (`retro-2026-10-20-pruebas-local.md:65`): ya en AGENTS y `casos-reales.md`.
