# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9.0` publicada en `main`: `ccr-d1e2d496-0vzck8`** = `main` = `8357389` (2026-11-24). La `0.9` queda cerrada; la siguiente es la `0.10` «Estable» |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.9.0` en `main`** (`8357389`, las tres fases hechas: revisión con 7 hallazgos arreglados, retro D176/D177, `reviewed.sh`; CI de `4b9b5e4` en verde). Release de GitHub `v0.9.0` publicada (2026-11-24, sesión local; etiqueta sobre `8357389`) |
| Siguiente paso | **La `0.9.1`** (parche B48-B56, `docs/roadmap.md`: B48-B51 y B57 hechos; sigue B52), luego la `0.10` «Estable» (E28 primero). Evolutivos de la recogida a la `0.11` (E87-E92). `task.py current` sigue en E86 (solo lo cambia el usuario). Presupuesto de compactaciones: 2 |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [x] 6. Piloto: Tarkor e instalador (2026-10-23; private-project-1, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Lanzamiento (antes «Público»; plan §9, A7)

## Para la próxima publicación

**Política de versiones** (usuario, 2026-11-01, plan §7): solo la última menor publicada recibe parches (hoy la `0.5`);
los evolutivos van a la siguiente menor que no esté en obra (`docs/roadmap.md`). Cada versión se publica en este repo
(público), a lo sumo una al día. La sesión en la nube no puede subir etiquetas (403 del proxy): la release, a mano o
desde una sesión local.

**Orden de publicación** (usuario, 2026-11-15): primero el parche `0.6.2` (D109-D115) desde su rama `version/0.6.2`, sacada de `main`; después la `0.7.0` desde esta rama, con `main` ya traído.

## Hecho (5 últimas)

1. 2026-11-25 — B51: `gw-update` paso 1 comprueba `HEAD..origin/<protectedBranch>` y para (con `merge-main.py` o rama nueva, y el aviso del ledger); paso 2, comprobar que la clave existe antes de recomendarla. Solo texto de skill y copias; tests de skills y check completo pendientes.
2. 2026-11-25 — B49: `other-repo-read.py` exenta la palabra `<dir>/scripts/apply.py` tras un intérprete `python*` (`apply_script_words`); otro script del clon o una lectura en el mismo comando siguen avisando. `test_other_repo_read` (23) en verde; check completo pendiente.
3. 2026-11-24 — B48: `workflowCloneAlso` (`../{owner}/{repo}`, `/home/user/{owner}/{repo}`, `/home/user/{repo}`, sin distinguir mayúsculas) y `config.find_workflow_clone`, usados por `doctor.py` y `review-scope.py` (y `scope-guard.py` a través de él); `gw-update` lo nombra. Tests de doctor y review-scope hechos herméticos; `test_doctor` (184), `test_review_scope` (33) y `test_config` (111) en verde; check completo pendiente.
4. 2026-11-24 — B57 (retro del CI sin vigilar de B50): `before-stop.py` bloquea una vez por commit cuando `HEAD` está subido y su CI sigue en cola o en marcha, con la orden para programar la comprobación o esperarla con `Monitor`; claves `stopSeverity.ciPending` (block por defecto) y `stopCiTimeout` (30 s). Fallos de lectura a `warns`, nunca bloquean. `test_before_stop` (133, 4 casos rojos sin el cambio), `test_config` y `test_templates` en verde; check completo pendiente.
5. 2026-11-24 — B50: el paso «Install actionlint» de `check.yml` y su plantilla enlaza solo el binario en `$RUNNER_TEMP/actionlint-bin` y pone ese directorio en `GITHUB_PATH` (no el `bin/` del venv, cuyo `python3` no tiene PyYAML). `test_ci_local` en verde. El `pre-push` paró en la paridad del roadmap (H28 no había pasado las secciones `0.9.1` y `0.11` a `docs/roadmap.en.md`): añadidas, `roadmap.py check` en verde. El CI de `b4904b1` falló además en `test_apply.CiSteps`: la línea vieja de `GITHUB_PATH` (v0.9.0) va a `templates/github/check.legacy-lines.txt`; `CiSteps` en verde.

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
