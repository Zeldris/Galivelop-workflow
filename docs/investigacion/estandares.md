# Fase 0 — Estándares, mejoras y problemas conocidos

> Revisión del 2026-10-21 pedida por el usuario antes de cerrar la Fase 0: qué estándares abiertos conviene seguir,
> qué mejoras traen y qué fallos típicos hay que prever. Fuentes primarias marcadas **[1ª]**; blogs y guías de
> terceros marcados **[3ª]** (pistas, no hechos). `agents.md`, `agentskills.io` y `copier.readthedocs.io` no
> resuelven desde este contenedor; se leyeron sus fuentes en GitHub.

## 1. Estándares que aplican

### AGENTS.md (instrucciones para cualquier agente)

- Formato abierto, «a README for agents», Markdown sin campos obligatorios, en la raíz; admite archivos anidados
  (manda el más cercano) **[1ª: github.com/agentsmd/agents.md; 3ª para el anidado]**. Lo custodia la Agentic AI
  Foundation (Linux Foundation) y lo leen Codex, Cursor, Copilot, Gemini, Amp, opencode… **[3ª]**
- Claude Code lo lee **solo si no hay `CLAUDE.md`**; si hay los dos, lee solo `CLAUDE.md`. Recomendación oficial:
  `AGENTS.md` como archivo compartido y un `CLAUDE.md` con `@AGENTS.md` más lo propio de Claude. Un enlace simbólico
  sirve, pero Edit/Write no escriben a través de él y se rompe en Windows **[1ª: code.claude.com/docs/en/memory]**.
- `CLAUDE.md`: objetivo «under 200 lines». Las importaciones `@ruta` **no** ahorran contexto **[1ª]**.
- `.claude/rules/*.md` con `paths:` (globs) carga reglas solo al tocar esos archivos **[1ª]**.

**Mejora:** las reglas del flujo (relevos, commits, ramas, revisión) van en `AGENTS.md`; el `CLAUDE.md` de la
plantilla queda en `@AGENTS.md` + lo específico de Claude (skills, `/code-review`, compactación). El flujo deja de
depender de un solo agente, y la etapa 1 (abajo) se apoya justo en eso. Las reglas de «Ganchos y scripts» de
`REVIEW.md` pueden ir a `.claude/rules/` con `paths:` sobre los ganchos.

### Agent Skills (formato abierto de `SKILL.md`)

Especificación **[1ª: github.com/agentskills/agentskills, `docs/specification.mdx`]**:

| Campo | Regla |
|---|---|
| `name` | Obligatorio, 1–64, minúsculas, dígitos y guiones; sin guion al principio/final ni `--`; igual que la carpeta |
| `description` | Obligatorio, 1–1024 caracteres; qué hace **y cuándo** usarla |
| `license` | Opcional (p. ej. `MIT` o archivo incluido) |
| `compatibility` | Opcional, ≤500; requisitos del entorno («Requires git, bash and python3») |
| `metadata` | Opcional, mapa texto→texto (sitio natural para `version`) |
| `allowed-tools` | Opcional, experimental |

Carpetas opcionales `scripts/`, `references/`, `assets/`; carga progresiva; `SKILL.md` «under 500 lines» (el plan pide
<200: más estricto, se mantiene). Lo adoptan Claude Code, Codex, Gemini CLI, Copilot, VS Code, Cursor… **[3ª]**

**Mejora:** cada skill lleva `license` (MIT, y la atribución de mattpocock), `compatibility` y
`metadata.version: X.Y.Z` (sustituye a la «cabecera de versión» del plan, §5.4). Un test valida nombre y longitudes.

### Copier (plantillas que se pueden **actualizar**)

**[1ª: github.com/copier-org/copier, `docs/updating.md`]**

- `copier copy` genera desde una plantilla (git, con etiquetas) y guarda las respuestas en `.copier-answers.yml`.
- `copier update` hace un **merge a tres bandas**: regenera con la versión vieja y tus respuestas, calcula tus cambios,
  genera la nueva y los reaplica. Lo que choca queda con marcas de conflicto (`--conflict inline`) o en `.rej`.
- Exige repo git con `git status` limpio. Tiene migraciones antes/después por versión. «Never update
  `.copier-answers.yml` manually».
- Recomienda un gancho que impida commitear marcas de conflicto o `.rej`.

**Mejora:** Copier resuelve exactamente lo que el plan pide a `/gw-update` («diff del cambio de plantilla, no del
archivo que el proyecto rellenó») sin IA. Coste: depende de Python (`pipx`/`uvx copier`). Candidato para la etapa 2.

### Ganchos de git sin gestor

Husky ata a `package.json`; Lefthook es un binario Go; pre-commit es Python con muchos ganchos de terceros **[3ª]**.
El flujo solo necesita un `pre-push`: **`core.hooksPath` nativo** sigue siendo lo más portable (sin dependencias,
cualquier stack). Pero hay que convivir con ellos (ver §3).

### Otros que ya estaban en el plan

SemVer, Keep a Changelog, etiquetas `vX.Y.Z` y una sola fuente de versión (`plugin.json`; la deriva entre
`plugin.json` y `marketplace.json` es el fallo típico de los marketplaces **[3ª]**; la doc oficial dice no ponerla en
los dos **[1ª]**).

## 2. Mejoras propuestas para el flujo

1. **`AGENTS.md` como fuente de las reglas** y `CLAUDE.md` = `@AGENTS.md` + lo de Claude (arriba).
2. **Skills según Agent Skills** (`license`, `compatibility`, `metadata.version`) y test de validación.
3. **`gw-doctor` como script** (`scripts/doctor.sh`/`.py`), no como skill: comprobación determinista con la orden
   que arregla cada cosa. La skill solo lo llama. Lo mismo para todo lo mecánico de `gw-init`.
4. **El `pre-push` rechaza marcas de conflicto y `.rej`** (lección de Copier; también sirve para merges a mano).
5. **Historia superficial:** los clones de la nube son superficiales (`--depth`). Las comprobaciones «la marca es
   antecesora de HEAD» (`git merge-base --is-ancestor`) fallan si falta historia. Deben fallar cerradas **con la
   orden concreta** (`git fetch --deepen=200 origin <rama>`), y los tests deben cubrir un clon superficial.
6. **Convivir con otros gestores de ganchos:** si `core.hooksPath` ya apunta a otro sitio (Husky `.husky/`), no
   pisarlo; `gw-doctor` lo detecta y explica cómo encadenar el `pre-push` del flujo.
7. **Guía de problemas conocidos** (`docs/es/problemas.md` / `docs/en/troubleshooting.md`), con lo de §3.

## 3. Problemas conocidos (para la guía)

| Síntoma | Causa | Arreglo |
|---|---|---|
| Un gancho de Claude no se ejecuta | JSON inválido, evento o matcher mal escrito (distinguen mayúsculas; `bash` ≠ `Bash`), archivo de ajustes equivocado, sesión sin reiniciar **[3ª]** | `/hooks` para ver lo cargado; `jq . .claude/settings.json`; reiniciar la sesión |
| «No pasa nada» con exit 0 | Exit 0 sin salida no se ve ni aprueba **[1ª]** | Registrar en un log para depurar; para bloquear, exit 2 o `permissionDecision: deny` |
| El gancho no bloquea | Puesto en `PostToolUse` o `SessionStart`, que no pueden bloquear **[1ª]** | `PreToolUse` |
| En la nube no corren los ganchos del proyecto | Sesión con varios repos **[1ª]** | Una sesión, un repo; o ganchos desde el plugin (opción D) |
| En la nube no aparece el plugin | La nube ignora `extraKnownMarketplaces` del repo **[1ª + probado]** | Copia en el repo (A) o instalarlo en el script del entorno (D) |
| Marketplace privado falla en local | Sin credencial de git no interactiva **[1ª]** | `gh auth login && gh auth setup-git`, o SSH con agente |
| El script no encuentra el repo | La nube arranca en `/home/user`; `$CLAUDE_PROJECT_DIR`/cwd no son la raíz | Raíz desde la ruta del script o `git rev-parse --show-toplevel` |
| «La marca no es antecesora» sin motivo | Clon superficial | `git fetch --deepen=200 origin <rama>` |
| El `pre-push` no se ejecuta | `core.hooksPath` sin poner, o lo puso otro gestor; falta el bit de ejecución (Windows) | `git config core.hooksPath .githooks`; `git update-index --chmod=+x .githooks/pre-push` |
| Fallos raros en Windows | CRLF en scripts, enlaces simbólicos | `.gitattributes` con `*.sh text eol=lf`; Git Bash o WSL; sin enlaces simbólicos |
| `CLAUDE.md` existe y `AGENTS.md` no se lee | Claude solo lee `AGENTS.md` si no hay `CLAUDE.md` **[1ª]** | `@AGENTS.md` en `CLAUDE.md` |

## 4. Propuesta del usuario: dos etapas

> **Decidido (2026-10-21):** el usuario aprobó las propuestas; ver `docs/plan.md` §0.

**Etapa 1 — un agente aplica el flujo leyendo este repo.** **Etapa 2 — instalación automática sin IA**, para
proyectos nuevos (lo recomendado) y existentes. Aprobada con la copia en el repo como base de la etapa 1, reglas
en `AGENTS.md` y scripts deterministas para todo lo comprobable (`docs/plan.md` §0 y §9).
