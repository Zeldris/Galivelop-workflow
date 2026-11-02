# Harvest instalador-wmf-tarkor — 2026-10-26 (segunda recogida)

De `f399a63d` a `a73f8812` (`scripts/recoger.py`, 34 commits). Las ideas salen de las retros de FLU-5, FLU-6 e
INS-42. Según el plan §7, la `0.4` solo recibe correcciones: lo evolutivo va marcado «para la 1.0.0». Numeración
seguida de `2026-10-26-instalador-wmf-tarkor.md`.

## P8. `bitacora.py` no sugiere `git commit --amend`

- **Source:** `docs/registros/retro-2026-10-26-flu5.md` @ `3712259` (script)
- **What changes:** los avisos de `scripts/bitacora.py:245` y `:333` dicen «edit … and commit again: git commit
  --amend». En `commit-msg` el commit todavía no existe (enmendar reescribe el anterior), y el modo automático de
  Claude Code bloquea `--amend`. Cambiar el texto a «edita la bitácora, `git add` y repite el commit» (o, en
  `pre-push`, «haz un commit nuevo»), según el gancho que llame; con su caso en `tests/` que compruebe el mensaje.
- **Why it is general:** el mensaje es falso en todos los proyectos y empuja a reescribir un commit ajeno.
- **Version bump:** patch (corrección, `0.4.2`)
- **Status:** aprobada (2026-10-27)

## P9. Comprobar la propia fila de la bitácora al hacer el commit (`own-row --staged`)

- **Source:** `docs/registros/retro-2026-10-26-flu5.md` @ `3712259` (script)
- **What changes:** hoy la fila de otra rama o el límite de 600 caracteres solo saltan en el `pre-push`, cuando ya
  hay que deshacer commits. Un modo `--staged` de `bitacora.py own-row` en el `pre-commit` lo detecta antes.
- **Why it is general:** todos los proyectos con varias ramas a la vez tienen el mismo `pre-push` tardío.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P10. `doctor.py` avisa de worktrees ya fusionados

- **Source:** retro de FLU-6 @ `a73f8812` (script)
- **What changes:** `check_worktrees` de `scripts/doctor.py` lista también los worktrees cuya rama ya está en la
  rama protegida, con la orden que los quita (`git worktree remove …`).
- **Why it is general:** los subagentes dejan worktrees en todos los proyectos; los ya fusionados ocupan disco y
  confunden el `git worktree list`.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P11. `scout-updates` lee la versión de Rust del proyecto

- **Source:** retro de FLU-6 @ `a73f8812` (skill)
- **What changes:** `skills/scout-updates/scripts/inventory.py` lee `rust-toolchain`/`rust-toolchain.toml` y
  `rust-version` de `Cargo.toml`, igual que ya lee las versiones de Node y Python.
- **Why it is general:** cualquier proyecto con Rust (Tauri, CLI) se queda sin esa parte del inventario.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P12. Check en una orden con resumen y salida recortada

- **Source:** `docs/registros/retro-2026-10-26-ins42.md` @ `32da0fb` (O1) (script); la misma idea sale en WMF
  (`2026-10-26-world-maker-fantasy-2.md`, P4)
- **What changes:** sobre el `scripts/check.sh` de la 1.0.0: un modo silencioso que da OK/FALLA por orden y, de las
  que fallan, solo el final de la salida; y la opción de comprobar una revisión concreta.
- **Why it is general:** la salida entera del check es el mayor gasto de tokens al arreglar un rojo, en todos los
  proyectos.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## P13. Regla de invariantes en `REVIEW.md`

- **Source:** `docs/registros/retro-2026-10-26-ins42.md` @ `32da0fb` (R2); redacción del proyecto @ `762004c`
  (plantilla)
- **What changes:** una línea en `templates/es|en/REVIEW.md`: un cambio que toca una invariante (un dato en un solo
  sitio, un orden de pasos, un estado que no puede darse) se revisa buscando los demás sitios que la sostienen.
- **Why it is general:** es criterio de revisión, no del proyecto.
- **Version bump:** minor → 1.0.0
- **Status:** aprobada (2026-10-27)

## Stays in the project

- Retro de FLU-5, R2: es del plan del instalador.

## Ya está

- Retro de FLU-5, 1b («tarea cerrada → Hecho» en el `pre-commit`): en la 1.0.0 (P6 de la primera recogida de hoy).
- Retro de INS-42, R4: en la 1.0.0.
