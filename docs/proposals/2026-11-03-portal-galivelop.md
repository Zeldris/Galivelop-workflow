# Harvest portal-galivelop — 2026-11-03

De `aa76b34d` a `5248b0a7` (`scripts/harvest.py`). Sin cambios propios en skills ni scripts del flujo.

Sin skills ni scripts cambiados; las copias antiguas del flujo no cuentan. Hallazgos: 3 skills nacidas, 5 retros, ideas "For Galivelop-workflow" en 4 retros.
Estado del flujo comparado: rama actual (`0.5`), roadmap y bitácora al día 2026-11-03.

## P1. Aviso al lanzar un subagente sin `model`

- **Source:** `docs/registros/retro-2026-10-27-movil.md` (G1) @ 5248b0a (retro)
- **What changes:** Un gancho `PreToolUse` sobre `Agent|Task` avisa (sin bloquear) cuando la llamada no lleva `model`, con el recordatorio de `gw-selector`. Hoy `subagent-cap.py` ya cuelga de ese matcher (`templates/claude/settings.json`) y no mira `model`; bastaría ampliarlo.
- **Why it is general:** La regla "subagentes con plan cerrado, en el modelo barato" se rompió dos veces en el portal (un subagente heredó el modelo grande: 2,38M de entrada en trabajo mecánico); cualquier proyecto con `gw-orchestrate-dealer` tiene el mismo riesgo y una regla escrita que se rompe pide una comprobación.
- **Version bump:** minor
- **Status:** proposed

## P2. Endurecer `config-guard.py` (hallazgos 1-4 del code-review de la fase 1, retro gw-update 0.4.3 P4)

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.1-4.4) @ 5248b0a (retro)
- **What changes:** Proteger `.claude/settings.local.json` (hoy `EXACT` solo tiene `settings.json` y `gw.json`) y las mismas rutas dentro de `.claude/worktrees/<agente>/`; cubrir `find -exec rm`, `tar -C`, `unzip -d`, `git apply`, `git checkout <rama>`, `git stash pop` (`patch` y `-i` ya están); quitar el falso positivo de `touch -r`, `chmod --reference=` y `chown --reference=`.
- **Why it is general:** El guardián se instala en todos los proyectos y `settings.local.json` puede apagar los ganchos; los worktrees son el modo de trabajo de `gw-orchestrate-dealer`.
- **Version bump:** patch (es un arreglo de un gancho de seguridad; el falso positivo, también)
- **Status:** proposed

## P3. `/gw-update` sobre un clon de una sola rama: usar las etiquetas, no `git pull`

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P2) @ 5248b0a (retro) -> `skills/gw-update/SKILL.md`
- **What changes:** El paso 1 de `gw-update` (hoy `git -C <workflow> pull --ff-only`, líneas 23 y 30) pasa a lo que ya hace `gw-init` (líneas 34-37): `git ls-remote --tags --refs --sort=-v:refname`, última etiqueta, `git fetch origin tag vX.Y.Z`, sin depender de la rama del clon.
- **Why it is general:** Un clon que sigue solo una rama vieja (pasó con `claude/galivelop-workflow-inicio`, 0.1.0) no trae `main` ni las etiquetas, y la actualización falla o se queda corta en cualquier proyecto.
- **Version bump:** patch
- **Status:** proposed

## P4. `commit-msg` no debe cortar un `WIP:` ni un commit sin bitácora si `gw.json` no se lee

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.6) @ 5248b0a (retro) -> `templates/githooks/commit-msg` (líneas 37-38)
- **What changes:** Hoy `validate` fallido hace `exit 1` siempre. Distinguir: sin `gw.json` legible, solo se corta el commit que lleva la bitácora (o que necesita sus claves); un `WIP:` sin bitácora pasa con aviso.
- **Why it is general:** Rompe el relevo ("si hay que parar, commit con `WIP:`") justo cuando algo falla; afecta a todos los proyectos.
- **Version bump:** patch
- **Status:** proposed

## P5. La marca `gw-push-en-curso` del `pre-push` guarda la rama remota y se pisa entre worktrees

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.7) @ 5248b0a (retro) -> `templates/githooks/pre-push` (líneas 55-70)
- **What changes:** El `awk` guarda `$3` (rama remota) donde la documentación dice rama local, y el archivo es uno solo por git-common-dir: usar la local y un archivo por pid (o por rama).
- **Why it is general:** Los worktrees en paralelo son el modo normal de `gw-orchestrate-dealer`; dos subidas simultáneas se pisan la marca de las que depende el `Stop`.
- **Version bump:** patch
- **Status:** proposed

## P6. `doctor.py`: el aviso de "sesión fuera del repo" según falten los ganchos, no según la carpeta

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.9) @ 5248b0a (retro) -> `scripts/doctor.py` `check_session` y `scripts/session-start.sh` (líneas 47-60)
- **What changes:** En la nube la sesión en `/home/user` se da por buena (`cloud_start`, `check_compaction` solo cubre la ventana). Avisar cuando la sesión no cargó `.claude/settings.json` (varios repos, sin gancho `SessionStart`), no según el directorio de arranque.
- **Why it is general:** Fue la causa de un techo de 340k de contexto en el portal (retro SEO) y de la media de 225k (retro legal); cualquier proyecto en la nube lo sufre.
- **Version bump:** patch
- **Status:** proposed

## P7. `tope-subagentes.py` (hoy `subagent-cap.py`): contador sin enlaces simbólicos

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.5) @ 5248b0a (retro) -> `scripts/subagent-cap.py` (carpeta temporal, `gw-subagents-<session_id>`)
- **What changes:** Abrir el contador con `O_NOFOLLOW` o usar una carpeta por usuario.
- **Why it is general:** Es un script del flujo copiado a todos los proyectos; un enlace en `/tmp` compartido puede hacerle escribir donde no debe.
- **Version bump:** patch
- **Status:** proposed

## P8. `apply.py --dry-run` más corto (diff proyecto-contra-plantilla solo con `--verbose`)

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P3, T2) @ 5248b0a (retro) -> `scripts/apply.py` (`--dry-run`, sin `--verbose`)
- **What changes:** El ensayo no imprime el diff de los archivos rellenados salvo con `--verbose`; el paso 3 de `gw-update` ya da el que importa.
- **Why it is general:** La salida cuesta ~300k de contexto arrastrado por sesión de `/gw-update`; cualquier proyecto con archivos rellenados paga lo mismo.
- **Version bump:** minor (cambia la salida de una opción documentada)
- **Status:** proposed

## P9. Texto del paso "Git hooks path" de la plantilla del CI

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.8) @ 5248b0a (retro) -> `templates/github/check.yml` (línea 80)
- **What changes:** El paso dice que `doctor.py` está en el check; solo corre cuando está. Corregir el texto o condicionarlo.
- **Why it is general:** Es un archivo de plantilla que se copia a todos; el mensaje engaña en un fallo del CI.
- **Version bump:** patch
- **Status:** proposed

## P10. Script de sustituciones en varios archivos, todo o nada

- **Source:** `docs/registros/retro-2026-10-31-legal.md` (G2) @ 5248b0a (retro)
- **What changes:** Un `scripts/replace.py` (nombre en inglés, A8) que comprueba que todos los patrones casan antes de escribir nada, para que un script de sustituciones no deje un estado a medias.
- **Why it is general:** El problema (dos veces un script se paró a mitad) no depende del proyecto; pero se resuelve también con un solo `git stash`/`git checkout -- .` y no hay otro caso. Valor bajo: conviene confirmar con una segunda recogida antes de añadir un script.
- **Version bump:** minor
- **Status:** proposed

## P11. Decidir si `prepush-branches.sh` basta mirando la bitácora solo en la punta

- **Source:** `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` (P4.10) @ 5248b0a (retro)
- **What changes:** Decisión de criterio, no código: aceptar o no que un commit intermedio con la bitácora rota llegue al remoto (a propósito desde la 0.4.2).
- **Why it is general:** Es una regla del flujo que afecta a todos; sin cambio previsible, se presenta solo como pregunta al usuario.
- **Version bump:** (sin versión; solo decisión)
- **Status:** proposed

## Stays in the project

- `docs/registros/retro-2026-10-27-movil.md` P1 y P2: `tools/qa/medir-paginas.cjs` (móvil 390/360/320, cortes y táctiles) y arreglos de `global.css`; son del portal web.
- `docs/registros/retro-2026-10-27-productos.md`: dice "Nada general esta vez"; todas sus propuestas son del proyecto.
- `docs/registros/retro-2026-10-30-seo.md`: el resto de propuestas (SEO del portal); su T1 "sesión abierta fuera del repo" la cubre la propuesta 6 y lo que toca al entorno es del proyecto.
- `docs/registros/retro-2026-11-02-gw-update-0-4-3.md` T1 (variable de compactación y entorno solo con el portal) y la nota de T2: las hace la persona en el entorno de la nube del portal.
- `comprobar.yml` con líneas `# Portal: …` y la adaptación local de los textos legales/tarjetas (retros legal y movil): contenido del portal.

## Already here

- `skills/gw-selector`, `skills/gw-orchestrate-dealer`, `skills/gw-opt-tokens` (skills nacidas `selector`, `orchestrate-dealer`, `opt-tokens` del portal): son las versiones antiguas, sin prefijo `gw-` (A8, `docs/roadmap.md`); el flujo las tiene con el nombre y la forma nuevos.
- Retro legal G1 (avisar si falta `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en la nube): `scripts/doctor.py` `check_compaction` (líneas 654-672) y `templates/*/gw-opt-tokens.md`.
- Retro SEO P4 (`rojo-sin-arreglo.sh --commit <sha>`): `scripts/red-without-fix.sh --fix-at COMMIT` (deshace el arreglo ya commiteado contra `COMMIT^`), con la comprobación de que el test no vaya en el mismo archivo sin commitear.
- Retro gw-update 0.4.3 P1 (`aplicar.py --update` pisaba un archivo con cambios locales): `scripts/apply.py` (líneas ~278-308): un archivo del flujo que difiere de la versión de su cabecera se propone como `.gw-new` y no se sobrescribe.
- Retro gw-update 0.4.3 P4.3 en parte: `patch` ya está en `WRITERS` de `scripts/config-guard.py` y `awk -i inplace`/`sed -i` por `--in-place` (línea 284); el resto va en la propuesta 2.
- Scripts del flujo (`config.py`, `doctor.py`, `session-start.sh`) y skills (`gw-init`, `gw-update`, `pr`, `retro`, `gw-media-content*`): copias antiguas sin cambios locales; nada que recoger.
