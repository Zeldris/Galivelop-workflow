# Harvest verinews_ai — 2026-10-21

De `never` a `a9b5761e6445` (`scripts/recoger.py`). Sin skills nacidas ni scripts con diferencias (el flujo se portó de
Tarkor); las 14 skills que difieren llevan notas de idioma, `GLOSSARY.md` y Maven/Vite. Lo de ganchos, antisecretos y
`registro_sesion.py` ya figura en `casos-reales.md`. Ideas del `retro-2026-10-21-flujo.md` (sección «Retro»):

## P1. Autorizar el reparto a subagentes en `CLAUDE.md`

- **Source:** `docs/registros/retro-2026-10-21-flujo.md` § «Retro», R1 (y T2 en `/opt-tokens`) @ a9b5761e6445 (retro, plantilla)
- **What changes:** la plantilla de `CLAUDE.md` incluye «el usuario autoriza repartir con `orchestrate-dealer` sin preguntar cada vez»; `doctor.py` avisa si falta.
- **Why it is general:** sin esa frase, el sistema de Claude Code no lanza subagentes sin que se pidan y `orchestrate-dealer` y el `selector` quedan en papel; en esta sesión no se repartió nada y se arrastraron ~5M de tokens.
- **Version bump:** minor
- **Status:** propuesta

## P2. Lo traído de otro repo se adapta a los contratos de este

- **Source:** `docs/registros/retro-2026-10-21-flujo.md` § «Retro», R3 y R2 @ a9b5761e6445 (retro, guía de revisión)
- **What changes:** sección en la plantilla de `REVIEW.md`: formatos, rutas, patrones de nombres, constantes y ids de tarea se comprueban contra este repo, no contra el original; en `test-plantillas.sh`, que la tabla de ejemplo de cada runbook la lea su script.
- **Why it is general:** 6 de 12 hallazgos eran exactamente eso (extensiones sin `.java`/`.jsx`, claves de proveedores, constante que ya no existía); el plan §12 solo cubre la forma de subir.
- **Version bump:** minor
- **Status:** propuesta

## P3. Sesión abierta fuera del repo: qué hacer y qué avisar

- **Source:** `docs/registros/retro-2026-10-21-flujo.md` § `/opt-tokens`, T1 y R4 @ a9b5761e6445 (retro, plantilla)
- **What changes:** línea en la plantilla de `CLAUDE.md`: si la sesión no arrancó en la raíz del repo (no carga `settings.json`: sin tope de compactación ni gancho de inicio), activar `core.hooksPath` y avisar al usuario. `doctor.py` lo comprueba con `registro_sesion.py`; el paso 1 de `opt-tokens` dice usar `--sesion`.
- **Why it is general:** contexto medio de 262k y ganchos sin activar; `registro_sesion.py` y el respaldo de `medir.py` ya se portan, falta la regla y el aviso al usuario.
- **Version bump:** patch
- **Status:** propuesta

## Se queda en el proyecto

- `.claude/skills/pr/SKILL.md` (+8): `mvn test`, lint, capturas y peligro de `ALTER` en producción.
- `.claude/skills/grilling/SKILL.md`: referencias del IMI (marcos de verificación); la parte general es P1 del harvest de `world-maker-fantasy`.
- `retro-2026-10-21-flujo.md` R2 en su forma exacta (`resolver_hallazgos.py`): su registro de hallazgos.

## Ya está aquí

- R5 (pre-commit antisecretos también en CI): `--rango` en `casos-reales.md`.
- `opt-tokens` con respaldo de registro de otra carpeta: ya en nuestro `medir.py`.
