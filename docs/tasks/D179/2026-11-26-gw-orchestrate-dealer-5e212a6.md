# 2026-11-26 · gw-orchestrate-dealer · pending · D179

## Why

Revisión B53, hallazgos 2, 3 y 17: el ancla de testRegex no aceptaba tabuladores, testPathRegex veía la ruta
absoluta del checkout y en config.md faltaba un separador.

## Alternatives

Quitar "$root/" solo al comparar con testPathRegex; descartado: `git show HEAD:<ruta absoluta>` también fallaba,
así que los archivos se pasan a rutas relativas al repo al principio.

## Changed because

—
