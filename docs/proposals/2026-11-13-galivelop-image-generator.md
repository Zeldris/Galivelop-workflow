# Harvest galivelop-image-generator — 2026-11-13

De `db9c3645` a `529468bc` (`scripts/harvest.py`); sin skills ni scripts del flujo cambiados. Lo nuevo sale de 3
retros. Recogida de la `0.6.0` (H19).

## P1. La fase 2 pide lanzar `gw-opt-ai`, que el agente no puede invocar

- **Source:** `docs/records/retro-2026-11-12-hojas-repos.md` W1 @ `3666cb06` (retro)
- **What changes:** `skills/gw-opt-ai/SKILL.md` tiene `disable-model-invocation: true` y la fase 2 de las plantillas
  de `AGENTS.md` pide al agente lanzarla. O se quita la marca, o la fase 2 dice que la lanza la persona.
- **Why it is general:** contradicción en todos los proyectos con IA local; la persona tuvo que escribirla.
- **Version bump:** patch
- **Status:** aprobada (2026-11-13) → B30

## P2. El aviso de celdas largas de la bitácora se ignora

- **Source:** `docs/records/retro-2026-11-12-hojas-repos.md` W2 @ `3666cb06` (retro)
- **What changes:** `handoff.py` ofrece mover a «Hecho» lo cerrado de una fila de más de 800 caracteres, o el gancho
  falla a partir de un segundo tope (clave nueva).
- **Why it is general:** un aviso que sale en cada commit deja de leerse (una celda llegó a 10 115 caracteres).
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → D96

## P3. El subagente no responde hasta acabar su trabajo de fondo

- **Source:** `docs/records/retro-2026-11-12-hojas-repos.md` W3 @ `3666cb06` (retro)
- **What changes:** la plantilla de encargo de `gw-orchestrate-dealer` añade «no respondas hasta que acabe» a lo que
  ya dice del push en segundo plano.
- **Why it is general:** un subagente reenvió su informe cuatro veces; la principal lo lee cuatro veces.
- **Version bump:** patch
- **Status:** aprobada (2026-11-13) → D92

## P4. `scripts/push.sh <rama>`

- **Source:** `docs/records/retro-2026-11-13-huecos-gimg.md` W1 @ `9a4dbecd` (retro)
- **What changes:** script que sube con reintentos 2, 4, 8 y 16 s (uno largo en segundo plano si el servicio de
  credenciales da 503) y solo da éxito si `git ls-remote origin <rama>` coincide con `HEAD`; `AGENTS.md` apunta a él.
- **Why it is general:** cada sesión escribe el bucle de `AGENTS.md` a mano y el estado de salida de la tubería es
  fácil de perder.
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → D94

## P5. `gw-init` con `agentSignatures: false` escribe la regla en `CLAUDE.md`

- **Source:** `docs/records/retro-2026-11-13-huecos-gimg.md` W2 @ `9a4dbecd` (retro)
- **What changes:** con `agentSignatures: false`, la plantilla de `CLAUDE.md` lleva la línea «Sin firmas de Claude»
  (la que tiene este repo): el recordatorio de atribución de Claude Code choca con el `commit-msg`.
- **Why it is general:** cada sesión nueva de cualquier proyecto con firmas apagadas falla el primer commit.
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → E49

## P6. Aviso al leer capturas sueltas

- **Source:** `docs/records/retro-2026-11-13-interfaz-r10.md` W1 @ `e7dd5ec3` (retro)
- **What changes:** gancho `PreToolUse` de `Read` que avisa, sin bloquear, al leer varias capturas sueltas del
  scratchpad y sugiere montarlas en una hoja (la orden, una clave del proyecto).
- **Why it is general:** cada imagen cuesta tokens fijos; vale para cualquier proyecto con interfaz (encaja con los
  checks de front de la `0.8`, E9-E16).
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → E50

## P7. Aviso de contexto cerca de la ventana con el presupuesto gastado

- **Source:** `docs/records/retro-2026-11-13-interfaz-r10.md` W2 @ `e7dd5ec3` (retro)
- **What changes:** `recover.py --state` o el gancho `Stop` avisan cuando el contexto del tramo se acerca a la
  ventana y el presupuesto de compactaciones ya está gastado, y proponen cerrar el paso con `/clear`.
- **Why it is general:** hoy solo avisa `context_guard.py` tras la compactación (B21, D65), cuando ya se pagó.
- **Version bump:** minor
- **Status:** aprobada (2026-11-13) → B31

## Stays in the project

- `intentos-en-hoja.py` (citado en P6): la herramienta que monta la hoja es del proyecto.
