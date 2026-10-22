# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-76251061-b1yiwq` (sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `9b97d7b` = **release `v0.1.0`** (2026-10-22) |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **5. Piloto: Portal-Galivelop** — publicado en el portal (`673602b`); propuestas aplicadas (2026-10-22); falta publicar `v0.2.0` |
| Último punto estable | **Fase 1 (código) antes de `main`**: `/code-review` del diff contra `origin/main` hecho (10 hallazgos) y arreglados los confirmados; check en verde en local; el CI de GitHub no arranca (cupo de Actions) |
| Siguiente paso | Que el usuario decida el hallazgo 5 (`version.py --release`, en «Pendiente»); luego fase 2 (`/opt-tokens` y `/retro`) y cierre con `revisado.sh`; subir la versión (`python3 scripts/version.py 0.2.0`, entrada del CHANGELOG con las 19 filas) y `v0.2.0`, todo **con confirmación del usuario** |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [ ] 5. Piloto: Portal-Galivelop
- [ ] 6. Piloto: Tarkor, instalador y VeriNews
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.1.0` publicada. Para la siguiente: `release.yml` con lanzamiento manual desde Actions que cree la etiqueta (la
sesión en la nube no puede subir etiquetas: 403 del proxy).

## Hecho (10 últimas)

1. 2026-10-22 — Fase 1 antes de `main`: `/code-review` del diff contra `origin/main`. Arreglado: una rama no protegida
   con un `.claude/gw.json` inválido en su punta remota ya no bloquea la subida que lo arregla (`pre-push`) ni un PR hacia
   ella (`revision-antes-de-main.sh`, que además carga cada config una vez); la plantilla `gw.json` cuenta como contenido
   `README.es.md`, `CHANGELOG.md` y `CREDITS.md`; `recuperar.py` espera 1 s la entrada del gancho; `aplicar.py` importa de
   `doctor.py` `ignored_paths` y `stale_flow_hooks` (un dato, un sitio). 3 casos nuevos. Se queda como está: la rama
   protegida con config roto falla cerrada (test deliberado; se arregla desde GitHub); el primer push a `main` revisa el
   árbol entero; el coste de `recoger.py` (`earlier_match`).
2. 2026-10-22 — Tarkor P1-P4 en `orchestrate-dealer`: arreglos de revisión con `sonnet` (también en `selector`), arreglo
   de un archivo en la principal, antes del PR solo lo grave (también en `AGENTS.md` y `flujo.md`), el encargo comprueba la
   rama de partida del worktree.
3. 2026-10-22 — Portal P11: `gw-init` y `aplicar.md` §0 leen el flujo con un subagente; fila «Apply or update the workflow»
   en `selector`; `opt-tokens` avisa por encima de ~150k; cómo leer el flujo en la nube sin registrarlo como raíz.
4. 2026-10-22 — Portal P15 (a): clave `logSections` (esquema, plantilla, `config.md`); `recuperar.py --estado` devuelve esas
   secciones o, por defecto, la primera y la «Pendiente»/«Pending»; 2 casos en `test_sesion`.
5. 2026-10-22 — Portal P14 (a, c): `es-codigo.sh --explicar <ruta>...` dice código o contenido y por qué; plantillas de
   `AGENTS.md`/`REVIEW.md` (y el `AGENTS.md` de este repo): un test que espera un fallo comprueba el motivo.
6. 2026-10-22 — Portal P13 (parte): `templates/github/comprobar.yml` con `setup-node`/`setup-python`/`setup-java`
   condicionados a `hashFiles`, así el archivo queda del flujo sin tocar; guías ES/EN; test de orden y condiciones.
7. 2026-10-22 — Portal P18: `REVIEW.md`/`GLOSSARY.md` que ya existían: `aplicar.py` imprime su diff con la plantilla (sin
   escribir) mientras no lleven la marca de la versión; `aplicar.md` §3 dice qué pasar a mano; caso en `test_plantillas`.
8. 2026-10-22 — Portal P10: `--init` con `--require-retro`, `--visible-language` y `--design-reference`; `requireRetro`
   `false` en `templates/gw.json` y en el esquema; la tabla del paso 1 de `aplicar.md` lo pregunta.
9. 2026-10-22 — Portal P12: `aplicar.md`/`apply.md` §6 prueban la protección con `git push --dry-run` y aceptan los dos
   rechazos (sin marca, código tras la marca); test de que el simulacro pasa por el `pre-push`.
10. 2026-10-22 — Portal P7: `doctor.py` da WARN con los `*.gw-nuevo` pendientes (y sin «skills OK» mientras haya en
   `.claude/skills/`) y con ganchos que corren scripts del flujo desde otra carpeta; `aplicar.py` los lista al fusionar.

## Pendiente

- **Decisión del usuario (hallazgo 5 de la revisión):** `version.py --release` no detecta nada en `release.yml` (allí la
  etiqueta ya es la versión nueva) y falla si no hay etiqueta anterior. Lo que quiere evitar (`main` cambia archivos
  copiables sin subir la versión) solo se ve antes de subir a `main`. Propuesta: compararlo con `describe HEAD` y
  correrlo en el `pre-push` de este repo hacia `main` (vía `prepush-ramas.sh` o un `check` propio).
- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
