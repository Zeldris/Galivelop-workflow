# Retro del parche 0.8.1 (2026-11-19)

**Estado:** decidida por el usuario (2026-11-19): P3 y P4 aprobadas y aplicadas en `.claude/gw/gw-opt-tokens.md`;
P1 (D142) aplazada al parche `0.8.2`, P2 (D143) a la `0.9` y P5 (B47) a la `0.10`, apuntadas en
`docs/records/pending.md`.

Sesión `39d112ea` (nube, abierta en `/home/user`): D141, sellado de la `0.8.1` (H25) y fase 1 de su revisión.
Medida con `gw-opt-tokens`: 91 llamadas, contexto medio 129k (suelo 87k, techo 164k), 0 compactaciones; 11,8M de
entrada (99 % caché) y 31k de salida; 2 subagentes (0,99M). Arranque del contexto: ~79k de sistema y herramientas MCP
(91 % del suelo).

## Propuestas, por gravedad

1. **`measure.py` mide otra sesión (D142, fallo, general).** Sin `--session`, en la nube eligió `cc8f108d` (del
   2026-11-03, carpeta del repo) en vez de la sesión en curso (`-home-user`, la más nueva): la preferencia por la
   carpeta del repo (D139) gana a la más reciente. Un `gw-opt-tokens` sin `--session` informa de una sesión vieja sin
   avisar. Arreglo: la sesión en curso es la más nueva de todas las carpetas candidatas; la preferencia de D139 solo
   desempata. Con su test. Va al siguiente parche (`0.8.2`) o a la `0.9`.
2. **Copias instaladas desincronizadas, vistas tarde (automático, general).** Un cambio en `scripts/X.py` sin
   `apply.py .` solo lo vio el check completo tras subir (commit de arreglo `9feae0a`). Propuesta: el `pre-commit`
   avisa (o rechaza) si un archivo preparado de `scripts/` difiere de su copia en `.claude/gw/scripts/` preparada.
   Ahorra una vuelta de check + push (~20 min y ~10 llamadas).
3. **Push del sello cortado a los 20 min (economía, general).** El `pre-push` de un commit de sello corre casi todos
   los tests (>20 min) y el tope por defecto de una orden en segundo plano lo mató; hubo que relanzarlo. Propuesta:
   una línea en `.claude/gw/gw-opt-tokens.md` y en el paso de sellado: el push de un sello va con `timeout` de 90 min.
4. **Contexto fijo de ~79k (economía, entorno).** Casi todo el suelo es el sistema y las herramientas MCP (GitHub,
   Docs, nube). Propuesta: apuntarlo en «Costes conocidos» y que el usuario quite del entorno de este repo los
   conectores que no use (p. ej. Docs). Riesgo: ninguno si el conector no se usa aquí.
5. **Barrido de leves (B47, `0.10`).** `trace.py` es el script con más leves abiertos en `pendingFile`: D14 n.º 2
   (pliegue por `first[key]`), C11-trace n.º 3 (orden por hora), n.º 4 (`Acceptance` fijo), n.º 5 (casillas en
   bloques de código), n.º 6 (`normpath`), n.º 7 (`parse_entry` compartido con `task.py`). Una tarea B que los
   cierra todos.

Sin desvíos nuevos del guardián de alcance en este bloque (los últimos, de B9 el 2026-11-18).

## For Galivelop-workflow

Este repo es el flujo: las propuestas 1-3 y 5 se aplican aquí mismo si se aprueban.
