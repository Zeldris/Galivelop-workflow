# Harvest world-maker-fantasy — 2026-10-25 (segunda recogida del día)

De `076fe877` a `5641ebac` (`scripts/recoger.py`, 10 commits; sesión de difusión `QA-235`…`QA-239`). Ninguna skill ni
script del flujo cambia en el proyecto. Sale una skill nueva (`gw-media-content`) y tres ideas de la retro
`docs/registros/retro-2026-10-25-difusion.md`. Las ideas de la retro `…interfaz-imagenes` ya están en
`2026-10-25-world-maker-fantasy.md` y no se repiten.

## P1. Skill `gw-media-content` (contenido para redes y web, con imágenes)

- **Source:** `.claude/skills/gw-media-content/` (`SKILL.md`, `scripts/comprobar.py`, `scripts/render.mjs`,
  `scripts/test_comprobar.py`) @ `a9eb7bbf` (new skill, v0.2.0; nace en `c764d382`, 13 hallazgos de revisión arreglados
  en `a9eb7bbf`). Copia sin tocar en el scratchpad de la sesión (`social-media/`).
- **What changes:** skill nueva que prepara, sin publicar, los textos por canal (X, LinkedIn, Reddit, Discord, web) y
  las imágenes (tarjeta, diagrama, captura) de una novedad del proyecto, en una carpeta `AAAA-MM-DD-<tema>/` con una
  `ficha.md` de hechos con fuente. `comprobar.py` verifica huecos de plantilla, jerga interna (ids de tarea, ramas),
  X ≤ 280, JSON de `web.md`, imágenes sin renderizar o sin listar; `render.mjs` pasa HTML/SVG a WebP con Playwright e
  ImageMagick. Portarla exige quitar lo de WMF: la carpeta (`docs/difusion/`) y las plantillas `_plantilla/` pasan a
  ser configurables y a vivir en `templates/` o en `.claude/gw/gw-media-content.md` (idiomas, canales, paleta,
  escenarios de captura); las dependencias (Playwright, ImageMagick) pasan a `compatibility` y a un aviso de
  `doctor.py` solo si la skill se usa (el aviso, aplicado en `cf57265`: `media tools`, con la señal de la nota
  `.claude/gw/gw-media-content.md` o su carpeta).
- **Why it is general:** cualquier proyecto con novedades públicas repite el mismo ciclo (hechos con fuente → textos
  por canal → imágenes → comprobar que no se cuela jerga interna); el comprobador y los tests ya existen y son
  reutilizables.
- **Version bump:** minor
- **Status:** approved (2026-10-25), rediseñada: se parte en `gw-media-content` (hasta 10 propuestas) y `gw-media-content-now` (una pieza en carpeta con fecha); redes de inicio X, Reddit, LinkedIn y Discord; base en `docs/investigacion/redes-sociales.md`; **applied** (2026-10-25, `0.4.0`; el aviso de `doctor.py`, en `cf57265`): `reglas.json` y `comprobar.py` (b1), plantilla y `render.mjs` (b2), las dos `SKILL.md` con `catalogo.md` y `cifras.py` en `3cd53a9` y `534b2e6` (b3a), alta en el mapa, `selector`, patrón ES/EN y CHANGELOG (b3b)

## P2. El check falla si un script de skill propia no tiene su `test_*.py`

- **Source:** `docs/registros/retro-2026-10-25-difusion.md` (propuesta 1) @ `5641ebac`
- **What changes:** `doctor.py` avisa (y la plantilla del check del flujo puede exigir) cuando un
  `.claude/skills/*/scripts/*.py` no tiene al lado un `test_*.py`. Hoy `tests/comprobar.sh` corre los tests de las
  skills del flujo solo si existen; esto cubre las skills nacidas en el proyecto.
- **Why it is general:** en la sesión, 11 de 13 hallazgos de la revisión eran de robustez de un script sin tests.
- **Version bump:** patch
- **Status:** approved (2026-10-25); **applied** (`cf57265`, `0.4.0`): aviso `skill tests` en `doctor.py` y exigencia en el check de este repo (`tests/test_skills.py`)

## P3. `bitacora.py` dentro del `check` por defecto

- **Source:** `docs/registros/retro-2026-10-25-difusion.md` (propuesta 2) @ `5641ebac`
- **What changes:** `--init`/`templates/gw.json` y `docs/es/config.md` ↔ `docs/en/` recomiendan añadir la
  comprobación de `bitacora.py` a `check` cuando hay `log` y `plan`. Se solapa con la P1 del mismo día (el
  `commit-msg`, ya aprobada): si ese gancho se aplica, esta queda cubierta para el commit y solo falta para el CI.
- **Why it is general:** el fallo de la bitácora (tarea tachada y no en «Hecho recientemente») solo salta en el
  `pre-push`, con el commit ya hecho (amend y nueva subida).
- **Version bump:** patch
- **Status:** rejected (2026-10-25): se solapa con el gancho `commit-msg` aprobado en la recogida anterior

## P4. `requireRetro` con la persona ausente: dejarlo listo para un solo paso

- **Source:** `docs/registros/retro-2026-10-25-difusion.md` (propuesta 3) @ `5641ebac`
- **What changes:** una regla en `skills/retro/SKILL.md` y en las plantillas de `AGENTS.md`: si la persona pide llevar
  a `main` y no está para decidir la retro, se deja todo listo (retro escrita con `**Estado:** pendiente`, check en
  verde sobre la fusión con `main`, descripción del PR) y se para antes de `revisado.sh`; su confirmación de la retro
  es el único paso que falta.
- **Why it is general:** con `requireRetro` no hay forma de avanzar sin la decisión; hoy cada sesión lo improvisa.
- **Version bump:** patch
- **Status:** approved (2026-10-25); **applied** (`0.4.0`): regla en `skills/retro/SKILL.md`, en la fase 2 de las plantillas `AGENTS.md` (ES/EN), en `AGENTS.md` de este repo y en `requireRetro` de `docs/es/config.md` ↔ `docs/en/config.md`

## Se queda en el proyecto

- `.claude/gw/gw-media-content.md`, `docs/difusion/` (guía de canales, plantillas, ejemplo «mundo vivo»), la carpeta
  `docs/producto/plan-imagenes/` y `tools/playwright-e2e`: contenido y rutas de WMF.
- Retro, propuesta 4 (tres rojos falsos de `ci-local.sh` en un worktree: tests de `tools/qa/tests`): es de la
  herramienta propia del proyecto.
- Retro, `opt-tokens` (lecturas repetidas de READMEs del proyecto): sin propuesta general.
