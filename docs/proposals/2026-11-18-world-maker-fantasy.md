# Harvest world-maker-fantasy — 2026-11-18

De `b098334e` a `59a496f7` (`scripts/harvest.py`). 73 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 3 retros (la última, la de la actualización a `0.8.0`). Recogida de apertura de la `0.9` (2026-11-18).

## P1. La plantilla de `AGENTS.md` dice que `Findings:`/`Retries:` van en el bloque final de trailers

- **Source:** `docs/records/retro-2026-11-16-gw-update-0.7.md` punto 2 @ `a2902cc4` (retro)
- **What changes:** `templates/es/AGENTS.md` (l. 77) y `templates/en/AGENTS.md` (l. 76): la regla de `Findings:` y
  `Retries:` añade «en el último párrafo, con los demás trailers». El rechazo ya existe (`scripts/commit-message.py`,
  D97); falta que la regla escrita lo diga.
- **Why it is general:** el gancho rechaza la línea fuera del bloque y la regla que lee el agente no lo dice.
- **Version bump:** patch
- **Status:** proposed

## P2. `merge-main.py`: traer la rama protegida sin perder el ledger de métricas

- **Source:** `docs/records/retro-2026-11-16-marca-imagenes.md` R3 @ `47814f40` y
  `docs/records/retro-2026-11-18-gw-update-0.8.md` @ `e440b8d4` (retro; segunda vez: un `checkout` al resolver el
  merge descartó el ledger; allí lo llaman `merge-protected`)
- **What changes:** nuevo `scripts/merge-main.py`: si el único cambio sin commit es el ledger de métricas, lo
  commitea; si hay más, se niega; después hace `git merge origin/<protectedBranch>`. `templates/*/AGENTS.md` (paso 5 de
  «Al empezar», l. 17 en `es`) apunta a él en vez de `git merge` a pelo.
- **Why it is general:** los ganchos escriben el ledger en todos los proyectos, así que siempre está sucio; con
  `stash` + `merge` un conflicto dejó el `stash pop` sin aplicar y se perdieron 9 líneas (recuperadas de un commit
  suelto). `merge=union` (B32) evita el conflicto entre ramas, no el del árbol sucio.
- **Version bump:** minor
- **Status:** proposed

## P3. El aviso de `handoff.py` tras un rechazo de `pre-commit` dice «repite el mismo `git commit -m …`»

- **Source:** `docs/records/retro-2026-11-16-marca-imagenes.md` R4 @ `47814f40` (retro)
- **What changes:** `scripts/handoff.py` (l. 472-473, «run the commit again: git commit») dice repetir el mismo
  `git commit -m …`, y solo remite a `.git/COMMIT_EDITMSG` cuando rechazó `commit-msg`: un rechazo en `pre-commit` no
  escribe el mensaje nuevo y `-F COMMIT_EDITMSG` reutiliza el del commit anterior.
- **Why it is general:** el fallo sale de cómo git guarda el mensaje, no del proyecto. Valor bajo: conviene una
  segunda recogida que lo confirme.
- **Version bump:** patch
- **Status:** proposed

## Already here

- Parche P24 de WMF (`test_measure.py` busca los archivos del flujo): `skills/gw-opt-tokens/scripts/test_measure.py`
  ya los localiza desde `HERE` (su propia carpeta), sin depender de la raíz del proyecto; no hay nada que subir.
- Rechazo de `Findings:`/`Retries:` fuera del bloque final: `scripts/commit-message.py` (D97) ya lo hace con
  `commitRefs` o `commitNext`; solo falta el texto de la plantilla (P1).

## Stays in the project

- `hoja.sh`, CSS sin uso, UX-40/UX-41, QA-362…QA-368: trabajo del juego y de sus herramientas.
