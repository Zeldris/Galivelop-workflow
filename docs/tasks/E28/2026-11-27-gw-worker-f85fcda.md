# 2026-11-27 · gw-worker · pending · E28

## Why

B3 y D4 de `docs/records/security-review-E28.md` (decisión del usuario: entorno mínimo y `working-directory`
dentro del repo). `ci-local.py` pasaba todo el entorno (tokens) a los `run:` del repo, corría un paso fuera del repo
y `--record` escribía a través de un enlace simbólico.

## Alternatives

- Lista de variables prohibidas (denylist) en vez de una mínima: descartada, siempre falta un nombre de secreto.
- Clave anidada `ciLocal.passEnv`: se eligió la plana `ciLocalPassEnv`, como sus hermanas `ciLocalLog` y
  `ciLocalWorkflows`.

## Changed because

—
