# Harvest world-maker-fantasy — 2026-11-11

De `d35bfaa1` a `d8ef94ad` (`scripts/harvest.py`). 243 commits: mapas, zonas, puerta 3.4, lotes F-I y narrador
local; sin skills ni scripts del flujo cambiados. Lo nuevo sale de 5 retros. Recogida de cierre de la `0.6` (H18).

## P1. El encargo de arreglos del dealer dice qué hacer con el commit

- **Source:** `docs/records/retro-2026-11-11-lotes-f-i-a-main.md` candidata 3 @ `bc905bda` (retro)
- **What changes:** la plantilla de arreglos de `skills/gw-orchestrate-dealer/SKILL.md` dice «deja el cambio sin
  commitear» o «actualiza tu fila con `handoff.py` y commitéala junto».
- **Why it is general:** un subagente commiteó sin la bitácora, el `Stop` la pidió y el `--amend` lo bloquea el modo
  automático: un segundo commit de más.
- **Version bump:** patch
- **Status:** aprobada (2026-11-11) → D72

## P2. `related-tests.sh` imprime el número de archivos, no la lista

- **Source:** `docs/records/retro-2026-11-10-mapas-a-main.md` propuesta 2 @ `cbcd9372` (retro)
- **What changes:** los mensajes de inicio y de rojo de `scripts/related-tests.sh` dicen «N archivos» y la ruta de
  un temporal con la orden completa, en vez de ~150 rutas.
- **Why it is general:** ahorra tokens en cualquier proyecto grande.
- **Version bump:** patch
- **Status:** aprobada (2026-11-11) → D74

## P3. `recover.py --state` avisa de revisión atrasada

- **Source:** `docs/records/retro-2026-11-10-puerta-3.4.md` candidata 2 @ `14ebfd66` (retro)
- **What changes:** aviso en el estado de arranque cuando los commits desde la última revisión pasan de un umbral
  (clave nueva o `changeSize.block`). Hoy solo avisa el `commit-msg`, al commitear.
- **Why it is general:** caso real: 18 tandas y 48 commits sin revisar.
- **Version bump:** minor
- **Status:** aprobada (2026-11-11) → D85

## P4. El `Stop` no pide subir con subagentes en segundo plano

- **Source:** `docs/records/retro-2026-11-11-narrador-local.md` R6 @ `1b312295` (retro)
- **What changes:** ampliar D41 en `scripts/before-stop.py`: con subagentes activos, decir «espera al subagente y
  sube después» en vez de pedir commit. Falta comprobar si el gancho puede saber que hay subagentes en marcha.
- **Why it is general:** provoca un `WIP:` a medias en cualquier proyecto que reparta.
- **Version bump:** patch
- **Status:** aprobada (2026-11-11) → D88

## P5. `measure.py` mide la sesión anterior tras un `/clear`

- **Source:** `docs/records/retro-2026-11-11-narrador-local.md` @ `1b312295` (retro)
- **What changes:** si la sesión actual tiene menos de N llamadas (clave nueva), `measure.py` mide por defecto la
  anterior de la misma rama; hoy hay que pasar `--session`.
- **Why it is general:** tras `/clear` (que el flujo recomienda) la medida sale vacía en cualquier proyecto.
- **Version bump:** minor
- **Status:** aprobada (2026-11-11) → B29

## P6. Plantilla de licencia doble en `gw-init`

- **Source:** `docs/records/retro-2026-11-05-licencias.md` @ `3d2edfb1` (retro)
- **What changes:** `gw-init` ofrece MIT para todo o MIT para el código más CC BY-NC-SA 4.0 para el contenido, con
  la nota de terceros.
- **Why it is general:** útil en cualquier proyecto con contenido creativo; opción nueva.
- **Version bump:** minor
- **Status:** aprobada (2026-11-11) → D87

## P7. Cierre de una ronda de pruebas: parar lo levantado

- **Source:** `docs/records/retro-2026-11-11-narrador-local.md` @ `1b312295` (retro)
- **What changes:** la guía de rondas (o `gw-opt-tokens`, que la cita) añade un paso de cierre que llama a un script
  del proyecto para parar servidores, modelos e inhibidores de suspensión.
- **Why it is general:** cualquier ronda deja procesos vivos; el script es de cada proyecto.
- **Version bump:** patch
- **Status:** aprobada (2026-11-11) → D75

## Stays in the project

- P452, P443 (`WMF_HUIDA_PRUEBAS`), P441, QA-311…QA-321, el narrador local con Ollama y su script de parada.

## Already here

- `docs/records/retro-2026-11-11-narrador-local.md` R5 (modelo en el encargo, `sonnet` por defecto con plan
  cerrado): `gw-selector` y el dealer ya lo piden; solo faltaría exigir el motivo escrito para Opus.

## Sin novedades

- `private-project-2` (`70b0396a`) y `labs-log-detective` (`bc501f91`): nada desde la última recogida.
