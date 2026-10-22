# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-6dfbc880-ddr41g` (avance rápido de `ccr-76251061-b1yiwq`, que sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `01d1a75` = **release `v0.2.0`** (2026-10-22, etiqueta y release creadas a mano en GitHub); `v0.1.0` = `9b97d7b` |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **6. Piloto: Tarkor e instalador** — prompts enviados (2026-10-22) a las sesiones «Tarkor Develop» (WMF) y «Tarkor Installer»; trabajan en `claude/piloto-galivelop-workflow` de cada repo |
| Último punto estable | **Versión `0.2.0`**: `version.py 0.2.0`, entrada del CHANGELOG (19 filas, R1-R3, arreglos de las revisiones) y los tests leen la versión de `plugin.json`; check en verde en local; el CI no arranca (cupo de Actions) |
| Siguiente paso | Esperar a que cada piloto deje `docs/registros/piloto-galivelop-workflow.md`; luego `gw-harvest` de los dos repos |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [ ] 6. Piloto: Tarkor e instalador (VeriNews, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.2.0` publicada (etiqueta y release a mano en GitHub, título `Galivelop-workflow vX.Y.Z`, notas de la entrada del CHANGELOG). Para la siguiente: `release.yml` con lanzamiento manual desde Actions que cree la etiqueta (la
sesión en la nube no puede subir etiquetas: 403 del proxy).

## Hecho (10 últimas)

1. 2026-10-22 — Fase 3 antes de `main`: `/code-review` de `a9850a1..57a8884`. Arreglado: `.claude/gw.json` instala
   `shellcheck-py` en la nube (sin él, el `pre-push` fallaba en cada contenedor nuevo); `doctor.py` solo mira la
   compactación si el `settings.json` del proyecto fija la ventana y propone ese valor (no un 200000 inventado), y su
   docstring lo cuenta; `tests/shellcheck.sh` recibe los archivos de `comprobar.sh` (las exclusiones, en un sitio),
   ya no usa `git`/`xargs` y es ejecutable; los tests de compactación miran solo las líneas `compaction:` y el de
   shellcheck no depende de `which`. 3 casos nuevos.
2. 2026-10-22 — Fase 2 antes de `main`: retro de la Fase 5 con la medida de `/opt-tokens` (S2: 191k de media, 30M, sin
   compactación por arrancar en `/home/user`). Aplicadas R1 (`doctor.py` avisa `compaction` en la nube sin
   `CLAUDE_CODE_AUTO_COMPACT_WINDOW`; `problemas.md` ES/EN; `AGENTS.md`), R2 (`orchestrate-dealer`: las filas
   aprobadas se reparten o `/clear` cada 4-5) y R3 (`tests/shellcheck.sh`: en la nube falla sin `shellcheck`, con
   `pip install shellcheck-py`). R4 rechazada. 6 casos nuevos.
3. 2026-10-22 — Hallazgo 5 (decidido por el usuario): el `pre-push` pasa `GW_PUSH_PROTECTED=true|false` a cada orden de
   `check`; el `check` de este repo corre `version.py --release` solo al subir a `main`; `release_check` compara con la
   última etiqueta alcanzable desde `HEAD` (no `HEAD^`); `release.yml` ya no lo llama. Hoy rechaza `main` hasta subir a
   `0.2.0`. `config.md` y `contribuir.md` ES/EN; 2 casos.
4. 2026-10-22 — Fase 1 antes de `main`: `/code-review` del diff contra `origin/main`. Arreglado: una rama no protegida
   con un `.claude/gw.json` inválido en su punta remota ya no bloquea la subida que lo arregla (`pre-push`) ni un PR hacia
   ella (`revision-antes-de-main.sh`, que además carga cada config una vez); la plantilla `gw.json` cuenta como contenido
   `README.es.md`, `CHANGELOG.md` y `CREDITS.md`; `recuperar.py` espera 1 s la entrada del gancho; `aplicar.py` importa de
   `doctor.py` `ignored_paths` y `stale_flow_hooks` (un dato, un sitio). 3 casos nuevos. Se queda como está: la rama
   protegida con config roto falla cerrada (test deliberado; se arregla desde GitHub); el primer push a `main` revisa el
   árbol entero; el coste de `recoger.py` (`earlier_match`).
5. 2026-10-22 — Tarkor P1-P4 en `orchestrate-dealer`: arreglos de revisión con `sonnet` (también en `selector`), arreglo
   de un archivo en la principal, antes del PR solo lo grave (también en `AGENTS.md` y `flujo.md`), el encargo comprueba la
   rama de partida del worktree.
6. 2026-10-22 — Portal P11: `gw-init` y `aplicar.md` §0 leen el flujo con un subagente; fila «Apply or update the workflow»
   en `selector`; `opt-tokens` avisa por encima de ~150k; cómo leer el flujo en la nube sin registrarlo como raíz.
7. 2026-10-22 — Portal P15 (a): clave `logSections` (esquema, plantilla, `config.md`); `recuperar.py --estado` devuelve esas
   secciones o, por defecto, la primera y la «Pendiente»/«Pending»; 2 casos en `test_sesion`.
8. 2026-10-22 — Portal P14 (a, c): `es-codigo.sh --explicar <ruta>...` dice código o contenido y por qué; plantillas de
   `AGENTS.md`/`REVIEW.md` (y el `AGENTS.md` de este repo): un test que espera un fallo comprueba el motivo.
9. 2026-10-22 — Portal P13 (parte): `templates/github/comprobar.yml` con `setup-node`/`setup-python`/`setup-java`
   condicionados a `hashFiles`, así el archivo queda del flujo sin tocar; guías ES/EN; test de orden y condiciones.
10. 2026-10-22 — Portal P18: `REVIEW.md`/`GLOSSARY.md` que ya existían: `aplicar.py` imprime su diff con la plantilla (sin
   escribir) mientras no lleven la marca de la versión; `aplicar.md` §3 dice qué pasar a mano; caso en `test_plantillas`.

## Pendiente

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
