# 2026-11-21 · gw-worker · pending · E5

## Why

Trozo 3: los checks de front. `front.py run` corre en una copia temporal de `front.dir` con `node_modules` enlazado a
la caché del git-dir (como `tests/test_front_sample.py`), para no dejar nada en el árbol ni ensuciar el checkout que
comprueba el `pre-push`. `full` fuera de Linux sin Docker sale con 3 antes de correr nada: un verde parcial sería un
verde falso (E-9).

## Alternatives

- `NODE_PATH` o un `node_modules` enlazado en el árbol: el primero no lo respeta todo Playwright y el segundo deja un
  archivo en el árbol que el `pre-push` vería como cambio.
- Poner `front.py run fast` en `check` en vez de en el `pre-push`: lo correría también `check.sh` y el CI, y la ficha
  lo pide en el `pre-push`.
- La versión de Playwright de las capturas en su ruta (`snapshotPathTemplate`): toca `templates/front`, fuera de este
  trozo; se usa un archivo de sello (`front.snapshotStamp`).

## Changed because

—
