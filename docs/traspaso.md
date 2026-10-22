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
| Último punto estable | Reparto filas 1-18 hechas (todas las del portal); P11: aplicar o actualizar el flujo se lee con un subagente (`gw-init`, `aplicar.md` §0, fila en `selector`, aviso en `opt-tokens`) |
| Siguiente paso | Fila 19 del reparto: **Tarkor P1-P4** (`orchestrate-dealer`: arreglos con `sonnet`, arreglo de un archivo en la principal, solo lo grave antes del PR, rama de partida del worktree). Luego; tres fases y `v0.2.0` (la entrada `0.2.0` del CHANGELOG se escribe al publicar, con las filas hechas) |

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

1. 2026-10-22 — Portal P11: `gw-init` y `aplicar.md` §0 leen el flujo con un subagente; fila «Apply or update the workflow»
   en `selector`; `opt-tokens` avisa por encima de ~150k; cómo leer el flujo en la nube sin registrarlo como raíz.
2. 2026-10-22 — Portal P15 (a): clave `logSections` (esquema, plantilla, `config.md`); `recuperar.py --estado` devuelve esas
   secciones o, por defecto, la primera y la «Pendiente»/«Pending»; 2 casos en `test_sesion`.
3. 2026-10-22 — Portal P14 (a, c): `es-codigo.sh --explicar <ruta>...` dice código o contenido y por qué; plantillas de
   `AGENTS.md`/`REVIEW.md` (y el `AGENTS.md` de este repo): un test que espera un fallo comprueba el motivo.
4. 2026-10-22 — Portal P13 (parte): `templates/github/comprobar.yml` con `setup-node`/`setup-python`/`setup-java`
   condicionados a `hashFiles`, así el archivo queda del flujo sin tocar; guías ES/EN; test de orden y condiciones.
5. 2026-10-22 — Portal P18: `REVIEW.md`/`GLOSSARY.md` que ya existían: `aplicar.py` imprime su diff con la plantilla (sin
   escribir) mientras no lleven la marca de la versión; `aplicar.md` §3 dice qué pasar a mano; caso en `test_plantillas`.
6. 2026-10-22 — Portal P10: `--init` con `--require-retro`, `--visible-language` y `--design-reference`; `requireRetro`
   `false` en `templates/gw.json` y en el esquema; la tabla del paso 1 de `aplicar.md` lo pregunta.
7. 2026-10-22 — Portal P12: `aplicar.md`/`apply.md` §6 prueban la protección con `git push --dry-run` y aceptan los dos
   rechazos (sin marca, código tras la marca); test de que el simulacro pasa por el `pre-push`.
8. 2026-10-22 — Portal P7: `doctor.py` da WARN con los `*.gw-nuevo` pendientes (y sin «skills OK» mientras haya en
   `.claude/skills/`) y con ganchos que corren scripts del flujo desde otra carpeta; `aplicar.py` los lista al fusionar.
9. 2026-10-22 — Portal P3: `git check-ignore` sobre config, scripts, `settings.json`, una skill y `pre-push`: FAIL en
   `doctor.py` y aviso en `aplicar.py` con la línea `!…` del `.gitignore`; casos en `test_doctor` y `test_aplicar`.
10. 2026-10-22 — Portal P4: `retro` sin `disable-model-invocation` y con descripción de cuándo usarla (cuadra con `AGENTS.md`,
   `selector` y `revisado.sh`); test de las skills que el flujo lanza solo.

## Pendiente

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
