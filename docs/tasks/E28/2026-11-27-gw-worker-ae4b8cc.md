# 2026-11-27 · gw-worker · pending · E28

## Why

B4, D3 y D5 de `docs/records/security-review-E28.md`: nombres fijos en `/tmp` abiertos siguiendo enlaces, `npm ci`
con los scripts de instalación de los paquetes y un `scripts/is-code.sh` del proyecto ejecutado en cada Edit/Write.

## Alternatives

- Candado: `O_NOFOLLOW|O_CREAT` y comprobación de dueño (elegida) frente a mover el estado a una carpeta privada
  (cambiaría la ruta que limpia `recover.py --state`).
- Registros: una carpeta `mktemp -d` por ejecución (elegida) frente a `mktemp` por archivo (dos nombres que pasar).
- `is-code.sh`: el del flujo junto al gancho si vive en el repo, si no la regla en Python (elegida); copiar la regla
  siempre en Python perdería la lectura del config por commit de `is-code.sh`.

## Changed because

—
