# Retro antes de publicar 0.3.0 en `main` (2026-10-23)

Fase 2 de las tres antes de `main`, tras la fase 1 (code review contra `origin/main` y revisión de sus arreglos).

## Propuestas

- **opt-tokens P1:** tope de ~35 llamadas por subagente en `orchestrate-dealer` (las tandas de 44-55 llamadas
  promediaron 100-116k de contexto); 2 filas pequeñas por subagente como mucho.
- **opt-tokens P2:** la bitácora guarda solo las 5 últimas entradas de «Hecho», de dos líneas cada una (se leyó 39
  veces en la sesión y arrastró ~385k).
- **opt-tokens P3:** notas del proyecto en `.claude/gw/opt-tokens.md`: el check se lanza en segundo plano y se
  espera su salida, sin bucles con `pgrep -f`; medida de referencia de la sesión.
- **retro R1:** regla en `REVIEW.md` para carpetas con nombre fijo en directorios compartidos (`$TMPDIR`, `/tmp`): por
  usuario, permisos 700, rechazadas si son symlink o de otro usuario; archivos sueltos con `mktemp`.
- **retro R2:** P7 del instalador: aceptar como comprobado un CI que pasó en local cuando Actions no arranca.

**Estado:** aprobadas por el usuario y aplicadas en la rama opt-tokens P1-P3 y retro R1.

R2 queda para hablarla con el usuario después de publicar.
