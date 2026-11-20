# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | **`0.9`: `ccr-d1e2d496-0vzck8`**, con `main` fusionado. `main` = `4ca45d0` = **`0.8.1`**. `version/1.0.0` se queda con el diseño (`docs/design/`) |
| Check | `bash tests/check.sh` en verde en local. **El CI sí arranca** (2026-11-01, repo público). |
| Fase en curso | **6 cerrada**. Próxima: **7. Rodaje etapa 1** |
| Último punto estable | **`0.8.1` publicada** (`main` = `4ca45d0`, 2026-11-19; CI en verde; etiqueta y release `v0.8.1` creadas desde una sesión local) |
| Siguiente paso | **`0.9` «Front»**: la recogida de apertura (H24) ya está hecha; las tareas de la recogida ya están (E65-E77; bloques E65-E71 y E72-E74 revisados, 2026-11-20; E75-E77 sin revisar), A12 hecha (2026-11-20, `docs/tasks/A12.md`), así que siguen E4 (diseño cerrado, Q-23 a Q-28; ficha `docs/tasks/E4.md`; trozos 1 (carga), 2a (`profile.py`), 2b-guard (`config-guard.py`) y 2b-doctor (`doctor.py`) hechos; sigue el trozo 3, docs), E5, E7, E9-E16, E42 y E50. **Al cerrar el desarrollo de la `0.9`, antes de publicarla:** recogida y `0.8.2` (D142 y los arreglos que traiga; preguntas Q-4 a Q-6). Presupuesto de compactaciones: 1 (E4) |

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

1. 2026-11-20 — E4 trozo 2b-doctor, revisión: 8 hallazgos arreglados (valores que no son cadena o `profiles.dir` no válido avisan en vez de caer, y nunca se lee fuera del repo; correos con TLD de letras, sin falsos con `prettier@3.0.0` ni `git@host:…`; perfil que `config.load` rechaza avisa, con `config.profile_shape_problems` compartido; nombres filtrados por `PROFILE_NAME` y citados con `shlex.quote`; `config.CONFIG_REL`; `config.EMAIL_ADDRESS`/`EMAIL_IN_TEXT` únicos; mayúsculas en macOS); tests en `test_doctor.py`, `test_config.py`
2. 2026-11-20 — E4 trozo 2b-doctor: `doctor.py` avisa (con la orden que lo arregla) de perfiles huérfanos en `profiles.dir`, de cargos usados en `profiles.people` sin entrada en `profiles.roles`, de cargos o personas cuyo archivo de perfil no existe, de perfiles con JSON roto (sin caer) y de correos en claro en el bloque `profiles` o en un perfil (Q-25); sin bloque, sin avisos; 13 tests en `test_doctor.py`; falta el trozo 3 (docs)
3. 2026-11-20 — E4 trozo 2b-guard, revisión: 4 hallazgos arreglados (`profile.py` con `--r`/`--ro`/`--roo` o verbo ilegible pregunta; `profiles.dir` igual a la raíz lo rechaza el esquema y el guard protege los `*.json` de la raíz; `find` recorre `profiles.dir` con sus mayúsculas; redacción de `patterns.md`) y, en un worktree de agente, se protege también su propio `profiles.dir`; 94 tests en `test_config_guard.py`
4. 2026-11-20 — E4 trozo 2b-guard: `config-guard.py` pregunta antes de `profile.py new|assign|role` (también con `cd` a scripts, `bash -c`, envoltorios y `--root`; `list` y `show` no) y antes de escribir en la carpeta de perfiles (`profiles.dir` del config crudo, defecto del esquema si está roto; con `..`, mayúsculas, symlinks y worktrees; sus carpetas padre cuentan como ancestros); 11 tests en `test_config_guard.py`, `test_profile.py` con el docstring nuevo; falta `doctor.py`
5. 2026-11-20 — E4 trozo 2a, revisión: 7 hallazgos arreglados (`profile.py` carga sin capas y solo `show` las aplica; `role`/`assign` validan la cadena destino con `apply_profiles(force=True)`; `assign` no conserva un cargo retirado; correo con parte local y dominio; `show` con mensaje propio; sin literal del directorio); `config.load(profiles=False)`; 45 tests en `test_profile.py`

## Pendiente

Lo pendiente está en [`docs/records/pending.md`](records/pending.md); se añade y se quita allí.

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
