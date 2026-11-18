# 2026-11-18 · session · pending · C13

## Why

- Clave `scopeGuard.mode` con `off|warn|block|auto` y `warn` por defecto: una sola clave, legible, y `auto` cubre lo
  que pide P3 (bloquear con `modes.questions` restrictivo) sin atar el guardián a otro modo cuando no se quiere. Este
  repo se queda en `warn` (no hace falta escribirla en `.claude/gw.json`).
- Política ante un dato que falta: este guardián avisa por oficio, así que un `.claude/gw.json` ilegible es un aviso de
  una línea (una vez), no un bloqueo; `questions-guard.py` ya bloquea el código en ese caso y `commit-msg` rechaza lo
  que no sea `WIP:`. Git colgado o un fallo del script solo rechazan si el modo leído es `block`.
- Sin tarea, sin ficha o sin `## Files`: permitido en silencio; no hay alcance con el que comparar y la forma de la
  ficha ya la exige `commit-msg`.
- La tarea en curso y la ubicación del archivo se reutilizan importando `questions-guard.py` (sin tocarlo).
- `deviations.jsonl` en el git common dir (compartido por los worktrees): una línea por cada paso dejado fuera de
  alcance (`warn` en el gancho, `commit-warn` en el `pre-commit`); un rechazo no se apunta.

## Alternatives

- `scopeGuard.block` booleano más `followQuestions`: dos claves para lo que una enumeración dice sola.
- Avisar cuando la ficha no tiene `## Files`: ruido en proyectos con `taskRecord` apagado.
- Extraer los ayudantes de `questions-guard.py` a un módulo: más diff sin ganancia ahora.

## Changed because

—
