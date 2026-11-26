# Retro del parche `0.9.1` (2026-11-26)

Sesión en la nube del 2026-11-26: fase 1 de la `0.9.1` (tres revisores, 19 hallazgos), D179 (17 arreglos repartidos a
cinco `gw-worker`), subida de versión y fase 2. Medida con `measure.py --hours 0`: principal 86 llamadas, 120,6k de
contexto medio, suelo 88k y techo 150k, 1 compactación; arranque fijo ~82k por llamada (68 % de la entrada);
subagentes 193 llamadas y 7,9M de entrada, todos con el modelo grande (ganchos y guardas, `gw-opt-tokens.md`).

**Estado:** aprobada (usuario, 2026-11-26): P1, P2, P3 y P6 aplicadas en la `0.9.1` (B58-B61); P4 aplazada a la `0.10` (B62); P5 aprobada para la `0.10` (D180).

## Propuestas

1. **El check apunta el verde aunque solo cambie el ledger** (ahorro; general, se aplica aquí). `scripts/check.sh`
   no apuntó el verde porque `docs/metrics/ledger.jsonl` cambió durante la ejecución (los ganchos lo escriben solos),
   y el `pre-push` repitió el check completo: unos 50 minutos y varias llamadas de espera de ~120k. Cambio: la
   comparación del árbol ignora ese archivo (clave `metricsLedger` o similar, con valor por defecto). Riesgo: ninguno
   (son métricas, `merge=union`); con su caso en los tests.
2. **Un clon superficial falla en segundos, no tras 50 minutos** (comprobación automática; general). El primer push
   falló en el `pre-push` porque `test_harvest` necesita la historia y el clon de la nube era superficial. Cambio:
   `tests/check.sh` (o `doctor.py` al arrancar) detecta `git rev-parse --is-shallow-repository` y para al principio
   con `git fetch --unshallow`. Riesgo: ninguno.
3. **El encargo de `gw-orchestrate-dealer` dice cómo crear el registro de decisiones** (skill; general). Los dos
   últimos `gw-worker` vieron rechazado su primer commit por el `commit-msg` (`taskRecord`: falta la entrada en
   `docs/tasks/<id>/`) y tuvieron que descubrir `task.py log`. Cambio: una línea en la plantilla del encargo cuando
   `taskRecord` está activo. Riesgo: ninguno.
4. **El aviso de `Findings:` no salta si los commits del bloque ya lo llevan** (comprobación; general). El commit
   que cerró D179 recibió el aviso aunque los cinco commits de los subagentes ya sumaban `Findings: 17`; añadirlo lo
   habría contado dos veces en `metrics.py quality`. Cambio: `commit-message.py` solo avisa si ningún commit desde el
   último cierre de revisión lleva `Findings:`. Riesgo: un cierre real sin el trailer pasa sin aviso si otro commit del
   bloque lo tiene; el caso va en los tests.
5. **Barrido de `whole-read.py` (D180, para la `0.10`)** (barrido del cierre). `trace.py` ya tiene el suyo (B47); el
   siguiente con dos leves abiertos es `whole-read.py`: E70 (falla abierto con `wholeReadDenyPaths` ante un comando
   que no sabe partir o un `limit` enorme) y E74 (anotar en `AGENTS.md` la excepción de los ganchos que solo
   aconsejan).
6. **`review-scope.py --worktree` en la documentación** (navegación; de este repo). B54 lo añadió en el script, pero
   ni `docs/es/` ni `docs/en/` lo nombran. Cambio: una línea junto a `reviewTrivialLines` en ambos `config.md`.

## Coste fijo (sin propuesta nueva)

El arranque fijo (~82k por llamada: sistema y herramientas MCP) sigue siendo el 68 % de la entrada, como ya recoge
`.claude/gw/gw-opt-tokens.md` (medida del 2026-11-19): solo baja desactivando conectores o servidores MCP que no se
usan en el entorno de la nube.
