# Harvest portal-galivelop — 2026-11-15

De `9b690870` a `45823a62` (`scripts/harvest.py`). 44 commits; sin skills ni scripts del flujo cambiados. Lo nuevo
sale de 1 retro (`docs/records/retro-2026-11-14-auditoria.md`). Recogida de cierre de la `0.7` (usuario, 2026-11-15).

## Joined to another proposal

- P3 (gancho al leer entera la bitácora) @ `523931b`: el portal ya tiene `whole-read.py` instalado y registrado, y aun
  así la leyó entera 32 veces (1,49M) con 219 llamadas de Bash: el gancho no ve las lecturas por Bash. Va con
  world-maker-fantasy P3 (`2026-11-15-world-maker-fantasy.md`).

## Stays in the project

- P5 (selectores de atributo del CSS contra los componentes, `src/estilos/clases.test.ts` @ `523931b`): test de
  Vitest del portal; el flujo no trae tests de web.
- Nota de Chromium (un `import()` fallido queda en caché hasta recargar): norma de páginas perezosas, del stack web.
- Auditoría, tarjeta de equipo, piezas de redes y `tools/qa/recorrido.cjs`.
