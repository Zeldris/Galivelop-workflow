# Retro del parche 0.8.2 (2026-11-22)

**Estado:** pendiente de la decisión del usuario.

Sesión `784b6819` (nube, abierta en `/home/user`), parche `0.8.2` con `gw-orchestrate-dealer` (D142, D144-D166) y
fase 1 de su revisión. Medida con `gw-opt-tokens` desde la base con `main` (4ca45d0, 2026-11-19; incluye el final de
la obra de la `0.9`): principal 1469 llamadas, contexto medio 126k (suelo 105k, techo 160k), 11 compactaciones con un
presupuesto de 2; 184,6M de entrada (98 % caché) frente a 26,8M de los 14 subagentes (13 %). Lecturas más repetidas:
`docs/handoff.md` 94 veces (5,1M arrastrados) y `docs/roadmap.md` 101 veces (4,0M), casi todas con `cat`/`sed`.

## Propuestas, por gravedad

1. **El parche estuvo sin subir hasta el final (relevos, general).** Cada `check.sh; push.sh` caía en el check (tests
   viejos tras D163, un test inestable) y `origin/version/0.8.2` siguió en `f6f6529` todo el parche: un reinicio del
   contenedor lo habría perdido. Propuesta: `push.sh --wip` sube un commit `WIP:` sin esperar al verde (el `pre-push`
   lo deja pasar en una rama que no es `main` y lo apunta), y `before-stop.py` lo recomienda cuando hay commits sin
   subir y el último check está en rojo. Riesgo: un rojo subido; contrapeso: solo con `WIP:` y nunca a `main`.
2. **Un parser de lo que escribe el agente, probado solo con ejemplos inventados (revisión, general).** D142 pasó la
   revisión de su trozo y su regex no reconocía ninguna de las 32 líneas reales del selector (en español). La fase 1
   lo vio leyendo transcripciones. Propuesta: regla en `REVIEW.md`: el código que lee salida de agentes o de usuarios
   (líneas del selector, trailers, respuestas a preguntas) lleva al menos un test con una muestra real copiada de una
   transcripción o de la bitácora. Riesgo: ninguno.
3. **Lecturas enteras de la bitácora y del roadmap por `Bash` (economía, general).** `whole-read.py` (B26) solo vigila
   el `Read`; `cat docs/handoff.md` o `sed -n 1,80p` se le escapan, y fueron ~9M arrastrados. Propuesta: que también
   avise de un `cat`/`sed`/`head` del `log` o de `roadmapFiles` por encima de `wholeReadWarnBytes`, con la orden que
   da lo mismo (`recover.py --state`, `roadmap.py show <id>`). Riesgo: un aviso de más; se calla con un rango corto.
4. **La revisión de la fase 1 pasó el tope de un subagente (dealer, general).** El revisor hizo 74 llamadas con 101k
   de contexto medio (tope ~30). Propuesta: en `gw-orchestrate-dealer`, con un diff de fase 1 de más de N líneas
   (clave nueva `review.splitLines`), dos o más revisores por grupos de archivos de `review-scope.py`, más uno corto
   que cruce los contratos entre grupos. Riesgo: perder roturas entre grupos; contrapeso: ese revisor cruzado.
5. **La sesión no se limpió entre versiones (economía, entorno).** 82 compactaciones en una sesión que abarca varias
   versiones y 87 % del gasto en la principal. La regla existe (`/clear` al cerrar tarea o PR); en la nube sin
   `/clear` el usuario puede abrir una sesión nueva. Propuesta: al cerrar este parche, sesión nueva para la `0.9`.
   Riesgo: ninguno; la bitácora basta para retomar.
6. **Barrido de leves (B, `0.10`).** Tras `trace.py` (B47, ya en la `0.10`), el script con más leves abiertos en
   `pendingFile` es `apply.py` (6). Una tarea B que los cierre todos, para la `0.10`, si se aprueba.

Desvíos del guardián de alcance en este bloque: un commit de D156 llevaba archivos de D166 (`commit-warn`, 14); es un
trozo que se coló en otro, no una regla que estorbe. Sin propuesta.

## For Galivelop-workflow

Este repo es el flujo: las propuestas 1-4 y 6 se aplican aquí mismo si se aprueban; la 5 es del usuario.
