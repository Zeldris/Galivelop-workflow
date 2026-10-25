# Galivelop-workflow — plan de creación del repositorio

> Documento para la sesión de Claude que cree el repo. Léelo entero antes de empezar y síguelo por fases: cada
> fase acaba con commit + push y su casilla marcada en `docs/traspaso.md` del repo nuevo.
> Redactado el 2026-10-21 a partir del flujo en uso en **Portal-Galivelop** y **World-Maker-Fantasy (Tarkor)**.
> **Revisado el 2026-10-21 al cerrar la Fase 0** con las decisiones del usuario (§0). Investigación en
> `docs/investigacion/`.

## 0. Cambios tras la Fase 0 (decisiones del usuario, 2026-10-21)

1. **Dos etapas.** *Etapa 1:* un agente de IA aplica el flujo a un proyecto leyendo este repo (guía para agentes +
   plantillas + scripts deterministas). *Etapa 2:* instalación automática **sin IA**, para proyectos nuevos (lo
   recomendado) y existentes. No se empieza la etapa 2 hasta que la 1 sea estable en los pilotos.
2. **El flujo se copia al repo destino** (skills, scripts y ganchos, con su versión) como vía base: es lo que hace un
   agente al aplicarlo y funciona en la nube, que **no carga plugins declarados en el repo** (comprobado). El plugin
   y el marketplace pasan a ser una vía opcional de la etapa 2 (local, o el script de configuración del entorno).
3. **Reglas del flujo en `AGENTS.md`** (estándar abierto, válido para cualquier agente); `CLAUDE.md` = `@AGENTS.md`
   + lo propio de Claude.
4. **Claves de `gw.json` en inglés**; **`check` es una lista de órdenes**; **marca de revisado versionada** en el
   repo para los dos modos de subida.
5. **Se porta pieza a pieza** desde el repo que tiene la mejor versión de cada una (tabla en
   `docs/investigacion/casos-reales.md`), no «del portal».
6. **Este repo usa su propio flujo** desde la Fase 1, aplicado como copia igual que en cualquier proyecto.
7. **Skills según la especificación Agent Skills** (`name`, `description`, `license`, `compatibility`,
   `metadata.version`); las cosas comprobables las hacen scripts (p. ej. `doctor`), no skills.
8. **Recogida de mejoras desde los proyectos** (usuario, 2026-10-21): skill `gw-harvest` (§5.1) que revisa los
   repos conectados que usan el flujo y apunta como propuestas sus cambios, skills nuevas e ideas.

## 1. Qué es y para qué

**Galivelop-workflow** es la forma de trabajar con Claude Code del taller Galivelop, sacada de sus proyectos y
generalizada para cualquier repositorio. Es la **fuente única y versionada** de sus skills, ganchos y plantillas:
una mejora se hace aquí una vez, sube de versión y llega a todos los proyectos, en vez de copiarse a mano repo a
repo (que es como está hoy: Portal y Tarkor tienen cada uno su copia y ya divergen).

Lo que resuelve el flujo:

1. **Relevos sin pérdidas.** Una sesión puede acabarse (tokens, contenedor, cambio de cuenta) y la siguiente sigue
   sin preguntar: bitácora al día, commit + push en cada punto estable, «lo que no está subido no existe».
2. **Elegir bien antes de empezar.** Un `selector` decide qué skill y qué modelo pide cada tarea, y una escalera
   de subagentes reparte lo mecánico a modelos baratos.
3. **Nada sin revisar llega a `main`.** `/code-review` del diff, marca de revisado en el repo y ganchos que no
   dejan subir código sin ella ni con el check en rojo.
4. **Gastar pocos tokens sin perder calidad.** `orchestrate-dealer`, compactación a 200k, recuperación tras
   `/clear`, y `opt-tokens` + `retro` que miden y proponen mejoras del entorno.

**Fin del camino:** tras mucho rodaje en proyectos reales y con los criterios de la §10 cumplidos, se publica la
**`1.0.0`, y solo esa**, en un repo público aparte; se publica en el portal Galivelop como proyecto (ficha en
castellano, gallego e inglés) y se valora publicarla también en npm. Las versiones siguientes siguen privadas.
La `1.0.0` se obtiene **solo como plugin**: tener el flujo en local (copiado en un repo) queda para el repo privado,
los colaboradores invitados o una posible venta. Por eso el portal (público) quita su copia del flujo y pasa a
depender del plugin (decidido por el usuario, 2026-10-22).

## 2. Decisiones ya tomadas (del usuario, 2026-10-21)

| Decisión | Valor |
|---|---|
| Nombre del repo | `Galivelop-workflow`, siempre privado; la `1.0.0` se publica en un repo público aparte (§10) |
| Idiomas | **Español e inglés** (ver §4.4) |
| Distribución | La más cómoda y limpia: **plugin de Claude Code servido desde el propio repo como marketplace**. npm se valora al final |
| Versionado | El repo es el punto de versión de todas las skills y mejoras |
| Publicación | Solo la `1.0.0` es pública (+ ficha en Galivelop), cuando el flujo esté probado como 100 % funcional y aplicable a cualquier sistema; de la siguiente en adelante, privadas (decidido por el usuario, 2026-10-22) |

> **Revisado en §0:** la distribución base es la copia gestionada; el plugin queda como opción de la etapa 2.
>
> **Revisado de nuevo (2026-10-22):** hasta la Fase 8, la copia gestionada sigue siendo la base de trabajo en los
> pilotos privados; desde la Fase 9, el plugin pasa a ser **la única distribución hacia fuera**. Límites que hay que
> resolver ahí: un plugin baja sus archivos a quien lo instala, así que lo que controla el uso es la **licencia**
> (la MIT actual permite redistribuir; la de la `1.0.0` queda abierta para la Fase 10, y las skills de Matt Pocock
> conservan su MIT); en la nube el plugin lo instala el script de entorno (Opción D); los ganchos de git
> (`pre-push`, marca de revisado) tienen que llegar desde el plugin, y eso está sin probar.

**Por qué plugin y no un script que copia archivos** (razonamiento original): el plugin trae versión, actualización (`/plugin update`) y
desinstalación de serie; las skills no se duplican en cada repo; y en un proyecto basta una línea en
`.claude/settings.json` para que cualquier sesión (también en la nube) lo cargue. Lo que **no** puede vivir en el
plugin (ganchos de git, `CLAUDE.md`, la bitácora, lo propio del proyecto) lo crea en el repo destino una skill de
arranque, `/gw-init`, y lo mantiene `/gw-update` (§5.4).

## 3. Inventario: qué se trae y de dónde

Fuente principal: **Portal-Galivelop** (la versión más reciente y ya corregida: 29 fallos de ganchos arreglados en
su retro del 2026-10-21). Tarkor aporta lo que el portal quitó por ser «de web pequeña» (roadmap con hitos).
**Ambos repos se leen, nunca se modifican desde la sesión que crea este.**

| Pieza | Origen (ruta en Portal-Galivelop) | Qué se hace al generalizar |
|---|---|---|
| `selector` | `.claude/skills/selector/SKILL.md` | Quitar casos del portal (rutas, SEO, tres idiomas). Tabla genérica + filas extra que el proyecto declara en su config (§6) |
| `orchestrate-dealer` | `.claude/skills/orchestrate-dealer/SKILL.md` | Plantilla de encargo con `{check}`, `{bitacora}` e idiomas del proyecto en vez de los fijos |
| `opt-tokens` + `medir.py` | `.claude/skills/opt-tokens/` | `medir.py` tal cual (ya es genérico) con referencias `QA-*` limpiadas; `proyecto.md` pasa a ser archivo del repo destino (`.claude/gw/opt-tokens.md`) |
| `retro` | `.claude/skills/retro/SKILL.md` | Mantener cuerpo MIT; la nota «En este repositorio» pasa a genérica (mirar skills del plugin y proponer cambios **al plugin** si la mejora es general) |
| `grilling`, `grill-with-docs`, `domain-modeling`, `diagnosing-bugs`, `codebase-design`, `improve-codebase-architecture`, `writing-for-agents`, `pr`, `prototype`, `research` | `.claude/skills/*` | Tal cual (MIT, mattpocock/skills). Solo se quitan las notas del portal. Licencia y créditos se conservan |
| Runbook del flujo | `docs/runbooks/skills-y-modelos.md` | Se convierte en `docs/<lang>/flujo.md` del plugin, genérico |
| `REVIEW.md` | `REVIEW.md` | Plantilla para el repo destino con las secciones genéricas («Un dato, un sitio», «Ganchos y scripts») y huecos para lo propio |
| `GLOSSARY.md` | `GLOSSARY.md` | Plantilla vacía con los términos del flujo (bitácora, punto estable, marca de revisado…) |
| `CLAUDE.md` | raíz de ambos repos | Plantilla: «Al empezar cualquier sesión», reglas de relevo y commits, con huecos `{{…}}` |
| Bitácora | `docs/traspaso.md` (portal) y `docs/registros/traspaso.md` (Tarkor) | Plantilla con las secciones del portal: Estado actual · Para la próxima publicación · Hecho (5 últimas) · Pendiente · Comprobar el estado |
| Gancho `SessionStart` | `.claude/hooks/session-start.sh` | Al plugin. Activa `core.hooksPath`, instala dependencias en la nube con la orden del config |
| Recuperación tras `/clear` | `tools/qa/recuperar.py` | Al plugin; lee la ruta de la bitácora del config |
| Gancho de PR a `main` | `.claude/hooks/revision-antes-de-main.sh` | Al plugin; rama protegida y ruta de la marca del config |
| `pre-push` | `.githooks/pre-push` | Plantilla copiada al repo destino por `/gw-init` (git no puede cargarlo desde el plugin): check del commit que se sube + marca de revisado para `main` |
| `es-codigo.sh`, `revisado.sh` | `tools/qa/` | Al plugin; los patrones de «contenido» salen del config |
| Tests de ganchos | `tools/qa/tests/test-ganchos.sh` | Al plugin, ampliados para que corran contra un repo de prueba temporal |
| Roadmap e hitos (opcional) | Tarkor: `tools/roadmap/cobertura.py`, `docs/producto/21-roadmap.md` | Módulo opcional activable en el config (`roadmap: true`) |
| Bitácora por ramas | Instalador: `tools/qa/bitacora.py`, `tools/qa/prepush-ramas.sh` | Una fila por rama, límite de caracteres y ruta del plan configurables |
| Utilidades de QA | Tarkor/instalador: `fusionar.sh`, `rojo-sin-arreglo.sh`, `tests-relacionados.sh`, `enlaces-md.py` | Genéricas; la orden de tests relacionados sale del config |
| Cierre de tareas | Tarkor: `tools/roadmap/cerrar.py` | Parte del módulo `roadmap` |
| Retro exigida antes de la marca | Tarkor/instalador: `revisado.sh` | Opción del config (`requireRetro`) |
| `scout-updates` | Tarkor: `.claude/skills/scout-updates/` | Skill opcional (solo a petición) |
| `opt-ai` + `medir.py` | Tarkor/instalador: `.claude/skills/opt-ai/` | Skill opcional para proyectos con modelos de IA locales; lo propio en `.claude/gw/opt-ai.md` |

> **Fuente por pieza (Fase 0):** la tabla «La mejor versión de cada pieza» de `docs/investigacion/casos-reales.md`
> manda sobre la columna «Origen» de arriba.

**No se trae:** lo propio de cada proyecto (tres idiomas del portal, lore de Tarkor, tarea semanal concreta,
rondas de pruebas jugando). `opt-ai` y `scout-updates` sí se traen, como skills opcionales (tabla de arriba). La **tarea programada semanal** se documenta como patrón
opcional en `docs/<lang>/patrones.md`, sin prompt concreto.

## 4. Estructura del repo

```text
Galivelop-workflow/
├── AGENTS.md                     # reglas del flujo para trabajar EN este repo (cualquier agente)
├── .claude-plugin/               # se mantiene válido; vía opcional de la etapa 2
│   ├── marketplace.json          # el repo es su propio marketplace (un plugin)
│   └── plugin.json               # nombre, versión (semver: la única fuente), descripción, autor, licencia
├── skills/                       # una carpeta por skill, SKILL.md en inglés (§4.4)
│   ├── selector/  orchestrate-dealer/  opt-tokens/  retro/  pr/
│   ├── grilling/  grill-with-docs/  domain-modeling/  diagnosing-bugs/
│   ├── codebase-design/  improve-codebase-architecture/  writing-for-agents/
│   ├── prototype/  research/
│   ├── gw-init/                  # arranca el flujo en un repo (§5.4)
│   ├── gw-update/                # trae las plantillas del repo a la versión del plugin
│   ├── gw-doctor/                # comprueba que el flujo está bien montado
│   └── gw-harvest/               # recoge como propuestas los cambios de los repos que usan el flujo
├── hooks/
│   └── hooks.json                # SessionStart (startup|resume|clear, clear|compact) y PreToolUse (PR a main)
├── scripts/                      # lo que llaman ganchos y skills; raíz por ${CLAUDE_PLUGIN_ROOT}
│   ├── session-start.sh  revision-antes-de-main.sh
│   ├── recoger.py                # parte determinista de gw-harvest
│   ├── recuperar.py  medir.py  es-codigo.sh  revisado.sh  bitacora.py  prepush-ramas.sh
│   ├── doctor.py                 # comprobación determinista del flujo (la usa gw-doctor y el CI)
│   ├── aplicar.py                # copia plantillas, skills y scripts sin pisar nada (etapa 1 y base de la 2)
│   └── config.py                 # lee y valida .claude/gw.json del proyecto (único lector)
├── templates/                    # lo que /gw-init copia al repo destino, en es/ y en/
│   ├── es/  AGENTS.md  CLAUDE.md  REVIEW.md  GLOSSARY.md  traspaso.md  opt-tokens.md
│   ├── en/  (los mismos)
│   ├── githooks/pre-push
│   ├── github/comprobar.yml      # CI mínimo: el check del proyecto
│   └── gw.json                   # config de ejemplo comentada en el README
├── schema/gw.schema.json         # JSON Schema del config
├── tests/
│   ├── test-ganchos.sh           # crea un repo git temporal y prueba cada gancho y script
│   └── test-plantillas.sh        # /gw-init sobre un repo vacío produce lo esperado; idempotente
├── docs/
│   ├── es/  flujo.md  aplicar.md  instalar.md  config.md  patrones.md  problemas.md  contribuir.md
│   └── en/  workflow.md  apply.md  install.md  config.md  patterns.md  troubleshooting.md  contributing.md
├── CLAUDE.md                     # @AGENTS.md + lo propio de Claude
├── .claude/  .githooks/          # el flujo aplicado a este repo (copia generada por scripts/aplicar.py)
├── docs/traspaso.md              # su bitácora
├── REVIEW.md  GLOSSARY.md
├── README.md  (en)   README.es.md
├── CHANGELOG.md                  # Keep a Changelog, bilingüe por entrada
├── LICENSE                       # MIT (compatible con las skills de mattpocock)
├── LICENSE-mattpocock-skills  CREDITS.md
└── .github/workflows/
    ├── comprobar.yml             # shellcheck, tests, validar JSON contra schema, plugin.json == última entrada del CHANGELOG
    └── release.yml               # al etiquetar vX.Y.Z: comprueba versión y crea la release con su entrada del CHANGELOG
```

### 4.1 El repo usa su propio flujo

Desde la Fase 1, el repo se trabaja con su propio flujo, **aplicado igual que en cualquier proyecto**: `AGENTS.md`,
`CLAUDE.md`, bitácora y, según se construyan, la copia de skills en `.claude/skills/`, scripts en `.claude/gw/` y
ganchos. Esa copia la genera `scripts/aplicar.py` desde `skills/` y `scripts/`, y un test comprueba que no diverge.
Es la primera prueba de rodaje: si algo del flujo estorba aquí, estorba en todas partes.

### 4.2 Nombres

- Proyecto y plugin: `galivelop-workflow`. Copiadas al repo destino, las skills se llaman por su nombre (`selector`);
  vía plugin, `galivelop-workflow:selector`.
- Las skills propias de gestión llevan prefijo `gw-` para no chocar con skills del proyecto.
- Config del proyecto: `.claude/gw.json`. Archivos propios del flujo en el repo destino: `.claude/gw/` (scripts) y
  `.claude/skills/<skill>/` (skills). Todo lo copiado lleva su versión (`metadata.version` en las skills, cabecera
  `galivelop-workflow vX.Y.Z` en scripts y plantillas).

### 4.3 Rutas

Todo script saca su raíz de su propia ruta (`$(dirname "$0")`) o de `${CLAUDE_PLUGIN_ROOT}`, y la del proyecto de
`git rev-parse --show-toplevel`. En `.claude/settings.json`, `$CLAUDE_PROJECT_DIR` solo sirve para **localizar** el
script; dentro, la raíz se calcula como se acaba de decir, **nunca** de `$CLAUDE_PROJECT_DIR` ni del directorio actual: en la nube la sesión
puede arrancar en `/home/user` (lección del portal, `REVIEW.md` §«Ganchos y scripts»).

### 4.4 Idiomas: español e inglés

- **Documentación para personas** (README, `docs/`, CHANGELOG, plantillas): en los dos idiomas. `README.md` en
  inglés (es lo que muestra GitHub y npm) con enlace a `README.es.md` arriba; `docs/es/` y `docs/en/` paralelos.
  Un test comprueba que cada archivo de `docs/es/` tiene su par en `docs/en/` y viceversa.
- **Skills (`SKILL.md`)**: en **inglés, una sola versión**. Se cargan en el contexto del agente; duplicarlas
  dobla su coste. Las skills de mattpocock ya están en inglés. El agente responde en el idioma del proyecto
  (`language` del config), y eso lo dice el `CLAUDE.md` generado.
- **Plantillas**: `/gw-init` copia las de `templates/<idioma>/` según el config.
- **Mensajes de los scripts**: en inglés, con la orden concreta que arregla el fallo.

## 5. Componentes en detalle

### 5.1 Skills

Cada `SKILL.md` de menos de 200 líneas (`writing-for-agents`), frontmatter con `name` y `description` que diga
**cuándo** usarla. Las de mattpocock conservan su texto; las propias se reescriben genéricas:

- **`selector`**: tabla de casos genéricos (diseño, fallo, cambio grande, cambio acotado, mecánico, traer de
  otro repo, revisar antes de `main`, cierre de bloque, escribir para agentes) con skill, modelo de sesión y modelo
  de subagentes. Reglas: el modelo de sesión lo elige el usuario y Claude lo dice en una línea; escalera de
  subagentes `sonnet low → sonnet medium → opus medium → opus high`, dos fallos y se para; en la duda, la fila de
  más riesgo. Lee filas extra de `selector.cases` del config.
- **`orchestrate-dealer`**: la principal planea, decide y revisa; los subagentes leen, implementan trozos y
  suben. Plantilla de encargo con punteros, criterio de hecho y respuesta de ≤15 líneas
  (`HECHO · COMMIT · FALTA · PREGUNTAS`). Uno a la vez en la misma rama si escriben.
- **`opt-tokens`**: igual que en el portal («calidad primero», contexto medio × llamadas manda). Lo propio del
  proyecto, en `.claude/gw/opt-tokens.md`.
- **`retro`**: añade una salida nueva: si una mejora vale para cualquier proyecto, la propuesta es un **issue o
  PR al repo `Galivelop-workflow`**, no un parche local. Así el flujo aprende de todos los proyectos.
- **`gw-harvest`** (se usa desde este repo; el «tirar» que complementa el «empujar» de `retro`): para cada repo
  conectado a la sesión que tenga `.claude/gw.json`, recoge lo nuevo desde la última recogida:
  - **cambios locales a piezas del flujo** (skills, scripts, plantillas): lo copiado comparado con la versión del flujo
    con que se aplicó (`metadata.version` y cabeceras);
  - **skills nuevas** nacidas en el proyecto (en `.claude/skills/` y que no son del flujo);
  - **ideas y mejoras generales** en sus retros y su bitácora.

  Lo mecánico (qué archivos difieren, qué skills son nuevas, qué commits hay desde la última vez) lo hace
  `scripts/recoger.py`, sin IA; el agente solo juzga si cada cambio es general o propio del proyecto y lo redacta.
  Escribe `docs/propuestas/AAAA-MM-DD-<repo>.md` (origen con ruta y commit, qué cambia, general/propio, versión que
  pediría: parche, menor o mayor) y guarda en `docs/propuestas/estado.json` el último commit recogido de cada repo.
  **Nunca aplica nada sin confirmación**: lo aprobado entra como cambio normal, con CHANGELOG y versión nueva. Los
  repos se leen en solo lectura, con subagente.
- **`gw-init`, `gw-update`, `gw-doctor`**: ver §5.4.

### 5.2 Ganchos de Claude Code (`hooks/hooks.json`)

| Evento | Qué hace |
|---|---|
| `SessionStart` (`startup\|resume\|clear`) | `session-start.sh`: `core.hooksPath=.githooks` si no hay otro, dependencias en la nube (`install` del config, solo si `CLAUDE_CODE_REMOTE=true` y el lockfile cambió), aviso si `gw.json` falta o la versión copiada va por detrás de la del flujo |
| `SessionStart` (`clear\|compact`) | `recuperar.py --estado`: fila de estado de la bitácora, `git status`, últimos commits, cómo buscar un detalle |
| `PreToolUse` (`create_pull_request\|merge_pull_request` del MCP de GitHub y `gh pr create\|merge` por Bash) | `revision-antes-de-main.sh`: sin marca de revisado del mismo código o con CI sin verde, bloquea. Falla cerrado |

### 5.3 Ganchos de git y CI (en el repo destino)

- `.githooks/pre-push` (copiado por `/gw-init`, con cabecera `# galivelop-workflow vX.Y.Z`): corre `check` del
  config **sobre el commit que se sube** (worktree temporal si no es la carpeta de trabajo); a la rama protegida,
  exige la marca de revisado si trae código. `--no-verify` solo para `WIP:` en rojo.
- Marca de revisado: `revisado.sh` escribe el sha en `reviewMark` del config (por defecto
  `docs/registros/revisado.txt`) y hace commit. Viaja con el repo, así la ven tareas programadas y otras cuentas.
- `es-codigo.sh`: «código» es todo lo que no casa con `content` del config. Solo lo que es código pide revisión.
- `.github/workflows/comprobar.yml`: `install` + `check` en cada push que no sea a la rama protegida y en cada PR.

### 5.4 Aplicar, actualizar y comprobar

- **`docs/<lang>/aplicar.md` (etapa 1):** la guía que sigue un agente para aplicar el flujo. Separa lo que exige
  criterio (deducir `install`/`check` de `package.json`, `pyproject.toml`, `Cargo.toml`, `Makefile`…; fusionar un
  `CLAUDE.md`/`AGENTS.md` existente, enseñando el bloque antes) de lo mecánico, que siempre es un script.
- **`scripts/aplicar.py`:** escribe `.claude/gw.json`, copia plantillas, skills y scripts **sin pisar nada** (lo que
  ya existe queda como propuesta `*.gw-nuevo` para revisar), añade los ganchos a `.claude/settings.json` y
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`, y pone `core.hooksPath` si no hay otro gestor. Idempotente. Commit
  `Flujo Galivelop-workflow vX.Y.Z` y `Siguiente:`.
- **`/gw-init`, `/gw-update`** (skills con `disable-model-invocation: true`): envoltorios finos de `aplicar.md` y
  `aplicar.py`. `gw-update` compara versiones y enseña el diff del cambio de plantilla (no del archivo que el
  proyecto rellenó) antes de aplicar lo que el usuario confirme.
- **`scripts/doctor.py`** (y `/gw-doctor`, que lo llama): comprueba y lista con la orden que arregla cada cosa:
  config válido contra el schema, `core.hooksPath` y convivencia con otros gestores, `pre-push` ejecutable y de la
  versión actual, bitácora con sus secciones, órdenes de `check` existentes, CI presente, copia sin divergir.

## 6. El config del proyecto: `.claude/gw.json`

Todo lo que cambia de un proyecto a otro, y nada más. Lo lee solo `scripts/config.py` (un dato, un sitio). Claves en
inglés (decisión de la Fase 0).

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/zeldris/Galivelop-workflow/v1.0.0/schema/gw.schema.json",
  "version": "0.1.0",                       // versión del flujo con la que se aplicó
  "language": "es",                         // es | en: plantillas y lengua de las respuestas
  "visibleLanguages": ["es", "gl", "en"],   // opcional: lo que REVIEW.md exige al texto visible
  "log": "docs/traspaso.md",                // bitácora
  "logRows": false,                         // opcional: una fila por rama con límite (bitacora.py)
  "protectedBranch": "main",
  "pushToProtected": "direct",              // direct | pr: push directo (pre-push pide la marca en los dos) o PR (además, PreToolUse)
  "install": ["npm ci"],
  "check": ["npm run check"],               // lista de órdenes; se corren en orden sobre el commit que se sube
  "reviewMark": "docs/registros/revisado.txt",
  "requireRetro": true,                     // opcional (por defecto en la plantilla): revisado.sh exige una retro en la rama
  "content": ["^docs/", "^public/", "^src/data/", "\\.md$"],   // regex: lo que NO pide /code-review
  "roadmap": false,                         // módulo opcional de hitos (Tarkor)
  "selector": { "cases": [] },              // filas extra propias del proyecto
  "designReferences": [],                   // opcional: con qué se contrasta el diseño (grilling, selector)
  "protectedPaths": [],                     // opcional: rutas que un agente no puede commitear (pre-commit)
  "staleRefs": [],                          // opcional: patrones que no deben aparecer en docs/ (enlaces-md.py)
  "plan": [], "taskId": "[A-Z]{2,5}-\\d+",   // opcional: plan con casillas e ids de tarea (bitacora.py)
  "relatedTests": { "fast": [], "slow": [] } // opcional: tests de lo que cambia, en pre-push
}
```

Ejemplos que los pilotos tienen que cubrir: el portal (Node, subida directa, tres idiomas visibles), Tarkor (backend
+ frontend, roadmap con hitos, varias cuentas, PR) y el instalador de Tarkor (Rust/Tauri: el caso sin Node).

## 7. Versionado

- **SemVer** en `plugin.json`. Mayor: cambia el config o una plantilla de forma que pide tocar el repo destino.
  Menor: skill o gancho nuevo, o mejora compatible. Parche: arreglos.
- **`CHANGELOG.md`** (Keep a Changelog), una entrada por versión con `### ES` y `### EN`. El CI falla si la
  versión de `plugin.json` no tiene entrada.
- **Etiquetas `vX.Y.Z`** y release de GitHub con la entrada del CHANGELOG (`release.yml`).
- **Cada versión empieza con una recogida** (`gw-harvest`, §5.1; usuario, 2026-10-23): lo que traen los proyectos
  entra en la versión que se abre. `scripts/version.py --release` no deja publicar sin una recogida (`# Harvest …`
  en `docs/propuestas/`) añadida desde la última etiqueta.
- **Rama `main` = última versión publicada**; se trabaja en ramas y se sube a `main` solo con confirmación (el
  propio flujo).
- **Fijar versión en un proyecto**: el marketplace se añade con `#vX.Y.Z` cuando un proyecto no quiera
  actualizaciones automáticas. Lo normal: seguir `main` y `/plugin update`.
- **La `0.4` es la última menor `0.x`** (usuario, 2026-10-25): la versión estable antes de la `1.0`. Cada recogida
  sigue haciéndose y reparte lo que trae: las correcciones de lo que ya hay van al siguiente parche (`0.4.x`); un
  evolutivo o algo nuevo (skill, gancho, mejora) se apunta para la **`1.0.0`** y no entra en la `0.4`. La `1.0.0` y
  siguientes son la línea que crece y el producto a largo plazo. Así no hay una cadena de evolutivos entre la `0.4` y
  la `1.0`. Los parches de la `0.4.x` se fusionan
  también en la rama de la `1.0.0`. Por decidir: si la `1.0.0` llega a `main` antes de cumplir la §10 (la copia
  pública de la Fase 10 la sigue pidiendo).

## 8. Instalación en un proyecto

**Etapa 1 (lo que contará `docs/<lang>/aplicar.md`):** desde una sesión con el proyecto y este repo a mano, se
pide al agente «aplica Galivelop-workflow siguiendo `docs/es/aplicar.md`». El agente decide lo que exige criterio,
lanza `scripts/aplicar.py` y termina con `scripts/doctor.py` en verde. En la nube funciona sin configurar nada,
porque el resultado vive en el repo.

**Etapa 2 (lo que contará `docs/<lang>/instalar.md`):** instalación sin IA, p. ej. con Copier (merge a tres bandas
para actualizar) o un script propio sin dependencias más allá de git, bash y python3; se decide en su fase. Vías
opcionales: el plugin desde el marketplace del repo (local) o instalado por el script de configuración del entorno
de la nube.

El instalador cubre **las dos cosas, instalar y actualizar**, con una sola orden que mira el proyecto y decide:

- **Instalar:** el proyecto no tiene el flujo (nuevo, o existente sin él): crea `.claude/gw.json` y copia todo sin
  pisar lo que ya exista.
- **Actualizar:** el proyecto ya tiene `.claude/gw.json`: lleva el flujo de su `version` a la nueva, respeta lo propio
  del proyecto y marca los conflictos.
- **Copia anterior sin `gw.json`** (como VeriNews_AI o los pilotos antes de aplicar el flujo): se trata como
  actualización, sustituyendo esa copia; nunca como instalación limpia que la duplique.

Las dos vías tienen sus tests y se prueban en los pilotos.

```text
claude plugin marketplace add zeldris/Galivelop-workflow
claude plugin install galivelop-workflow@galivelop-workflow
```

> Comprobado en la Fase 0 (`docs/investigacion/plugins.md`): un repo privado se añade como marketplace desde la
> CLI, también en la nube; la nube **no** carga lo declarado en `.claude/settings.json` del repo; un plugin
> instalado antes de que arranque Claude sí carga.

## 9. Fases de construcción

Cada fase: rama de trabajo, pasos con commit + push en cada punto estable, bitácora en el mismo commit, tests en
verde, y al cerrar `/code-review` antes de subir a `main` (con confirmación). Modelo según el `selector`: diseño y
ganchos con el grande; portar skills y plantillas con el medio. Desde la Fase 1, todo con el propio flujo (§4.1).

**Etapa 1 — aplicable por un agente**

| Fase | Qué | Hecho cuando |
|---|---|---|
| **0. Verificar** ✅ | Doc oficial de plugins, marketplaces y hooks; pruebas en la nube; tres casos reales; estándares | §0 decidido; notas en `docs/investigacion/` |
| **1. Esqueleto** | `LICENSE`, `AGENTS.md` + `CLAUDE.md`, README ES/EN, bitácora, CHANGELOG `0.1.0`, `.claude-plugin/` válido, CI (shellcheck, JSON, pares ES/EN, versión == CHANGELOG) | CI en verde y el repo trabajándose con su propio `AGENTS.md` |
| **2. Skills** | Portar las skills (§3) pieza a pieza, con campos de Agent Skills y test que los valida; `gw-harvest` + `scripts/recoger.py` | Todas validan; `writing-for-agents` pasado a las propias; licencias y créditos; `gw-harvest` recoge propuestas reales de Tarkor, el instalador, el portal y VeriNews |
| **3. Ganchos y scripts** | `config.py`, `doctor.py`, `session-start.sh`, `recuperar.py`, `revision-antes-de-main.sh`, `es-codigo.sh`, `revisado.sh`, `bitacora.py`, `prepush-ramas.sh`, `medir.py`, plantilla `pre-push`. Tests contra repo temporal: categorías de los 29 fallos, clon superficial, marcas de conflicto, otro gestor de ganchos. Aplicados a este repo | Tests en verde en Linux y macOS; fallan cerrado sin config |
| **4. Plantillas y aplicación** | `templates/es` y `templates/en`, `gw.schema.json`, `aplicar.py`, `aplicar.md`, `gw-init`, `gw-update`, `test-plantillas.sh`, `problemas.md` | Un agente aplica el flujo a un repo vacío y `doctor.py` lo da por bueno; dos veces no cambia nada |
| **5. Piloto: Portal-Galivelop** | En una sesión del portal (con permiso): un agente lo aplica siguiendo `aplicar.md` y sustituye su copia | `npm run check` en verde, `pre-push` y marca funcionando, tarea semanal sin cambios |
| **6. Piloto: Tarkor e instalador** | Igual en World-Maker-Fantasy (`roadmap: true`, PR) e Instalador-WMF-Tarkor (Rust). VeriNews_AI (Java + Vite) queda para la Fase 8, ya sin agente de IA | Relevo entre cuentas sin perder nada; lo que falte vuelve como versión nueva |
| **7. Rodaje etapa 1** | Uso real semanas; cada `retro` con mejora general → issue/PR aquí | Criterios de la §10 para la etapa 1 |

**Etapa 2 — instalación automática sin IA**

| Fase | Qué | Hecho cuando |
|---|---|---|
| **8. Instalador** | Elegir Copier o script propio; una orden que **instala** (proyecto nuevo o existente sin el flujo, sin pisar, conflictos marcados) o **actualiza** (con `gw.json`, o una copia anterior sin él) según lo que encuentre (§8) | Instalar sin IA en un repo nuevo; actualizar sin IA los pilotos (de su versión a la nueva) y VeriNews_AI (copia anterior sin `gw.json`); `doctor.py` en verde |
| **9. Plugin y npm** | El plugin pasa a ser la única distribución hacia fuera: marketplace en el repo privado con acceso por invitación, instalado en local y por el script de entorno de la nube (Opción D); que el plugin traiga también los ganchos de git (`pre-push`, marca de revisado); valorar npm (§11) | Un proyecto (el portal) funcionando solo con el plugin, en local y en la nube, ganchos incluidos |
| **10. Público** | Elegir la licencia de la `1.0.0` (que no permita redistribuirla ni venderla; MIT solo en lo de terceros), `/security-review`, quitar rutas o nombres privados, `1.0.0` **solo como plugin** copiada en un repo público aparte **sin el historial** (un solo commit; este repo sigue privado y continúa en `1.0.x`/`1.1`), ficha en el portal (tres idiomas); el portal quita su copia del flujo (desde una sesión del portal) y depende del plugin. Si hay npm, solo la `1.0.0` | Repo público con la `1.0.0` como plugin y ficha publicada; el portal sin copia del flujo; nada posterior fuera del repo privado |

**Apuntes para las Fases 9 y 10** (recogida de 2026-10-25, sin cambio ahora; se miran al abrir cada fase):

- **Fase 9:** validar el marketplace en el CI fijando el `sha` de las entradas `git-subdir`; si se porta a Codex,
  tope de 8 KB por skill; `"strict": false` con lista de skills como forma de partir el plugin (comportamiento sin
  comprobar).
- **Fase 10:** tabla amenaza / contramedida / evidencia como documento de seguridad; acciones del CI fijadas por
  `sha` y `permissions: {}` por defecto (hoy `comprobar.yml` y `release.yml` usan `@v4` / `@v5`).

## 10. Criterios para «100 % funcional y aplicable a cualquier sistema» (paso a 1.0)

- Funciona en **tres proyectos** de stacks distintos (al menos uno sin Node: el instalador de Tarkor o VeriNews son los candidatos)
  durante **≥ 4 semanas** cada uno.
- **Relevos probados**: al menos 5 cortes de sesión (tokens, `/clear`, cambio de cuenta) sin pérdida, comprobado
  con la bitácora.
- **Ganchos**: ningún falso positivo ni subida sin revisar a `main` en el rodaje; tests de ganchos en Linux y
  macOS en verde. Windows: documentado (Git Bash o WSL) y probado al menos una vez.
- **Instalación limpia**: etapa 1, un agente con `aplicar.md` + `doctor.py` en un repo nuevo sin tocar nada a mano;
  etapa 2, lo mismo sin IA.
- **Nada privado** en el repo: ni rutas de Tarkor o el portal, ni identificadores internos, ni datos personales.
- Documentación ES/EN completa y emparejada (lo comprueba el test).

## 11. npm (al final, opcional)

Paquete `galivelop-workflow` (o con ámbito `@galivelop/workflow`) con un binario `npx galivelop-workflow init`
que instala el marketplace y lanza el init para quien no quiera usar `/plugin`. Decidir en la Fase 9 si aporta algo
sobre el marketplace de GitHub; si se publica, `release.yml` también hace `npm publish` y la versión sale del
mismo `plugin.json`.

## 12. Lecciones que ya cuestan caro (no repetirlas)

De la retro del portal (2026-10-21) y del trabajo en Tarkor:

- Raíz del repo desde la ruta del script, nunca desde `$CLAUDE_PROJECT_DIR` o el directorio actual.
- Un gancho de subida comprueba **el commit que se sube**, no la carpeta de trabajo.
- Los ganchos **fallan cerrados** cuando les falta un dato (commit ausente, API sin respuesta).
- Lo traído de un proyecto se adapta a cómo sube ese proyecto (directo a `main` o por PR).
- Cada cambio en ganchos o scripts lleva su caso en los tests.
- Calidad primero: un ahorro de tokens que empeora el resultado no es ahorro.
- Leer otros repos con un subagente que devuelva un resumen; la principal no lee archivos enteros.

## 13. Primer mensaje para la sesión que cree el repo

```text
Vas a crear el repo Galivelop-workflow siguiendo el plan adjunto (galivelop-workflow-plan.es.md).
Empieza por la Fase 0. Portal-Galivelop y World-Maker-Fantasy son solo lectura.
Trabaja en la rama claude/galivelop-workflow-inicio, commit + push en cada punto estable,
bitácora en docs/traspaso.md del repo nuevo. A main, solo con mi confirmación.
```
