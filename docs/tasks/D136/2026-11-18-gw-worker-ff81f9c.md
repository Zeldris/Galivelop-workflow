# 2026-11-18 · gw-worker · pending · D136

## Why

`git worktree remove` falla con un worktree bloqueado por un agente vivo y la limpieza de `merge-branch.sh` daba un
aviso engañoso tras una fusión correcta. Se lee `locked` de `git worktree list --porcelain` y se deja worktree y rama.

## Alternatives

Un `--force`/`unlock` automático: rechazado, mataría el trabajo de un agente vivo. No había mecanismo de «siguiente
pasada» al que sumarse; el aviso da la orden manual.

## Changed because

—
