# Retro de la versión 0.5.0 (2026-11-04)

Sesiones de la `0.5`: oleadas 1-3 de evolutivos (2026-11-03), recogida H15 con sus 13 propuestas (D32-D40, E18, E19,
B14, B15) y el `/code-review` contra `origin/main` con sus 10 arreglos. Recoge los puntos (1)-(19) que la bitácora fue
apuntando «para la retro» e incluye la medida de `/gw-opt-tokens`.

**Estado:** pendiente de decisión del usuario (la sesión lo dejó listo de noche; el usuario decide por la mañana).

## Medida (`gw-opt-tokens`)

- Sesión de la recogida, la implementación y la revisión (3 compactaciones en este tramo, 7 en total frente a un
  presupuesto de 2): principal con 143 llamadas, un contexto medio de 121k (suelo 103k, techo 147k) y 17,3M de entrada
  (98 % de caché). Un subagente: 30 llamadas, 3,4M y un arranque de 57k. Total: 20,8M.
- Lo que más pesa: los 10 arreglos de la revisión se hicieron en la sesión principal (~100 llamadas a ~120k). Los
  archivos más releídos fueron `scripts/config-guard.py` (9 veces), `scripts/commit-message.py` (8) y `CHANGELOG.md`
  (15, con 207k arrastrados).

## Propuestas (de más a menos grave)

### R1. El check largo, a prueba de esperas: un registro fijo, un cerrojo y un resumen de lo que falló (general)

- **Qué pasó:** el check tarda 25-30 min y casi todo lo que falló alrededor de él viene de ahí:
  - (7) y (9): esperas con tope corto y monitores que dieron falsos atascos;
  - (8) y (15): un `pkill -f` amplio, y un push y una fusión con check en paralelo, cortaron el check («Terminated»);
  - (2) y (3): varios checks a la vez saturaron la máquina;
  - (10), (12) y (16): `merge-branch.sh` borra su registro y solo enseña las últimas líneas;
  - (6) y (11): el `pre-push` repite el check que la fusión ya pasó;
  - (19): en `e1f312f` el check dio rojo solo por una copia sin refrescar, y se dio por verde leyendo un resumen en
    vez del final del registro. Al final, `CHECK FAILED` no dice qué sección falló.
- **Qué cambia:**
  - `check.sh` escribe siempre en `.git/gw/check-<sha>.log` y toma un cerrojo con su pid: un segundo check espera o
    sale diciendo cuál corre. Termina con una línea `CHECK <ok|FAILED>: <secciones que fallaron>`.
  - `merge-branch.sh` usa ese registro, enseña ese resumen y apunta el verde para que el `pre-push` no lo repita.
  - Cada cambio, con su test.
- **Riesgo:** un cerrojo huérfano que bloquee. Contrapeso: el cerrojo guarda el pid y se descarta si el proceso no
  existe.

### R2. Los tests que pide un cambio, calculados por un script (general)

- **Qué pasó:**
  - (13) y (17): los subagentes que tocan `scripts/` no corren `test_reviewed.py` (copias) ni los tests de los
    ganchos, y los rojos salen en la fusión.
  - (18): la revisión halló una regresión de D36 que sus tests no cubrían: el commit de la marca no se probó con el
    `commit-msg` estricto.
- **Qué cambia:**
  - `scripts/related-tests.py <archivos>` da los archivos de test de un cambio:
    - `scripts/X.py` lleva a `test_X.py`;
    - `scripts/` o `templates/githooks/` llevan además a `test_reviewed.py` y `test_hooks.py`;
    - un test con e-mails lleva a `test_private_check.py`.
  - El encargo de `gw-orchestrate-dealer` lo cita en vez de enumerar los tests.
  - En `REVIEW.md`, una regla de criterio: un script que hace commits se prueba con los ganchos del proyecto
    instalados.
- **Riesgo:** un mapa incompleto. Contrapeso: el check completo sigue antes de subir; el script solo adelanta lo
  barato.

### R3. Los arreglos de una revisión, repartidos (opt-tokens, general)

- **Qué pasó:** los 10 arreglos se hicieron en la sesión principal, con ~100 llamadas a ~120k de contexto medio
  (~12M, más de la mitad de la sesión). El presupuesto de compactaciones (2) acabó en 7.
- **Qué cambia:** `gw-orchestrate-dealer` dice que los hallazgos aprobados de un `/code-review` se reparten como filas,
  con un subagente por grupo de archivos:
  - el modelo medio para lo mecánico (un renombrado, las copias);
  - el grande para los ganchos y las guardas, como dice `.claude/gw/gw-opt-tokens.md`.
  La sesión principal revisa cada diff.
- **Ahorro estimado:** unos 5-7M por versión. Cada subagente arranca en ~57k y trabaja con un contexto más pequeño que
  la principal.
- **Riesgo:** un subagente sin el contexto de la revisión arregla el síntoma y no la causa. Contrapeso: el encargo
  copia el hallazgo entero y su escenario de fallo, y la principal revisa el diff antes de fusionar.

### R4. Worktrees y scratchpad de los subagentes (general)

- **Qué pasó:**
  - (1): los worktrees de `isolation: worktree` nacen en `origin/main`, no en HEAD (D6, `worktree.baseRef`);
  - (4): un agente pisó los archivos de otro en el scratchpad compartido;
  - (5): `pkill` está denegado a los agentes.
- **Qué cambia:**
  - El encargo de `gw-orchestrate-dealer` da a cada agente una carpeta propia, `scratchpad/<id>/`.
  - Comprueba la base del worktree (`git merge-base --is-ancestor <HEAD de la sesión> HEAD`) antes de empezar.
  - Para cortar un proceso, `TaskStop`.
- **Riesgo:** ninguno.

### R5. El gancho `Stop` no insiste mientras corre un check o un push (general)

- **Qué pasó:** (14): el gancho pide subir mientras el check de una fusión aún corre.
- **Qué cambia:** `before-stop.py` lee el cerrojo de R1 (y la marca `gw-push-in-progress` de D38, que ya lo hace para
  el push) y avisa en una línea de que el check está en marcha.
- **Riesgo:** ninguno. Depende de R1.

### R6. El check local no ve lo que falla en un Python más viejo (general)

- **Qué pasó:**
  - El CI de Ubuntu (Python 3.12) dio rojo en `cdb37d1` con 8 tests de `handoff.py set-row`, que usaba
    `Path.read_text(newline=)` (3.13+), desde D23. El check local corre con 3.13 y salió verde.
  - Se arregló con `open()` y un test estático (`test_utils.OldestPython`) que prohíbe ese argumento.
- **Qué cambia:** `check.sh` corre además los tests con el Python más viejo que haya en la máquina, si es distinto, o
  avisa de que no lo prueba. La matriz `ciPython` (D19) ya cubre a los proyectos en el CI.
- **Riesgo:** el check tarda el doble si se corre todo dos veces. Contrapeso: con el Python viejo, solo los tests de
  los scripts que cambiaron (R2).

## Lo que funcionó

- La recogida con aprobación por filas: 13 de 44 propuestas, el reparto en dos oleadas de worktrees y la fusión en
  serie con un solo check al final (16).
- El `/code-review` contra `origin/main` encontró 10 fallos reales antes de `main`, entre ellos la regresión de D36,
  que habría bloqueado `reviewed.sh` con el `commit-msg` estricto.

## For Galivelop-workflow

Este repo es el flujo: R1-R5 se aplican aquí mismo. Por la política de versiones, a la `0.5.1` (arreglos: R1, R5) o a
la `0.6` (evolutivos: R2, R3, R4), según decida el usuario.
