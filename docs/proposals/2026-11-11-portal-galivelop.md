# Harvest portal-galivelop — 2026-11-11

De `dd327106` a `48827b11` (`scripts/harvest.py`). 129 commits: vistas previas por idioma, novedades, fichas,
animaciones, SEO e identidad visual; ninguno toca copias del flujo. Nacen las skills `gw-seo` y `gw-portal`.
Recogida de cierre de la `0.6` (H18).

## P1. Skill `gw-seo` en el flujo

- **Source:** `.claude/skills/gw-seo/SKILL.md` @ `76d8beb` (new skill; retro `docs/records/retro-2026-11-05-seo-y-fichas.md` @ `1e3e761`)
- **What changes:** SEO y vistas previas para webs estáticas, con `scripts/comprobar.py` sin red (stdlib, 47 tests) y
  referencias con fuente y fecha. Al traerla: nombres en inglés, `metadata.version`, tests en el check, docs es/en y
  la LICENSE MIT de la fuente que adapta (AgriciDaniel/claude-seo). Revisar antes que no dependa de rutas del portal.
- **Why it is general:** cualquier proyecto con web pública estática lo necesita.
- **Version bump:** minor
- **Status:** proposed

## P2. La revisión de la fase 1, en contexto limpio

- **Source:** `docs/records/retro-2026-11-10-novedades-productos-perfil.md` @ `dc253c7` (retro)
- **What changes:** la fase 1 de `AGENTS.md` y `gw-selector` dicen que `/code-review` empieza tras `/clear` o en un
  subagente limpio.
- **Why it is general:** medido: 3,7M de entrada a 127k por llamada para una revisión que solo necesita el diff.
- **Version bump:** patch
- **Status:** proposed

## P3. `prototype` publica el Artifact desde un subagente

- **Source:** `docs/records/retro-2026-11-08-identidad-visual.md` @ `e9efd02` (retro)
- **What changes:** `skills/prototype/SKILL.md`: la publicación (con su `quickstart`) va en un subagente que devuelve
  solo la URL.
- **Why it is general:** el `quickstart` (~10k) se arrastra en el resto de la sesión: 308k en 120 llamadas.
- **Version bump:** patch
- **Status:** proposed

## P4. `measure.py` muestra el `action` de las llamadas a Artifact

- **Source:** `docs/records/retro-2026-11-08-identidad-visual.md` @ `e9efd02` (retro)
- **What changes:** en HEAVIEST RESULTS, la fila de `Artifact` incluye `action` para separar `quickstart` de `publish`.
- **Why it is general:** sin eso no se ve qué llamada pesa.
- **Version bump:** patch
- **Status:** proposed

## P5. Encargos en paralelo devuelven el texto de la bitácora; `merge-branch.sh` avisa del conflicto en el `log`

- **Source:** `docs/records/retro-2026-11-09-carga-por-partes.md` @ `bb3b404` (retro)
- **What changes:** una variante del encargo de `gw-orchestrate-dealer` para subagentes concurrentes en ramas
  distintas: no tocan la bitácora y devuelven su texto, y la principal lo integra. Choca con «bitácora en el mismo
  commit»: decide el usuario. Aparte, `scripts/merge-branch.sh` distingue el conflicto en el archivo `log` y da la orden
  para resolverlo; caso en los tests.
- **Why it is general:** la bitácora es el conflicto de casi todo merge en paralelo.
- **Version bump:** minor
- **Status:** proposed

## P6. Corte «datos y textos al barato, lógica al grande» en el dealer

- **Source:** `docs/records/retro-2026-11-09-animaciones-workflow.md` @ `023f060` (retro)
- **What changes:** una frase en `gw-orchestrate-dealer` (o `gw-selector`) para un componente nuevo con diseño
  aprobado. Una sola observación: opcional.
- **Why it is general:** heurística de reparto válida en cualquier proyecto.
- **Version bump:** patch
- **Status:** proposed

## Stays in the project

- `.claude/skills/gw-portal/SKILL.md` @ `02756d1`: sincroniza el portal con los repos de la cuenta.
- Vistas previas, novedades, fichas, animaciones y borrados del portal.

## Already here

- `commit-msg` y `Siguiente:` fuera del último párrafo: `commit-message.py` ya lee solo el bloque de trailers; el
  proyecto tiene una copia anterior.
- Lo ya recogido del retro de SEO en `docs/proposals/2026-11-03-portal-galivelop.md`.
