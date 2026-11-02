# Retro antes de publicar 0.4.0 en `main` (2026-10-25)

Fase 2 de las tres antes de `main`, tras la fase 1 (`/code-review` del diff contra `origin/main`: 10 hallazgos; 6
arreglados por ser serios o medios, con la revisión de esos arreglos y de los suyos; los menores, en «Pendiente» de la
bitácora). Une `/opt-tokens` y `/retro` de la sesión `e9650d36` (recogida de la 0.4.0, `gw-media-content`, notas
personales y arreglos antes de `main`).

**Estado:** aprobadas todas (P1-P7) por el usuario el 2026-10-25 y aplicadas en la rama antes de `main` (P3, P4, P6
en `8c980ad`; P1+P2, P5 y P7 por subagentes, revisadas y fusionadas). Añadido en P7: el gancho de parada no cuenta
`.claude/worktrees/`.

## Medida (`medir.py --hours 0`)

- Principal: 184 llamadas, 107k de media, 2 compactaciones (techo 159k), 19,7M de entrada. Igual que en la Fase 6
  (106k): la compactación y el reparto funcionan.
- Subagentes: 32 (659 llamadas, 59,5M de entrada, tres veces la principal); arranque medio 34k (en la Fase 6, 50k:
  el mapa ha servido). Cuatro pasaron del tope de ~35 llamadas (49, 48, 42, 38) con 108-114k de media.
- En la principal: `cifras.py` y `test_cifras.py` leídos 5-6 veces (~106k arrastrados cada uno) y `docs/traspaso.md`
  12 veces.

## Propuestas

Ordenadas por ahorro estimado y gravedad. Todas son generales para el flujo: se aplicarían aquí, que es el flujo.

- **P1 (opt-tokens + retro; comprobación automática): la celda «Último punto estable» de la bitácora, corta.** Mide
  7.095 caracteres y deja `recuperar.py --estado` en 9.231 de un tope de 9.500. En esta sesión, la salida de la
  compactación ya salió cortada («output incomplete»). Cada subagente la lee al arrancar (~2,5k tokens, arrastrados
  unas 35 llamadas: ~2,8M por sesión de 32 subagentes). Cambio: la celda dice el último punto estable en una o dos
  frases con su commit (el detalle va en «Hecho» y en los commits), y `tests/comprobar.sh` (o `doctor.py` en los
  proyectos) avisa si una celda de «Estado actual» pasa de ~800 caracteres. Riesgo: menos detalle en la bitácora; lo
  cubren «Hecho» y `git log`.
- **P2 (retro; comprobación automática + herramienta): «Hecho» con forma comprobada y un script que la rote.** En
  esta sesión, las ediciones de los subagentes dejaron cuatro entradas de «Hecho» pegadas en una sola línea
  (`…).3. 2026-10-25 —…`) y nadie lo vio hasta que lo arreglé a mano. Cambio: `scripts/bitacora.py hecho "<texto>"`
  inserta la entrada 1 y quita la sexta; el check comprueba una entrada por línea y 5 como mucho. Ahorra 2-3 llamadas
  por commit de subagente. Riesgo: ninguno; lleva tests.
- **P3 (opt-tokens; mejorar `orchestrate-dealer`): el tope de llamadas, dentro del encargo.** La skill dice «Cap a
  subagent at ~35 tool calls», pero la plantilla del encargo no lo lleva, y los encargos de esta sesión tampoco: las
  37 llamadas de más costaron ~4,2M (a ~115k cada una). Cambio: una línea en la plantilla («At ~30 calls, commit
  `WIP:` and return what is missing under MISSING»), y en la misma plantilla «if the push is rejected, `git fetch` +
  `git merge` (never rebase), push again», porque otra sesión subió a la misma rama dos veces. Riesgo: más relevos;
  el siguiente subagente arranca con 34k.
- **P4 (retro; normas del revisor): los ganchos-guarda, revisados con la lista de evasiones.** La revisión antes de
  `main` encontró en `guardia-config.py` evasiones que las revisiones por tanda no vieron (`cp … .claude/`,
  `sudo -u X rm`, `dd of=`), y el primer arreglo trajo una regresión (`sudo -uroot`). Cambio: en `REVIEW.md`, para
  los ganchos que preguntan o bloquean, el revisor prueba envoltorios con opciones (`sudo -u`, `env -u`, `nice -n`,
  `xargs -I`), el destino de los copiadores, carpetas antecesoras y los falsos positivos habituales (`git restore
  --staged`, copiar desde). Riesgo: ninguno; la revisión tarda algo más.
- **P5 (retro; acceso a la información): estado del CI sin `gh`.** Aquí no hay `gh` y el repo es privado, así que la
  regla «al cerrar cada bloque, mira el CI» no se pudo cumplir y quedó en manos del usuario. Cambio: `doctor.py` avisa
  cuando ni `gh` ni `GITHUB_TOKEN` están disponibles y dice cómo instalarlo o configurarlo (`gh auth login`); el resto
  ya lo cubre la regla. Riesgo: ninguno.
- **P6 (retro; navegación): la orden para correr un solo archivo de tests.** Un encargo mandó `python3 -m unittest
  tests.test_guardia`, que falla (`ModuleNotFoundError`); la buena es `python3 -B -m unittest discover -s tests -p
  'test_X.py'`. Cambio: esa línea en «Comprobar» de `AGENTS.md` (o en `docs/mapa-agente.md`, si se prefiere no
  cargar `AGENTS.md`). Riesgo: ninguno.
- **P7 (retro; ruido del gancho de parada): avisos de `antes-de-parar.py` con un subagente a mitad de trabajo.** Tres
  veces en esta sesión bloqueó la parada por cambios sin confirmar o commits sin subir que eran de un subagente que
  estaba escribiendo o pasando el `pre-push`; la principal respondió sin hacer nada. Cambio parcial: el `pre-push`
  deja `.git/gw-push-en-curso` con su PID mientras corre, y `antes-de-parar.py` solo avisa (no bloquea) si ese PID
  sigue vivo. No cubre la fase de edición. Riesgo: si el marcador queda huérfano, el PID muerto lo invalida.

## Para Galivelop-workflow

Este repo es el flujo: lo aprobado se aplica en la rama antes de `main`.
