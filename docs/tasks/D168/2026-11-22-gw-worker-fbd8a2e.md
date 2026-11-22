# 2026-11-22 · gw-worker · pending · D168

## Why

El selector leía el informe entero (~3.7k tokens) y solo usa la tabla «By model»; el informe no trae una línea de resumen, así que se filtra esa sección.

## Alternatives

Una opción nueva de `metrics.py` para dar solo esa sección (más código para un recorte que un `sed` ya hace).

## Changed because

—
