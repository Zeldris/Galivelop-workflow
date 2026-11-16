# Release de GitHub `v0.7.1` (textos)

- **Etiqueta:** `v0.7.1`, sobre `7a6d1bd`, el commit de `main` de la subida del 2026-11-16.
- **Título:** el bloque de abajo.
- **Cuerpo:** el segundo bloque. La entrada completa está en el CHANGELOG.
- **Publicada:** pendiente; a mano por el usuario en local (elegido por él): `gh release create v0.7.1 --target main
  --title "Galivelop-workflow v0.7.1" --notes-file <cuerpo>`, con el cuerpo de abajo.

```text
Galivelop-workflow v0.7.1
```

````markdown
## Galivelop-workflow v0.7.1 — 2026-11-16

**ES** · [English below](#en)

Parche de la recogida de apertura de la `0.8`.

### Contexto de arranque

- Con el presupuesto de compactaciones pasado, si lo que más pesa en el arranque es el resto del sistema (prompt,
  herramientas, MCP), `recover.py --state` y la alarma de bucle de compactación piden quitar los conectores y
  servidores MCP que no se usan en vez de `/clear`. Solo con un arranque por encima de `contextGuard.warn`; se apaga
  con `contextGuard.systemAdvice: false`.

### Versiones y CI

- `version.py <X.Y.Z>` avisa al sellar, sin fallar, si a la versión nueva le falta su recogida.
- `ci-status.py` sigue dando en rojo un job cancelado antes de ejecutar ningún paso, pero lo dice y da la orden para
  relanzarlo (`gh run rerun <run> --failed`).

### Actualizar un proyecto

Desde una sesión en el proyecto, la skill `gw-update` y luego `python3 .claude/gw/scripts/doctor.py`. Clave nueva en
`.claude/gw.json`, con su valor por defecto: `contextGuard.systemAdvice` (`true`).

Entrada completa: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.7.1/CHANGELOG.md).

<a id="en"></a>

**EN**

Patch from the `0.8` opening harvest.

### Startup context

- With the compaction budget spent, if the largest share of the startup is the rest of the system (prompt, tools,
  MCP), `recover.py --state` and the compaction-loop alarm ask to disable unused connectors and MCP servers instead
  of `/clear`. Only for a startup over `contextGuard.warn`; `contextGuard.systemAdvice: false` turns it off.

### Versions and CI

- `version.py <X.Y.Z>` warns at the seal, without failing, when the new version has no harvest.
- `ci-status.py` still reports red a job cancelled before running any step, but says so and gives the command to
  rerun it (`gh run rerun <run> --failed`).

### Updating a project

From a session in the project, the `gw-update` skill, then `python3 .claude/gw/scripts/doctor.py`. New key in
`.claude/gw.json`, with its default: `contextGuard.systemAdvice` (`true`).

Full entry: [CHANGELOG](https://github.com/zeldris/Galivelop-workflow/blob/v0.7.1/CHANGELOG.md).
````
