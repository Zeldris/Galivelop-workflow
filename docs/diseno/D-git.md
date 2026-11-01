# D. Git: entornos, releases, tags, trazabilidad, roles

**Estado:** cerrado (2026-11-01): las 17 preguntas, decididas por el usuario. Se implementa según el mapa de
versiones (bloque H).

## Respuestas del usuario (2026-11-01)

- **1:** sí, «toveriai» es VeriNews_AI.
- **2:** el correo de `AGENTS.md` se queda (es el del usuario).
- **3:** las recogidas se revisan en la `1.0.0`, con el check de datos privados del bloque E.
- **4:** el historial no se reescribe; la regla vale de aquí en adelante.
- **6:** `worktree.baseRef: "head"` en el `settings.json` instalado, como arreglo en un parche `0.4.x`. Sale con la
  cadencia de A-6.
- **7 y 8:** según la recomendación.
- **9:** según la recomendación, y además el Management Center (bloque G) permitirá configurar los entornos y añadir
  otros nuevos según lo que necesite cada proyecto.
- **10, 11, 12, 15, 16 y 17:** según la recomendación.
- **5:** (a). Los `[NC]` se aceptan y cada uno se comprueba cuando se implemente la pieza que lo usa.
- **13:** el roadmap es la única fuente de ids, con un enlace opcional a una issue. Así funciona sin red, sin la API
  de GitHub y sin cuota de Actions; el gancho valida leyendo un archivo, y sirve igual para opencode y Codex.
- **14:** `trace.py <id>` calcula al momento lo que hay de un id: fila del roadmap, bitácora, commits, PR, documentos
  y lo deducido. No escribe ningún índice, y las comprobaciones solo se fían de lo declarado.

Fuentes: [`README.md`](README.md) (bloque D), las ideas para D de
[`ref-aider-graphify-worktrees.md`](../investigacion/ref-aider-graphify-worktrees.md) y el repaso del bloque F.

## Preguntas (se responden por número)

Cada punto lleva la recomendación del agente (**Rec.**).

### Lo que queda del bloque A (A-2)

1. **«toveriai»:** ¿es VeriNews_AI? **Rec.:** sí, y se apunta así en el plan.
2. **El correo de `AGENTS.md`** (el de `git config user.email`): (a) se queda, porque los commits ya lo muestran;
   (b) se cambia por el correo `noreply` de GitHub en el texto y en `git config`. **Rec.:** (b), en la `1.0.0`. El
   historial ya publicado sigue mostrando el correo de siempre.
3. **Las recogidas publicadas** (`docs/propuestas/`) que nombran proyectos privados: (a) se revisan ahora en un
   parche `0.4.x`; (b) se revisan en la `1.0.0`, con el check de datos privados del bloque E. **Rec.:** (b), salvo que
   lleven algo sensible (claves, datos de clientes). En ese caso, (a).
4. **El historial con autor Claude:** 155 commits, del 21 al 26 de octubre, tienen el autor
   `Claude <noreply@anthropic.com>`. Reescribirlos rompe todos los clones y las etiquetas publicadas. **Rec.:** no se
   reescriben; la regla vale de aquí en adelante, y el gancho `commit-msg` ya la vigila.

### Repaso del bloque F

5. **Datos sin confirmar:** algunas webs no resuelven desde el entorno (aider.chat, opencode.ai,
   developers.openai.com…). Lo que sale de ellas va marcado `[NC]` en las notas. **Rec.:** se aceptan así, y cada
   `[NC]` se comprueba cuando se implemente la pieza que lo usa.
6. **Worktrees:** por defecto, Claude Code crea el worktree de un subagente desde `main` (`worktree.baseRef: "fresh"`),
   no desde la rama de trabajo. Así, un subagente puede trabajar sobre código viejo sin que nadie lo vea.
   **Rec.:** el flujo fija `"head"` en el `settings.json` que instala, con su test. Como es un arreglo, puede ir en un
   parche `0.4.x`. ¿Parche o `1.0.0`?
7. **opencode y Codex:** los dos leen `AGENTS.md`, pero ninguno expande `@includes`. Las skills las encuentran en otras
   carpetas: opencode, en `.agents/skills`; Codex, en `~/.codex/skills`. **Rec.:** en una menor `1.x`, con dos cambios:
   un `AGENTS.md` que se entienda sin includes y una copia de las skills en `.agents/skills`. Los ganchos de opencode
   (plugins JS) se dejan para más adelante.
8. **Ideas de gstack y ECC:**
   - `/careful` y `/freeze` (modo restrictivo) → bloque C.
   - Perfiles de instalación `minimal`, `core` y `full` → bloque E.
   - Canal estable con un mínimo de horas entre versiones → ya lo cubre A-6.

   **Rec.:** se reparten así.

### Bloque D

9. **Entornos.** Opciones:
   - (a) como hoy: `main` y ramas de trabajo;
   - (b) `main` más una rama `dev` que integra;
   - (c) `dev`, `uat` y `prod`.

   **Rec.:** que lo elija cada proyecto, con `environments` en `gw.json`, y por defecto como hoy (a). Este repo sigue
   con (a) hasta que haya QA de verdad.
10. **Versiones por entorno:** si un proyecto usa `uat`, publica allí versiones previas (`v1.1.0-rc.1`) y la final en
    `main`. **Rec.:** sí, y sin ramas por versión.
11. **El tipo en la primera línea del commit:** `fix(B1): …`, `feat(D3): …`, con el texto en el idioma del proyecto.
    Sustituye al actual `Fase N: …`. Con eso, `version.py` sugiere el salto de versión (fix → parche, feat → menor,
    `!` → mayor) y avisa si no casa con el de `plugin.json`. Solo sugiere: la versión la confirma el usuario.
    **Rec.:** sí, con Conventional Commits.
12. **El id de tarea en un trailer:** una línea `Refs: D3` al final del commit, que el gancho `commit-msg` valida contra
    los ids del roadmap (`docs/roadmap.md`, A3) y de la bitácora. El nombre del trailer va en inglés, como las rutas
    (A-4). **Rec.:** sí, obligatorio en las ramas de trabajo, salvo en los merges.
13. **Tickets:** (a) el roadmap como única fuente de ids; (b) issues de GitHub. **Rec.:** (a), con un enlace opcional a
    una issue; el flujo hace la release a mano y no depende de la API de GitHub.
14. **Trazabilidad:** una orden `trace.py <id>` que, en el momento, junta todo lo de un id: fila del roadmap, filas de
    la bitácora, commits, PR y documentos que lo citan. Separa lo declarado (trailer, id escrito) de lo deducido (mismo
    archivo tocado). No guarda un índice, para no tener el dato en dos sitios. **Rec.:** sí.
15. **Un trailer de agente sin modelo:** `Agent: orchestrate-dealer`, para saber qué commits hizo un subagente. No es
    una firma: ni nombre de modelo ni enlace de sesión. **Rec.:** sí, opcional, y el gancho rechaza cualquier valor
    que nombre un modelo.
16. **Rama de subagente con la tarea en el nombre** (`agent/D3-<tema>`), y `fusionar.sh` copia `Refs: D3` al commit
    de fusión. **Rec.:** sí.
17. **Roles** (`DEV` → `dev`, `QA` → `uat`, `ADMIN` → todo; cuentas de GitHub en `gw.json`): **Rec.:** el esquema se
    diseña ahora y se implementa con el MMC (bloque G). Hasta entonces, el único rol es `ADMIN`, que es lo de hoy.
