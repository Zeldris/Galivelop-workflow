# Retro de la `0.7.0` antes de `main` (2026-11-15)

Fase 2 de la `0.7.0` en `ccr-d1e2d496-0vzck8`, tras la retro del bloque (`retro-2026-11-15-block-0-7.md`, hasta
`39f14ad`) y la del parche `0.6.2`: B37, E56, E57, la recogida H21, la fusión de la `0.6.2` y la fase 1. Fuentes:
`measure.py` sobre la sesión larga de la nube (`784b6819`, últimas 48 h, con sus subagentes) y sobre la sesión de la
fase 1 (`562bd148`), la bitácora y `docs/records/pending.md`.

**Estado:** aprobada por el usuario (2026-11-15): T1 aplicada como E62, T3 aplicada como B39 y R2 aprobada como
B38 a la `0.8`.

## Medida

- Sesión principal (48 h): 1.254 llamadas, contexto medio 126k (suelo 102k, techo 164k), 11 compactaciones, 158M de
  entrada. Fase 1 aparte, tras `/clear`: 24 llamadas, 99k de media, 2,4M.
- Subagentes: 10 (338 llamadas, 29M). Los 6 `gw-worker` con `sonnet` arrancan con ~13k; los 4 `general-purpose` con
  `opus` (implementación de D104 y D108, dos revisiones) arrancan con ~65k y suman 181 llamadas y 21M.
- Arrastre mayor: `docs/handoff.md` 91 lecturas (4,3M), `docs/roadmap.md` 104 (2,0M), `pending.md` 44 (1,5M).

## Lo que salió bien

- La fase 1 cerró con un diff trivial revisado en la sesión (B27), sin subagente: 24 llamadas.
- E57 ya se usa aquí: el barrido de abajo sale de su regla.

## Propuestas, de más a menos grave

- **T1 (tokens, general; `gw-orchestrate-dealer` y `.claude/agents/`).** La regla de la `0.6.2` (T3) solo lleva a
  `gw-worker` los trozos `sonnet low`; los de `opus` (ganchos, guardas, revisiones) siguen en `general-purpose`, con
  52k más de arranque por llamada. Propuesta: (a) el dealer usa `gw-worker` para cualquier peldaño, pasando `model` y
  `effort` en la llamada (el `model` de la llamada manda sobre el de la definición), y (b) una definición
  `gw-reviewer` (`Read`, `Grep`, `Glob`, `Bash`, `Skill`; `model: opus`) para las revisiones de `/code-review`.
  Ahorro: ~52k × 181 llamadas ≈ 9M por versión (~5 % del total). Riesgo de calidad: ninguno de modelo; un revisor sin
  herramientas MCP no pierde nada que `/code-review` use. Contrapeso: comparar los `Findings:` de la siguiente
  revisión con los de esta versión.
- **R2 (barrido, este repo; tarea B38 a la `0.8`).** Por E57: el script con más leves abiertos en `pending.md` es
  `scripts/handoff.py` (tocado por D104 en la `0.6.1`): la cuenta del puntero de pendientes se duplica y nada la
  vigila en un commit que solo toca `pending.md`; con `pendingFile`, `archive` exige «## Pendiente» y `check`/`recover`
  no, y si falta el archivo el mensaje nombra la bitácora; el `pre-push` lee `pendingFile` de la copia de trabajo, no
  del commit que sube; la cuenta solo mira la sección «Pendiente (de la bitácora)»; `move-pending` descarta las líneas
  que parecen punteros. Segundo candidato: `scripts/merge-branch.sh` (D117: `--defer-check` sin tests de las ramas
  diferidas; «nothing to merge» con código 0; la línea 165 del dealer). Riesgo: gastar en leves lo que pide un
  evolutivo; el usuario elige cuáles entran.
- **T3 (medida, general; `measure.py`).** «BY FILE» cuenta como archivos los argumentos de `git config`
  (`user.email`, el dominio del correo): ruido en el informe y un dato personal en él. Propuesta: no tomar como ruta
  lo que no existe en el árbol. Riesgo: ninguno.

## Sin propuesta

- 11 compactaciones en 48 h con presupuesto 1: la sesión siguió de la `0.6.2` a la recogida y a la `0.7` sin `/clear`
  entre tareas. Las reglas ya lo cubren (`/clear` al cerrar cada fase, tarea o PR); esta fase 2 empieza tras `/clear`.

## For Galivelop-workflow

T1 y T3 son del flujo; como este repo es el flujo, si se aprueban se aplican aquí mismo.
