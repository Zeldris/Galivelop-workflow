# Harvest portal-galivelop — 2026-10-26 (segunda recogida)

De `b8470762` a `aa76b34d` (`scripts/recoger.py`, 30 commits). Numeración seguida de `2026-10-26-portal-galivelop.md`.

## P4. `orchestrate-dealer`: los repos que solo se leen, clonados aparte y sin registrar

- **Source:** `docs/registros/retro-2026-10-26-miembro.md` @ `051940a` (skill)
- **What changes:** una línea en `skills/orchestrate-dealer/SKILL.md`, donde habla de traer material de otro repo: el
  repo se clona en el scratchpad y no se registra como raíz de la sesión (si no, sus `CLAUDE.md`, skills y ganchos se
  cargan y se mezclan con los del proyecto). Ya lo dicen `gw-harvest` y `docs/es/problemas.md`. Un aviso en
  `doctor.py` solo podría ser heurístico: como mucho, informativo.
- **Why it is general:** la sesión de la nube del Portal cargó las reglas de otro repo por registrarlo; le pasa a
  cualquier proyecto que lea otro.
- **Version bump:** minor → 1.0.0 (frase nueva en una skill)
- **Status:** propuesta

## P5. Apartado «Navegadores» en `REVIEW.md`

- **Source:** `docs/registros/retro-2026-10-26-miembro.md` @ `051940a` (plantilla)
- **What changes:** un apartado opcional en `templates/es|en/REVIEW.md` para proyectos web: lo que se mira en varios
  navegadores y en el móvil (APIs que no están en Safari, `100vh`, foco y teclado).
- **Why it is general:** sirve a todo proyecto web que use el flujo (Portal, VeriNews).
- **Version bump:** minor → 1.0.0
- **Status:** propuesta (valor bajo-medio)

## Stays in the project

- Nada más: el resto de la retro es del portal.
