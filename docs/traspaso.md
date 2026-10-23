# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-6dfbc880-ddr41g` (avance rápido de `ccr-76251061-b1yiwq`, que sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `01d1a75` = **release `v0.2.0`** (2026-10-22, etiqueta y release creadas a mano en GitHub); `v0.1.0` = `9b97d7b` |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **6 cerrada** (2026-10-23): propuestas de los dos pilotos aplicadas (tandas A-G) y versión `0.3.0` en la rama, sin publicar; P7 del instalador (CI pasado en local) aplazada para hablarla con el usuario. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **Versión `0.3.0`** con los arreglos de la fase 1 antes de `main` (code review contra `origin/main`); check en verde en local; el CI no arranca (cupo de Actions) |
| Siguiente paso | Con el visto bueno del usuario: las tres fases antes de `main` (fase 1 hecha y sus arreglos revisados; luego `/opt-tokens` + `/retro`, `revisado.sh`) y publicar `0.3.0`; hablar la P7 del instalador; luego la Fase 7 |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [x] 6. Piloto: Tarkor e instalador (2026-10-23; VeriNews, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.2.0` publicada (etiqueta y release a mano en GitHub, título `Galivelop-workflow vX.Y.Z`, notas de la entrada del CHANGELOG). Para la siguiente: `release.yml` con lanzamiento manual desde Actions que cree la etiqueta (la
sesión en la nube no puede subir etiquetas: 403 del proxy).

## Hecho (10 últimas)

1. 2026-10-23 — Revisión de los arreglos antes de `main` (3b47af1): la carpeta de worktrees del `pre-push` es por
   usuario (`gw-pre-push-wt-<uid>-<id>`), con permisos 700, y se rechaza si es un symlink o de otro usuario (`/tmp`
   es de todos); `config.md` dice que cambiar `worktreeDir` deja la carpeta anterior sin limpiar. Tests en
   `test_ganchos.py` (97 OK). Menores, en «Pendiente».
2. 2026-10-23 — Fase 1 antes de `main` (arreglos del `/code-review` contra `origin/main`): el `pre-push` crea el
   worktree en `${TMPDIR:-/tmp}/gw-pre-push-wt-<id>` (id = `cksum` del git-dir común) o bajo la clave nueva
   `worktreeDir`, nunca dentro de `.git/` (jest), y solo borra huérfanos de más de 24 h con el proceso muerto;
   `rojo-sin-arreglo.sh` rechaza una regex inválida antes de tocar nada; `revisado.sh` veta las palabras pendientes
   solo como palabra entera; `revision-antes-de-main.sh` comprueba el acceso leyendo el repo (`gh api repos/o/r`,
   vale con token de GitHub App) y juzga como abierto un update que reabre el PR; `compare.py` toma la raíz de su
   ruta o de git, nunca del directorio actual; `opt-ai/medir.py` cuenta la recuperación dentro del turno; el aviso
   de veredictos repetidos de `quality_bench.py` dice que cuenta el primero. Un caso por arreglo; copias
   resincronizadas; check en verde.
3. 2026-10-23 — Tanda G y cierre de la Fase 6: versión `0.3.0` (`version.py`), entrada del CHANGELOG ES/EN con las
   propuestas de los dos pilotos, marcas de `.claude/gw/*.md` y `.claude/gw.json` a `0.3.0`.
4. 2026-10-23 — Tanda F (instalador P5, P8, P9): plantillas con «la persona»/«the person» (sin clave nueva);
   `aplicar.md` ↔ `apply.md` (`.gitignore` con `.claude/*`, scripts del flujo no se editan en el proyecto, migrar:
   skills sustituidas, ganchos viejos, `recuperar.py`, `install` a mano) y `REVIEW.md` ES/EN. El `add_repo` (paso 0) y
   el clasificador (paso 2) ya estaban donde se pedía.
5. 2026-10-23 — Tanda E, arreglos de la revisión de 972ca92: `quality_bench.py summary` cuenta cada par una vez
   (`judged`/`x_bias`; `repeated` = pares repetidos) y, si `pairs.jsonl` no casa con la clave, sale diciendo que se
   regenere con `pairs --seed`; `opt-ai/medir.py` cuenta en `error_pct` los turnos fallidos sin tiempo; `scout_dir`
   con config ilegible, con test. Copias resincronizadas, check en verde.
6. 2026-10-23 — Tanda E de las propuestas aprobadas (skills): cada `SKILL.md` lee `.claude/gw/<skill>.md` si existe
   (una línea tras el título; regla en `writing-for-agents/SKILL-MECHANICS.md`). `opt-tokens/medir.py` avisa con
   `--hours 0` si la sesión mezcla ventanas de compactación (tramos cerrados con picos que difieren más de 1,5x) y
   gana `test_medir.py` (los 8 casos de WMF adaptados, más el del aviso). `opt-ai/medir.py` gana la tabla por turno
   (`app.turn`, con `ts`), con 3 casos. `scout-updates`: `compare.py` entiende los títulos en español (`sello`,
   `Restricciones`, `Cobertura`, `Componente`) y la ruta de `architecture.md` sale de la clave nueva `scoutDir`
   (esquema, `config.py get`, `config.md` ES/EN; por defecto `.claude/gw/scout`). El banco de calidad por pares de WMF
   se porta como `scripts/quality_bench.py` (en inglés, con 7 casos) y entra como herramienta opcional del paso 5.
   `aplicar.md` ↔ `apply.md` dicen cómo se descubren las pruebas de las skills. Copias resincronizadas. Los marcadores
   de `.claude/gw/*.md` (v0.1.0) siguen avisando de plantilla nueva: es de la versión, no de esta tanda.
7. 2026-10-23 — Tanda D de las propuestas aprobadas: `ciInstall` (la plantilla de CI lo usa y, si la clave no está, cae
   a `install`; un `[]` explícito no instala nada; no está en `templates/gw.json` a propósito); `setup` (órdenes que
   `session-start.sh` corre en la nube justo después de `install`, en orden y con el mismo sello; una que falla o pasa
   de `GW_COMMAND_TIMEOUT` s, 900 por defecto, se cuenta con la orden a mano y el gancho sale 0); `doctor.py` solo
   propone `comprobar.yml` si ningún workflow corre el `check` (y avisa de un `setup` que no existe); `staleRefs`
   acepta además `{patterns, skip}` con globs que `enlaces-md.py` no lee; `linkRoots` (carpetas cuyos enlaces
   resuelven desde la raíz) y una línea en `skills/pr`; `config.py` gana `stale_refs()` y `glob_regex()`. `aplicar.md`
   ↔ `apply.md` explican el paso `pre-commit --rango` suelto. Casos en `test_utilidades`, `test_sesion`, `test_doctor`,
   `test_config`, `test_plantillas`; copias resincronizadas.
   Revisión de 86afc95 (arreglada): el límite de `session-start.sh` es un vigilante en bash portable (sin `timeout`,
   mata el grupo de procesos, «timed out» solo si disparó el vigilante); `glob_regex` acepta rutas sin comodines y
   `docs/**` incluye `docs`; `doctor.py` ignora comentarios y exige frontera tras la orden; la plantilla de CI cae a
   `install` solo si falta `ciInstall`; `enlaces-md.py` resuelve `/x` desde la raíz y avisa de enlaces fuera del repo.
8. 2026-10-23 — Tanda C de las propuestas aprobadas: claves `checkWrapper` (prefijo literal de cada `check` y
   `relatedTests`; con `cwd`, `bash -c 'cd … && …'`) y `worktreeLinks` (por defecto `node_modules`, `.venv`);
   `relatedTests` acepta `{command, paths, cwd}` además del texto; el `pre-push` crea el worktree en
   `<git-dir común>/gw-pre-push/wt.XXXXXX.d` (no en `$TMPDIR`), lo borra en toda salida (INT/TERM/HUP), limpia los
   huérfanos de pushes muertos y deja un registro `mktemp` por orden (solo si falla); arreglado un fallo real: en un
   worktree enlazado git define `GIT_DIR` y la raíz salía mal (ahora se quita antes). `fusionar.sh` y `doctor.py`
   adaptados; casos en `test_ganchos` (worktree, enlaces con espacios, enlazado, wrapper, logs, concurrencia,
   huérfanos, señales, bash 3.2), `test_config`, `test_utilidades`, `test_doctor`; docs ES/EN; copias resincronizadas.
   Queda para la tanda D: la plantilla de CI no aplica `checkWrapper`.
   Revisión de 758a5ea (arreglada): enlaces de `worktreeLinks` que salen del worktree por un symlink commiteado (falla
   cerrado), sin `git worktree prune` global, marcador vacío y EPERM cuentan como vivos, `checkWrapper` siempre
   `<wrapper> bash -c '<orden>'` (pre-push, `fusionar.sh`, `config.py related`).
9. 2026-10-23 — Tanda B de las propuestas aprobadas: `revisado.sh` ignora lo no seguido, lee todo el párrafo de
   `**Estado:**`, acepta «aprobad*», lista las palabras válidas en el error y admite `--footer` (la skill `retro`
   fija la forma de la línea); `pre-commit` quita `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` antes de buscar la raíz
   (worktree enlazado); `revision-antes-de-main.sh` sale pronto sin python3 salvo en llamadas de PR, comprueba el
   acceso con `gh api user` y avisa si el PR ya está cerrado o fusionado; `es-codigo.sh` distingue una regex
   `content` inválida de otros fallos (BrokenPipe); casos en `tests/test_ganchos.py` y `tests/test_revision_main.py`,
   docs ES/EN y copias `.claude/gw/` resincronizadas.
10. 2026-10-23 — Tanda A de las propuestas aprobadas: `taskId` con grupos de captura se normaliza (`config.non_capturing`,
   lo usa `bitacora.py`; ya no rompe `closed`); `doctor.py` acepta «Siguientes pasos», reconoce un gancho del flujo por
   su cabecera (un `session-start.sh` propio no avisa), añade `reviewMark` a lo que git no debe ignorar (`aplicar.py`
   comparte ambas funciones) y avisa de términos repetidos en `GLOSSARY.md`; `bitacora.py closed` solo da por apuntada
   una tarea tachada en «Hecho» o nombrada en línea con fecha, y `check` falla con una fila «Tarea en curso» sin rama;
   `rojo-sin-arreglo.sh --ran-one REGEX` (exactamente una línea de test ejecutado). 10 casos; guías ES/EN.
   Revisión: `closed` cuenta también las líneas de continuación sangradas de la entrada con fecha (arreglado).

## Pendiente

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Menores de la revisión de la tanda A (no se revisan otra vez en este PR): `non_capturing` toca paréntesis en
  comentarios `(?x)`/`(?#…)`; `--ran-one` cuenta dos veces si el ejecutor repite el nombre del test en el resumen;
  `header_version` solo mira las 5 primeras líneas.
- Menores de la revisión de la tanda B: sin python3, `revision-antes-de-main.sh` deja pasar `gh pr<TAB>create` y
  `gh api …/pulls -f title=` (crear el PR por la API; el hueco ya existía) y bloquea `gh pr view 3 && echo create`
  (exceso de celo).
- Menores de la revisión del vigilante (89fdf09): el KILL de los 5 s podría dar con un pgid reutilizado (se acepta:
  el vigilante se detiene si la orden acaba antes).
- Menores de la revisión de la tanda E: el aviso de ventanas mezcladas de `opt-tokens/medir.py` salta con un
  `/compact` manual o una etapa muy corta; `opt-ai/medir.py` ignora un `app.turn` 0 o vacío y su clave sintética
  choca con una tarea llamada «turn»; `instant` descarta sin avisar un `ts` que `fromisoformat` no lee (Python <3.11);
  `quality_bench.py` envía un `format` de texto como `json_schema` con la API openai y `pairs` pisa en silencio un
  modelo repetido en dos `outputs.jsonl`.
- Menor de la revisión antes de `main`: `checkWrapper` se aplica en tres sitios (`pre-push` y `fusionar.sh` con
  `sed`, `config.py` con `shlex`) y la plantilla de CI no lo aplica: que lo construya solo `config.py`.
- Menores de la revisión de los arreglos antes de `main` (3b47af1): un push muerto en el mismo namespace deja su
  worktree 24 h (guardar `hostname:pid` en el marcador); `worktreeDir` con `~` o `..` no se valida en `config.py`;
  `cksum` de 32 bits puede juntar dos repos en una carpeta (el borrado sigue exigiendo 24 h y proceso muerto);
  `update_pull_request` con `state:open` y sin `base` no se juzga como reapertura; `compare.py default_root` da
  traceback sin git y, desde la caché del plugin, cae al cwd (exigir `--root`).
- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.
- La `1.0.0` solo como plugin (decidido 2026-10-22): en la Fase 9, plugin como única distribución hacia fuera y
  ganchos de git desde el plugin (sin probar); en la Fase 10, licencia de la `1.0.0` (abierta) y el portal quita su
  copia del flujo desde una sesión suya. Su historial seguirá teniendo la copia `0.2.0` (MIT).

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
