# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-6dfbc880-ddr41g` (avance rápido de `ccr-76251061-b1yiwq`, que sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `01d1a75` = **release `v0.2.0`** (2026-10-22, etiqueta y release creadas a mano en GitHub); `v0.1.0` = `9b97d7b` |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **6 cerrada** y `0.3.0` publicada en `main` (2026-10-23); P7 del instalador aplicada en la rama (`0.4.0`, sin publicar); recogida de la `0.4.0` hecha, propuestas presentadas al usuario. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | Recogida de la `0.4.0` (`docs/propuestas/2026-10-23-portal-galivelop.md`, `estado.json` al día); check en verde en local; el CI no arranca (cupo de Actions): comprobado solo en local |
| Siguiente paso | Aplicar lo que el usuario apruebe de `docs/propuestas/2026-10-23-portal-galivelop.md`; añadir la regla «una recogida al empezar cada versión» y su comprobación en `version.py --release` con sus tests; luego la **Fase 7 (rodaje etapa 1)** |

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

## Hecho (5 últimas)

1. 2026-10-23 — Recogida de la `0.4.0` (portal, WMF, instalador, VeriNews): 5 propuestas del portal en
   `docs/propuestas/2026-10-23-portal-galivelop.md`; los otros tres, nada nuevo. El usuario decide recoger en cada versión.
2. 2026-10-23 — P7 del instalador aplicada (`0.4.0`, sin publicar): sin CI, el check en local vale con la confirmación
   de la persona («comprobado solo en local»), en `AGENTS.md` y plantillas; el gancho lo nombra al bloquear.
3. 2026-10-23 — **`0.3.0` publicada en `main`** (ea81c9f). El usuario decide la P7: un check que pasó en local vale
   cuando Actions no arranca.
4. 2026-10-23 — Fase 2 antes de `main`: `/opt-tokens` (tope de ~35 llamadas por subagente, «Hecho» de 5 entradas
   cortas, check en segundo plano) y `/retro` (regla de `/tmp` en `REVIEW.md`); retro en `docs/registros/`.
5. 2026-10-23 — Revisión de los arreglos antes de `main`: carpeta de worktrees del `pre-push` por usuario, 700, sin
   symlinks (688da4d, 6aaf2cc); menores en «Pendiente».

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
