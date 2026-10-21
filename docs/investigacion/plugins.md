# Fase 0 — Plugins, marketplaces y hooks de Claude Code

> Investigación del 2026-10-21 con Claude Code **2.1.306**. Fuentes: la documentación oficial en
> `code.claude.com/docs/en/` (páginas citadas en cada punto) y pruebas reales en un contenedor de la nube. Responde a
> las dudas de la §8 del plan. Lo marcado **[probado]** se ha comprobado a mano; lo marcado **[doc]** sale solo de la
> documentación.

## Resumen

| Pregunta (plan §8) | Respuesta |
|---|---|
| ¿Un repo privado se puede añadir como marketplace? | **Sí**, desde la CLI, con las credenciales de git que ya tenga la máquina. En el contenedor de la nube funciona a través del proxy de GitHub de la sesión **[probado]** |
| ¿Una sesión en la nube carga el plugin declarado en `.claude/settings.json` del repo? | **No.** Ni privado ni público: la nube ignora `extraKnownMarketplaces`/`enabledPlugins` del repo **[doc + probado]** |
| ¿Carga en la nube lo que está en `.claude/skills/` del repo? | **Sí [probado]** |
| ¿Sirve instalar el plugin desde un gancho `SessionStart`? | **No en la nube:** se instala, pero solo lo ve la *siguiente* sesión del mismo contenedor, y en la nube cada sesión estrena contenedor **[probado]** |
| ¿Son correctos los nombres de campos del plan? | Sí, con los matices de la sección «Formato» de abajo **[doc]** |
| ¿Existe `CLAUDE_CODE_AUTO_COMPACT_WINDOW`? | Sí: la cadena está en el binario 2.1.306. Falta confirmar su semántica en la doc |

**Consecuencia:** la idea de la §2 («basta una línea en `.claude/settings.json` para que cualquier sesión, también
en la nube, lo cargue») **no se sostiene**. El plan B de la §8 deja de ser solo para el periodo privado y pasa a ser
**necesario para la nube siempre**. Ver «Propuesta» al final; no se ha cambiado ninguna decisión del plan.

## Pruebas realizadas

1. **Repo privado como marketplace desde la CLI de la nube.** Con `.claude-plugin/marketplace.json` y `plugin.json`
   mínimos en la rama: `claude plugin marketplace add "Zeldris/Galivelop-workflow#claude/galivelop-workflow-inicio"`
   → `Successfully added marketplace`; `claude plugin install galivelop-workflow@galivelop-workflow` → instalado,
   versión `0.0.1`. Una sesión `claude -p` nueva ve la skill `galivelop-workflow:gw-ping`.
2. **Sesión en la nube nueva sobre el repo** (sesión hija, solo lectura). Con `.claude/settings.json` declarando el
   marketplace y el plugin: `claude plugin list` → `No plugins installed`; marketplace no registrado; sin error
   «enabled in project settings but isn't installed here». La skill de `.claude/skills/gw-ping-local` **sí** carga.
3. **Instalación desde `SessionStart`.** Un gancho de proyecto que hace `marketplace add` + `install`: la sesión que
   lo ejecuta responde `NONE`; la siguiente sesión del mismo contenedor ve `galivelop-workflow:gw-ping`.
4. **Validación.** `claude plugin validate .` y `claude plugin validate .claude-plugin/marketplace.json` pasan
   con `source: "./"` (el repo es su propio marketplace y su propio plugin).

## Hallazgos por tema

### Carga en la nube [doc]

- «A cloud session doesn't add the marketplaces a repository lists under `extraKnownMarketplaces`, because that
  requires the workspace trust dialog, which a cloud session never shows.» (`/plugins/loading`)
- «Plugins declared in the repository's `.claude/settings.json` and plugins enabled only in your user settings don't
  load in cloud sessions.» (`/skills`)
- Las sesiones en la nube no leen `~/.claude/settings.json` ni `.claude/settings.local.json` (`/settings`).
- Lo que **sí** carga la nube: `.claude/skills/`, `.claude/agents/`, `.claude/commands/` del repo («Part of the
  clone») y los ganchos y permisos de `.claude/settings.json`, **pero solo en una sesión con un único repositorio**:
  «a session with several repositories doesn't load hooks from any repository's `.claude/settings.json`»
  (`/cloud-environments`). Las skills de proyecto tampoco cargan en «cloud threads in a project» (`/skills`).
- Las skills que el usuario habilita **en su cuenta de claude.ai** se cargan solas en las sesiones en la nube
  (`/cloud-environments`, `/skills`). Los *plugins* sincronizados desde claude.ai solo constan para terminal y Cowork,
  no para la nube (`/plugins/loading`).
- El **script de configuración del entorno** (setup script) corre «when a new cloud session starts, before Claude Code
  launches» (`/cloud-environments`). La doc no dice que `claude plugin install` funcione ahí, pero la prueba 1 muestra
  que un plugin instalado antes de arrancar sí carga. `/plugin` no está disponible en la nube.
- Acceso a GitHub en la nube: las credenciales se quedan en los servidores de Anthropic y un proxy las añade
  (`/claude-code-on-the-web`). Por eso la prueba 1 funcionó sin token en el contenedor.

### Carga en local [doc]

- `extraKnownMarketplaces` del proyecto solo se aplica **después de confiar en la carpeta**.
- Un plugin habilitado en el `settings.json` del proyecto pero no instalado en esa máquina **no se descarga solo**:
  `/plugin` muestra el error `Plugin "<name>" is enabled in project settings but isn't installed here`. Solo se
  descarga si lo habilitan los ajustes de usuario, `settings.local.json`, `--settings` o ajustes gestionados.
  → El «sin pasos a mano» de la §8 tampoco es cierto en local: cada máquina hace `/plugin install` una vez.
- Repo privado en local: Claude Code ejecuta `git` sin prompts con las credenciales de la máquina (SSH con agente o
  helper HTTPS, p. ej. `gh auth setup-git`). `GITHUB_TOKEN` en el entorno no basta por sí solo para la actualización
  en segundo plano; hace falta un helper que lo lea (`/plugins/host-marketplace`).

### Formato [doc]

- **`plugin.json`** en `.claude-plugin/plugin.json`; solo `name` es obligatorio (kebab-case). Campos del plan
  válidos: `version`, `description`, `author` (objeto con `name`), `license` (SPDX), `homepage`, `repository`,
  `keywords`. Componentes por defecto: `skills/<nombre>/SKILL.md`, `hooks/hooks.json`, `commands/`, `agents/`,
  `bin/` (se añade al PATH del Bash). Rutas en el manifiesto relativas y empezando por `./`; nada fuera de la raíz.
- **`marketplace.json`** en `.claude-plugin/marketplace.json`; obligatorios `name`, `owner.name`, `plugins[]` (cada
  uno con `name` y `source`). `source: "./"` es el propio repo **[probado]**. El nombre `galivelop-workflow` no está
  reservado.
- **Versión:** manda `version` de `plugin.json`; si no hay, la del marketplace; si tampoco, el sha (12 caracteres).
  La doc pide **no** ponerla en los dos sitios → el plan ya la pone solo en `plugin.json`. ✔
- **Fijar versión:** `owner/repo#ref` (o `@ref`) al añadir el marketplace; en `settings.json`, `source.ref` / `sha`. ✔
- **`hooks/hooks.json`:** el mapa de eventos va **dentro de una clave `"hooks"`** de primer nivel; sin ella no carga.
  Gancho `{"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/x.sh"}` o forma exec con `args`.
- **Matchers:** `SessionStart` admite `startup`, `resume`, `clear`, `compact`, `fork`. Herramientas MCP:
  `mcp__<servidor>__<herramienta>`; un matcher con solo letras, dígitos, `_`, `-` y `|` es lista exacta
  (`mcp__github__create_pull_request|mcp__github__merge_pull_request|Bash`); con otros caracteres es regex sin anclar.
- **Decisión en `PreToolUse`:** JSON con `hookSpecificOutput.permissionDecision: "deny"` y motivo, o exit 2 con el
  motivo en stderr. Callar (exit 0 sin salida) no aprueba. `SessionStart` no puede bloquear; su stdout pasa al
  contexto (encaja con `recuperar.py --estado`). `CLAUDE_ENV_FILE` sirve para exportar variables desde `SessionStart`.
- **Variables:** `${CLAUDE_PLUGIN_ROOT}` (cambia con cada versión: el plugin se copia a
  `~/.claude/plugins/cache/<mkt>/<plugin>/<versión>/`), `${CLAUDE_PLUGIN_DATA}` (persiste entre versiones),
  `CLAUDE_PROJECT_DIR`. `CLAUDE_CODE_REMOTE="true"` en la nube. ✔ con §4.3 (raíz del proyecto por
  `git rev-parse --show-toplevel`).
- **`SKILL.md`:** `name`, `description`, `when_to_use`, `argument-hint`, `disable-model-invocation` (útil para
  `gw-init`/`gw-update`: que solo se lancen a mano), `allowed-tools`, `model`, `effort`, `context: fork`, entre otros.
  Campos desconocidos se ignoran.

## Propuesta (pendiente de tu decisión)

La distribución como plugin solo funciona en local. Como el taller trabaja mucho en la nube, propongo:

- **Opción A — Copia gestionada como vía principal.** El repo mantiene la forma de plugin + marketplace (vale para
  local y para cuando sea público), pero `/gw-init` **copia** al repo destino lo que la nube necesita: skills en
  `.claude/skills/<skill>/` y scripts en `.claude/gw/scripts/`, todo con cabecera `galivelop-workflow vX.Y.Z`, y los
  ganchos en `.claude/settings.json` del proyecto (que la nube sí ejecuta). `/gw-update` (también copiado) trae la
  versión nueva desde este repo y enseña el diff; `/gw-doctor` avisa si la copia diverge. Sigue habiendo **una sola
  fuente** (este repo); la copia es generada, no editada a mano. *Recomendada.*
- **Opción B — Solo plugin + ajustes de usuario.** No sirve para la nube. Descartable.
- **Opción D — Plugin instalado por el script de configuración del entorno.** Una línea en el setup script de cada
  entorno de la nube (`claude plugin marketplace add Zeldris/Galivelop-workflow && claude plugin install
  galivelop-workflow@galivelop-workflow`). Ventajas: una sola vía (el plugin), sin copias, y los ganchos del plugin
  no dependen de que la sesión tenga un solo repo. Inconvenientes: se configura **por entorno y por cuenta**, no por
  repo (`/gw-init` no puede escribirlo, solo indicarlo), y falta probar que el setup script puede clonar el repo
  privado antes de que arranque Claude. Probarlo requiere que tú añadas esa línea a un entorno.
- **Opción C — Ambas a la vez en un mismo repo** (plugin en local + copia): duplicaría skills y ganchos en las
  sesiones locales. Si se quiere el plugin en local, `/gw-init` debería elegir una de las dos vías por repo.

Mi recomendación tras la segunda consulta: **probar D primero** (si funciona, es la vía más limpia y coincide con
la decisión original de plugin) y dejar **A como respaldo** para quien no controle el entorno. Ojo con A: sus
ganchos no corren en sesiones con varios repos, que es justo el caso de una sesión que trae otro repo como lectura.

Efectos en el plan si eliges A: §2 (motivo del plugin), §4 (`scripts/` debe funcionar tanto desde
`${CLAUDE_PLUGIN_ROOT}` como desde `.claude/gw/scripts/`), §5.4 (`gw-init`/`gw-update` copian skills y scripts),
§7 (fijar versión = la cabecera de la copia), §8 (instalación en la nube: `gw-init` desde una sesión con este repo
añadido), y el plan B de la §8 deja de ser provisional.

### Otras decisiones que salen de la Fase 0

- **Claves de `gw.json` en inglés.** Hoy ningún repo tiene `gw.json`, así que la «continuidad» no cuesta nada y,
  después de la `1.0.0`, cambiarlas sería un cambio mayor. Propuesta: `language`, `visibleLanguages`, `log`,
  `protectedBranch`, `pushToProtected` (`direct`|`pr`), `install`, `check`, `reviewMark`, `content`, `roadmap`,
  `selector.cases`. *Pendiente de tu decisión.*
- **`gw-init` y `gw-update` con `disable-model-invocation: true`**, para que el modelo no los lance solo.
- **`hooks.json`** con clave `"hooks"` y matchers exactos del MCP de GitHub (arriba).

## Pendiente de verificar

- Opción D: que el setup script del entorno clona el repo privado e instala el plugin (necesita que el usuario
  edite un entorno). `CLAUDE_CODE_SYNC_PLUGINS` existe en el binario pero no en la doc; no se usa.
- Semántica exacta de `CLAUDE_CODE_AUTO_COMPACT_WINDOW` en la doc.
- Las skills de prueba `gw-ping` y `gw-ping-local` se quitan al cerrar la Fase 0.
