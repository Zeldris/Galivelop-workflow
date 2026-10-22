# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-76251061-b1yiwq` (sale de `claude/galivelop-workflow-inicio` en `0f36412`); `main` = `9b97d7b` = **release `v0.1.0`** (2026-10-22) |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **5. Piloto: Portal-Galivelop** — publicado en el portal (`673602b`); propuestas decididas (2026-10-22), aplicándolas para `v0.2.0` |
| Último punto estable | Reparto filas 1-11 hechas (Portal P1, P16, P9, P2 a-b, P5, P19, P17, P21, P4, P3 y P7); P7: `doctor.py` avisa de `*.gw-nuevo` pendientes y de ganchos del flujo duplicados |
| Siguiente paso | Fila 12 del reparto: **Portal P12** (`aplicar.md` paso 6 con `--dry-run` y dos mensajes). Luego las filas 13-19 en orden; tres fases y `v0.2.0` (la entrada `0.2.0` del CHANGELOG se escribe al publicar, con las filas hechas) |

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

1. 2026-10-22 — Portal P7: `doctor.py` da WARN con los `*.gw-nuevo` pendientes (y sin «skills OK» mientras haya en
   `.claude/skills/`) y con ganchos que corren scripts del flujo desde otra carpeta; `aplicar.py` los lista al fusionar.
2. 2026-10-22 — Portal P3: `git check-ignore` sobre config, scripts, `settings.json`, una skill y `pre-push`: FAIL en
   `doctor.py` y aviso en `aplicar.py` con la línea `!…` del `.gitignore`; casos en `test_doctor` y `test_aplicar`.
3. 2026-10-22 — Portal P4: `retro` sin `disable-model-invocation` y con descripción de cuándo usarla (cuadra con `AGENTS.md`,
   `selector` y `revisado.sh`); test de las skills que el flujo lanza solo.
4. 2026-10-22 — Portal P21: `recoger.py` busca `## For|Para Galivelop-workflow` en todo `.md` rastreado cambiado desde
   la última recogida (notas de piloto incluidas); `gw-harvest` lo dice; caso en `test_recoger`.
5. 2026-10-22 — Portal P17: `aplicar.py` copia `LICENSE-mattpocock-skills` a `.claude/skills/` si alguna skill la cita;
   `doctor.py` avisa si falta; `version.py --release` la cuenta como copiable. Casos en `test_aplicar` y `test_doctor`.
6. 2026-10-22 — Portal P19: `.claude/hooks/` → `.claude/gw/scripts/` en las plantillas de `CLAUDE.md`, `aplicar.py` y las guías
   ES/EN; test de rutas que el flujo ya no usa en `test_plantillas`.
7. 2026-10-22 — Portal P5: `recuperar.py --estado` ya no se cuelga con la entrada estándar abierta sin datos (`select`
   de 0,2 s) ni da `BrokenPipeError` con `| head`; 2 casos en `test_sesion`.
8. 2026-10-22 — Portal P2 (a, b): `version.py --release` (y `release.yml`) falla si cambió algo copiable desde la
   última etiqueta sin subir la versión; `aplicar.py` dice «ediciones locales o copia anterior» con el `diff`; `recoger.py`
   separa las copias iguales a un commit anterior del flujo. Tests nuevos en `test_version`, `test_recoger`, `test_aplicar`.
9. 2026-10-22 — Portal P9: `content` por defecto `^docs/`, los `.md` de documentación de la raíz y los `.md` de
   `.claude/skills/`; guías ES/EN alineadas y test con rutas que deben ser código.
10. 2026-10-22 — Portal P16: el `pre-push` busca marcadores y `*.rej`/`*.orig` en `base..local` al subir a la rama
   protegida (también commits ya subidos a otra rama); 3 casos nuevos en los tests.

## Pendiente

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
