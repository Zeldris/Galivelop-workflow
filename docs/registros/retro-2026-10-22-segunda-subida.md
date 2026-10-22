# Retro — segunda subida a `main` (2026-10-22)

**Estado:** pendiente de la decisión del usuario.

Lo revisado: desde la primera subida (`603ca36`) hasta `d01091e`. El mensaje del `pre-push`, `version.py`,
`release.yml`, la segunda recogida de Tarkor (7 propuestas aplicadas) y dos rondas de `/code-review` con 10
hallazgos cada una. Medida de `/opt-tokens`: sesión principal con 62 llamadas, contexto medio **585k**, 0
compactaciones; 5 subagentes con 79 llamadas y un arranque medio de 61k.

## Propuestas

### R1. La sesión sigue siendo la misma de la creación y su contexto ya pasa de 580k (gasto, alta)

- **Qué pasó:** la T1 aprobada en la primera retro («abrir la sesión desde el repo y `/clear` al cerrar cada fase»)
  no se ha podido aplicar a esta sesión, que sigue abierta en `/home/user` y sin compactación. Cada llamada cuesta ya
  ~585k de contexto: casi el doble que en la primera medida.
- **Propuesta:** al terminar esta subida, **cerrar esta sesión**. La siguiente se abre desde
  `/home/user/Galivelop-workflow`, con la bitácora al día. No hace falta cambiar nada en el flujo, porque la regla ya
  existe; falta aplicarla.
- **Riesgo:** ninguno. La bitácora y los commits llevan todo el estado.

### R2. Cada ronda de revisión sobre código de subagentes encuentra unos 10 fallos (calidad, media)

- **Qué pasó:** las dos revisiones de esta tanda dieron 10 hallazgos cada una, casi todos de casos límite (push
  forzado lateral, clon divergido, marcadores que faltan, CRLF). La revisión al volver cada trozo (R5) los caza, pero
  después, y cuesta una ronda más de subagente.
- **Propuesta (general, `orchestrate-dealer`):** en los encargos de código de guarda o de scripts, pedir al subagente
  que **liste primero los casos límite** (estados de git, plataformas, entradas vacías o raras) y escriba un test por
  cada uno antes de dar el trozo por hecho. La revisión queda como red de seguridad, no como primera pasada.
- **Riesgo:** encargos un poco más largos. Compensa: una ronda de revisión y arreglo cuesta 2-3,5M de entrada.

### R3. Lo que funcionó

- Subir como `WIP:` con `--no-verify` el trabajo a medias de un subagente, cuando lo pidió el gancho de parada: no se
  perdió nada y el commit final lo dejó verificado.
- `recoger.py` encontró su propio fallo (clon atrasado) en la primera recogida real con commits nuevos.
- Marcar en el informe de la recogida qué propuesta conviene esperar (P5) ayudó a decidir.

## Decisión del usuario

_(pendiente)_
