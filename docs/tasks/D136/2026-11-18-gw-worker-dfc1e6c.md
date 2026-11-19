# 2026-11-18 · gw-worker · pending · D136

## Why

El /code-review halló que la pista del conflicto encadenaba `git worktree remove && git branch -d` sin mirar el
bloqueo, y que todo bloqueo se decía «de un agente vivo», así que uno viejo de un agente muerto no se limpiaba nunca.

## Alternatives

Dejar la detección dentro de `cleanup_branch` y duplicarla en la pista: descartado, se factoriza en
`worktree_locked`, definida antes del camino del conflicto.

## Changed because

`worktree_locked <ruta>` mira `git worktree list --porcelain`, deja la razón (`locked <razón>`) en `lock_reason` y
sale 0 si está bloqueado. La pista del conflicto antepone `git worktree unlock` si lo está; el aviso de limpieza
muestra la razón, dice que puede ser un agente vivo o un bloqueo viejo y da `unlock && remove && branch -d`.
