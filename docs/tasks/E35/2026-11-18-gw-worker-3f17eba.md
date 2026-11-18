# 2026-11-18 · gw-worker · pending · E35

## Why

El reintento y el registro van dentro del hilo de cada unidad (paralelo) y el apunte en el hilo principal, sin carreras en el archivo. El valor lo valida el esquema (config.load) y se lee con `config._section`, sin tocar config.py.

## Alternatives

Una función en config.py (como `test_unit_timeout`): descartada, fuera de los archivos del encargo y el esquema ya valida.

## Changed because

Nada cambió; no se reintenta un archivo que no importa (falla igual siempre).
