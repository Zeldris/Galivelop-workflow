# Galivelop-workflow — plan de creación del repositorio

> Documento para la sesión de Claude que cree el repo. Léelo entero antes de empezar y síguelo por fases: cada
> fase acaba con commit + push y su casilla marcada en `docs/traspaso.md` del repo nuevo.
> Redactado el 2026-10-21 a partir del flujo en uso en **Portal-Galivelop** y **World-Maker-Fantasy (Tarkor)**.

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

**Fin del camino:** tras mucho rodaje en proyectos reales y con los criterios de la §10 cumplidos, el repo se hace
público, se publica en el portal Galivelop como proyecto (ficha en castellano, gallego e inglés) y se valora
publicarlo también en npm.

## 2. Decisiones ya tomadas (del usuario, 2026-10-21)

| Decisión | Valor |
|---|---|
| Nombre del repo | `Galivelop-workflow` (privado hasta la §10) |
| Idiomas | **Español e inglés** (ver §4.4) |
| Distribución | La más cómoda y limpia: **plugin de Claude Code servido desde el propio repo como marketplace**. npm se valora al final |
| Versionado | El repo es el punto de versión de todas las skills y mejoras |
| Publicación | Público + ficha en Galivelop solo cuando el flujo esté probado como 100 % funcional y aplicable a cualquier sistema |

**Por qué plugin y no un script que copia archivos:** el plugin trae versión, actualización (`/plugin update`) y
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
| Bitácora | `docs/traspaso.md` (portal) y `docs/registros/traspaso.md` (Tarkor) | Plantilla con las secciones del portal: Estado actual · Para la próxima publicación · Hecho (10 últimas) · Pendiente · Comprobar el estado |
| Gancho `SessionStart` | `.claude/hooks/session-start.sh` | Al plugin. Activa `core.hooksPath`, instala dependencias en la nube con la orden del config |
| Recuperación tras `/clear` | `tools/qa/recuperar.py` | Al plugin; lee la ruta de la bitácora del config |
| Gancho de PR a `main` | `.claude/hooks/revision-antes-de-main.sh` | Al plugin; rama protegida y ruta de la marca del config |
| `pre-push` | `.githooks/pre-push` | Plantilla copiada al repo destino por `/gw-init` (git no puede cargarlo desde el plugin): check del commit que se sube + marca de revisado para `main` |
| `es-codigo.sh`, `revisado.sh` | `tools/qa/` | Al plugin; los patrones de «contenido» salen del config |
| Tests de ganchos | `tools/qa/tests/test-ganchos.sh` | Al plugin, ampliados para que corran contra un repo de prueba temporal |
| Roadmap e hitos (opcional) | Tarkor: `tools/roadmap/cobertura.py`, `docs/producto/21-roadmap.md` | Módulo opcional activable en el config (`roadmap: true`) |

**No se trae:** lo propio de cada proyecto (tres idiomas del portal, lore de Tarkor, tarea semanal concreta,
`opt-ai`, `scout-updates`, rondas de pruebas jugando). La **tarea programada semanal** se documenta como patrón
opcional en `docs/<lang>/patrones.md`, sin prompt concreto.

## 4. Estructura del repo

```text
Galivelop-workflow/
├── .claude-plugin/
│   ├── marketplace.json          # el repo es su propio marketplace (un plugin)
│   └── plugin.json               # nombre, versión (semver), descripción, autor, licencia
├── skills/                       # una carpeta por skill, SKILL.md en inglés (§4.4)
│   ├── selector/  orchestrate-dealer/  opt-tokens/  retro/  pr/
│   ├── grilling/  grill-with-docs/  domain-modeling/  diagnosing-bugs/
│   ├── codebase-design/  improve-codebase-architecture/  writing-for-agents/
│   ├── prototype/  research/
│   ├── gw-init/                  # arranca el flujo en un repo (§5.4)
│   ├── gw-update/                # trae las plantillas del repo a la versión del plugin
│   └── gw-doctor/                # comprueba que el flujo está bien montado
├── hooks/
│   └── hooks.json                # SessionStart (startup|resume|clear, clear|compact) y PreToolUse (PR a main)
├── scripts/                      # lo que llaman ganchos y skills; raíz por ${CLAUDE_PLUGIN_ROOT}
│   ├── session-start.sh  revision-antes-de-main.sh
│   ├── recuperar.py  medir.py  es-codigo.sh  revisado.sh
│   └── config.py                 # lee y valida .claude/gw.json del proyecto (único lector)
├── templates/                    # lo que /gw-init copia al repo destino, en es/ y en/
│   ├── es/  CLAUDE.md  REVIEW.md  GLOSSARY.md  traspaso.md  opt-tokens.md
│   ├── en/  (los mismos)
│   ├── githooks/pre-push
│   ├── github/comprobar.yml      # CI mínimo: el check del proyecto
│   └── gw.json                   # config de ejemplo comentada en el README
├── schema/gw.schema.json         # JSON Schema del config
├── tests/
│   ├── test-ganchos.sh           # crea un repo git temporal y prueba cada gancho y script
│   └── test-plantillas.sh        # /gw-init sobre un repo vacío produce lo esperado; idempotente
├── docs/
│   ├── es/  flujo.md  instalar.md  config.md  patrones.md  contribuir.md
│   └── en/  (los mismos)
├── CLAUDE.md                     # instrucciones para trabajar EN este repo (usa su propio flujo)
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

Desde la Fase 1, el repo se trabaja con su propio plugin instalado desde la carpeta local
(`/plugin marketplace add ./`). Es la primera prueba de rodaje: si algo del flujo estorba aquí, estorba en todas
partes.

### 4.2 Nombres

- Plugin: `galivelop-workflow`. Las skills se ven como `galivelop-workflow:selector`, etc.
- Las skills propias de gestión llevan prefijo `gw-` para no chocar con skills del proyecto.
- Config del proyecto: `.claude/gw.json`. Archivos propios del flujo en el repo destino: `.claude/gw/`.

### 4.3 Rutas

Todo script saca su raíz de su propia ruta (`$(dirname "$0")`) o de `${CLAUDE_PLUGIN_ROOT}`, y la del proyecto de
`git rev-parse --show-toplevel`, **nunca** de `$CLAUDE_PROJECT_DIR` ni del directorio actual: en la nube la sesión
puede arrancar en `/home/user` (lección del portal, `REVIEW.md` §«Ganchos y scripts»).

### 4.4 Idiomas: español e inglés

- **Documentación para personas** (README, `docs/`, CHANGELOG, plantillas): en los dos idiomas. `README.md` en
  inglés (es lo que muestra GitHub y npm) con enlace a `README.es.md` arriba; `docs/es/` y `docs/en/` paralelos.
  Un test comprueba que cada archivo de `docs/es/` tiene su par en `docs/en/` y viceversa.
- **Skills (`SKILL.md`)**: en **inglés, una sola versión**. Se cargan en el contexto del agente; duplicarlas
  dobla su coste. Las skills de mattpocock ya están en inglés. El agente responde en el idioma del proyecto
  (`idioma` del config), y eso lo dice el `CLAUDE.md` generado.
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
  más riesgo. Lee filas extra de `selector.casos` del config.
- **`orchestrate-dealer`**: la principal planea, decide y revisa; los subagentes leen, implementan trozos y
  suben. Plantilla de encargo con punteros, criterio de hecho y respuesta de ≤15 líneas
  (`HECHO · COMMIT · FALTA · PREGUNTAS`). Uno a la vez en la misma rama si escriben.
- **`opt-tokens`**: igual que en el portal («calidad primero», contexto medio × llamadas manda). Lo propio del
  proyecto, en `.claude/gw/opt-tokens.md`.
- **`retro`**: añade una salida nueva: si una mejora vale para cualquier proyecto, la propuesta es un **issue o
  PR al repo `Galivelop-workflow`**, no un parche local. Así el flujo aprende de todos los proyectos.
- **`gw-init`, `gw-update`, `gw-doctor`**: ver §5.4.

### 5.2 Ganchos de Claude Code (`hooks/hooks.json`)

| Evento | Qué hace |
|---|---|
| `SessionStart` (`startup\|resume\|clear`) | `session-start.sh`: `core.hooksPath=.githooks` si no hay otro, dependencias en la nube (`instalar` del config, solo si `CLAUDE_CODE_REMOTE=true` y el lockfile cambió), aviso si `gw.json` falta o la versión de plantillas va por detrás del plugin |
| `SessionStart` (`clear\|compact`) | `recuperar.py --estado`: fila de estado de la bitácora, `git status`, últimos commits, cómo buscar un detalle |
| `PreToolUse` (`create_pull_request\|merge_pull_request` del MCP de GitHub y `gh pr create\|merge` por Bash) | `revision-antes-de-main.sh`: sin marca de revisado del mismo código o con CI sin verde, bloquea. Falla cerrado |

### 5.3 Ganchos de git y CI (en el repo destino)

- `.githooks/pre-push` (copiado por `/gw-init`, con cabecera `# galivelop-workflow vX.Y.Z`): corre `check` del
  config **sobre el commit que se sube** (worktree temporal si no es la carpeta de trabajo); a la rama protegida,
  exige la marca de revisado si trae código. `--no-verify` solo para `WIP:` en rojo.
- Marca de revisado: `revisado.sh` escribe el sha en `marca` del config (por defecto
  `docs/registros/revisado.txt`) y hace commit. Viaja con el repo, así la ven tareas programadas y otras cuentas.
- `es-codigo.sh`: «código» es todo lo que no casa con `contenido` del config. Solo lo que es código pide revisión.
- `.github/workflows/comprobar.yml`: `instalar` + `check` en cada push que no sea a la rama protegida y en cada PR.

### 5.4 `/gw-init`, `/gw-update`, `/gw-doctor`

- **`/gw-init`**: pregunta lo mínimo (o lo deduce: `package.json`, `pyproject.toml`, `Cargo.toml`, `Makefile`…),
  escribe `.claude/gw.json` y copia las plantillas sin pisar nada que exista (si `CLAUDE.md` ya existe, propone un
  bloque para añadir y lo enseña antes). Añade a `.claude/settings.json` el marketplace y el plugin habilitado,
  más `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000`. Commit `Flujo Galivelop-workflow vX.Y.Z` y `Siguiente:`.
- **`/gw-update`**: compara la cabecera de versión de cada plantilla copiada con la del plugin; enseña el diff
  del cambio de plantilla (no del archivo, que el proyecto habrá rellenado) y aplica lo que el usuario confirme.
- **`/gw-doctor`**: comprueba y lista con la orden que arregla cada cosa: config válido contra el schema,
  `core.hooksPath`, `pre-push` ejecutable y de la versión actual, bitácora con sus secciones, `check` que existe,
  CI presente, plugin habilitado en `settings.json`.

## 6. El config del proyecto: `.claude/gw.json`

Todo lo que cambia de un proyecto a otro, y nada más. Lo lee solo `scripts/config.py` (un dato, un sitio).

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/zeldris/Galivelop-workflow/v1.0.0/schema/gw.schema.json",
  "version": "0.1.0",                       // versión del plugin con la que se generaron las plantillas
  "idioma": "es",                           // es | en: plantillas y lengua de las respuestas
  "idiomasVisibles": ["es", "gl", "en"],    // opcional: lo que REVIEW.md exige al texto visible
  "bitacora": "docs/traspaso.md",
  "ramaProtegida": "main",
  "subidaAProtegida": "directa",            // directa | pr: qué gancho vigila (pre-push o PreToolUse)
  "instalar": "npm ci",
  "check": "npm run check",
  "marca": "docs/registros/revisado.txt",
  "contenido": ["^docs/", "^public/", "^src/data/", "\\.md$"],   // regex: lo que NO pide /code-review
  "roadmap": false,                         // módulo opcional de hitos (Tarkor)
  "selector": { "casos": [] }               // filas extra propias del proyecto
}
```

> Las claves van en español por continuidad con los repos actuales; la Fase 0 puede decidir pasarlas a inglés
> antes de la `1.0.0` (después sería un cambio mayor).

Ejemplos que la Fase 5 tiene que cubrir: el portal (Node, subida directa, tres idiomas visibles) y Tarkor (backend
+ frontend, roadmap con hitos, varias cuentas). La Fase 7 añade uno que no sea Node (Python o Rust).

## 7. Versionado

- **SemVer** en `plugin.json`. Mayor: cambia el config o una plantilla de forma que pide tocar el repo destino.
  Menor: skill o gancho nuevo, o mejora compatible. Parche: arreglos.
- **`CHANGELOG.md`** (Keep a Changelog), una entrada por versión con `### ES` y `### EN`. El CI falla si la
  versión de `plugin.json` no tiene entrada.
- **Etiquetas `vX.Y.Z`** y release de GitHub con la entrada del CHANGELOG (`release.yml`).
- **Rama `main` = última versión publicada**; se trabaja en ramas y se sube a `main` solo con confirmación (el
  propio flujo).
- **Fijar versión en un proyecto**: el marketplace se añade con `#vX.Y.Z` cuando un proyecto no quiera
  actualizaciones automáticas. Lo normal: seguir `main` y `/plugin update`.
- Versión `0.x` durante todo el rodaje; `1.0.0` solo con la §10 cumplida.

## 8. Instalación en un proyecto (lo que contará `docs/<lang>/instalar.md`)

```text
/plugin marketplace add zeldris/Galivelop-workflow
/plugin install galivelop-workflow@galivelop-workflow
/galivelop-workflow:gw-init
```

`/gw-init` deja en `.claude/settings.json` del proyecto `extraKnownMarketplaces` y `enabledPlugins`, para que
cualquier sesión que abra el repo (otra cuenta, la nube) lo cargue sin pasos a mano.

> **A comprobar en la Fase 0** (no darlo por hecho): que una sesión en la nube instala un marketplace de un repo
> **privado** con el acceso de GitHub de la sesión. Si no puede, el plan B mientras sea privado es que
> `/gw-init` copie también las skills a `.claude/skills/` con cabecera de versión y `/gw-update` las refresque.
> Comprobar también los nombres exactos de campos de `plugin.json`, `marketplace.json` y `hooks.json` contra la
> documentación oficial de plugins de Claude Code del día.

## 9. Fases de construcción

Cada fase: rama de trabajo, pasos con commit + push en cada punto estable, bitácora en el mismo commit, tests en
verde, y al cerrar `/code-review` antes de subir a `main` (con confirmación). Modelo según el `selector` del
portal: diseño y ganchos con el grande; portar skills y plantillas con el medio.

| Fase | Qué | Hecho cuando |
|---|---|---|
| **0. Verificar** | Leer la doc oficial de plugins, marketplaces y hooks; probar en la nube un marketplace privado; anotar en `docs/investigacion/plugins.md` (skill `research`) | Las dudas de la §8 respondidas y el plan ajustado si hace falta |
| **1. Esqueleto** | Crear repo, `LICENSE`, `.claude-plugin/`, README ES/EN, `CLAUDE.md`, bitácora, CHANGELOG `0.1.0`, CI con shellcheck y validación JSON. Instalar el plugin desde local | `/plugin` lo lista y el CI está en verde |
| **2. Skills** | Portar las 14 skills (§3) y escribir `gw-doctor` | Todas cargan; `writing-for-agents` pasado a las propias; licencias y créditos en su sitio |
| **3. Ganchos y scripts** | `config.py`, `session-start.sh`, `recuperar.py`, `revision-antes-de-main.sh`, `es-codigo.sh`, `revisado.sh`, `medir.py` y plantilla `pre-push`, todo leyendo el config. `tests/test-ganchos.sh` contra un repo temporal, incluidos los casos de los 29 fallos del portal | Tests en verde en Linux y macOS (matriz del CI); fallan cerrado sin config |
| **4. Plantillas e init** | `templates/es` y `templates/en`, `gw.schema.json`, `gw-init`, `gw-update`, `test-plantillas.sh` | `gw-init` sobre un repo vacío deja un flujo que `gw-doctor` da por bueno; dos veces seguidas no cambia nada |
| **5. Piloto: Portal-Galivelop** | En una rama del portal (con permiso del usuario en esa sesión): sustituir su copia por el plugin + `gw.json`. Comparar comportamiento con el anterior | `npm run check` en verde, `pre-push` y marca de revisado funcionando, tarea semanal sin cambios. Lo que falte vuelve como versión nueva del plugin |
| **6. Piloto: Tarkor** | Igual en World-Maker-Fantasy, con `roadmap: true` | Relevo entre las dos cuentas con el plugin sin perder nada |
| **7. Rodaje** | Un proyecto que no sea Node; uso real semanas. Cada `retro` con mejora general → issue/PR aquí | Criterios de la §10 |
| **8. Público** | Revisión de seguridad (`/security-review`), quitar rutas o nombres privados, `1.0.0`, repo público, ficha en el portal Galivelop (tres idiomas, enlace al repo público), valorar npm (§11) | Repo público y ficha publicada |

## 10. Criterios para «100 % funcional y aplicable a cualquier sistema» (paso a 1.0)

- Funciona en **tres proyectos** de stacks distintos (al menos uno sin Node) durante **≥ 4 semanas** cada uno.
- **Relevos probados**: al menos 5 cortes de sesión (tokens, `/clear`, cambio de cuenta) sin pérdida, comprobado
  con la bitácora.
- **Ganchos**: ningún falso positivo ni subida sin revisar a `main` en el rodaje; tests de ganchos en Linux y
  macOS en verde. Windows: documentado (Git Bash o WSL) y probado al menos una vez.
- **Instalación limpia**: `gw-init` + `gw-doctor` en un repo nuevo sin tocar nada a mano.
- **Nada privado** en el repo: ni rutas de Tarkor o el portal, ni identificadores internos, ni datos personales.
- Documentación ES/EN completa y emparejada (lo comprueba el test).

## 11. npm (al final, opcional)

Paquete `galivelop-workflow` (o con ámbito `@galivelop/workflow`) con un binario `npx galivelop-workflow init`
que instala el marketplace y lanza el init para quien no quiera usar `/plugin`. Decidir en la Fase 8 si aporta algo
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
