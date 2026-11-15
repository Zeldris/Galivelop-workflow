# Harvest instalador-wmf-tarkor — 2026-11-15

De `9fce3d18` a `8ae98626` (`scripts/harvest.py`). 22 commits; ninguna skill del flujo cambiada, un script del flujo
reescrito (`tools/dev/version.py`) y 1 retro (`docs/records/retro-2026-11-15-flu-10.md` @ `6eea9fd`). Recogida de
apertura de la `0.8` (H22).

## P1. El aviso de bucle de compactación no pide `/clear` si lo pesado es el sistema

- **Source:** `docs/records/retro-2026-11-15-flu-10.md` P1 @ `6eea9fd` (retro)
- **What changes:** cuando `recover.py --state` avisa de que se pasó el presupuesto de compactaciones («push and ask
  for /clear», `scripts/recover.py` ~581), mira el desglose de `scripts/context_guard.py`: si el mayor culpable del
  arranque es «rest of the system (system prompt, tools, MCP)», dice que un `/clear` no lo baja y que solo lo baja
  quitar conectores que no se usan, sin pedir parar.
- **Why it is general:** en el instalador el arranque estaba al 67 % del tope y el 89 % era sistema y MCP; pedir
  `/clear` ahí gasta un relevo sin bajar nada. Pasa en cualquier proyecto con varios conectores.
- **Version bump:** patch (arreglo de un aviso que engaña: `0.7.1`)
- **Status:** proposed

## Joined to another proposal

- P2 (aviso al releer entero un archivo grande ya leído y sin cambios) @ `6eea9fd`: el flujo ya trae `whole-read.py`
  en `PreToolUse` de `Read`; el instalador releyó `docs/05-plan-de-trabajo.md` 24 veces (~238k) y `release.yml` 14
  (~119k). Lo que falta es lo de E58 (lecturas por `cat`/`sed` en Bash) y un criterio nuevo: avisar solo si el
  archivo ya se leyó entero en la sesión y no ha cambiado. Va a E58 como evidencia y ampliación.

## Already here

- P3 (el proxy de la nube da 403 al subir una etiqueta; el agente prepara y la persona la sube): está en `AGENTS.md`
  («Tras la subida a `main`») y en la bitácora («Para la próxima publicación»).

## Stays in the project

- `tools/dev/version.py` (`cea6845`, `e80a4af`): reescrito para el proyecto (versión en `tauri.conf.json` copiada a
  `package.json`, `Cargo.toml` y `Cargo.lock`; órdenes en español; notas de `CHANGELOG.md`). No es el
  `scripts/version.py` del flujo, que sella sus propios archivos.

## Nothing new

- galivelop-image-generator (`6e73f1ec` → `46248251`, 17 commits): su retro `retro-2026-11-15-l7.md` dice «Nada: P3
  ya estaba en el flujo».
- portal-galivelop (`45823a62` → `c926bcc9`, 1 commit): revisión semanal de los proyectos, sin ideas para el flujo.
- labs-log-detective, private-project-1, private-project-2, private-project-3, private-project-4 y
  world-maker-fantasy: sin commits desde la recogida de cierre de la `0.7`.
