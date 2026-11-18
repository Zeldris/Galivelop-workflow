# 2026-11-18 · session · pending · D94

## Why

En el runner de macOS cargado, 10 vueltas de `sleep 0.1` pasaron de 2 s: el límite de 1 s no cortó un `ls-remote` de 2 s. Se suma el tiempo real (`$SECONDS`, segundos enteros; una diferencia mayor que el límite asegura que pasó) y el test usa 4 s para tener margen.

## Alternatives

`date +%s` en cada vuelta (un proceso más por vuelta) o un binario `timeout` (macOS no lo trae).

## Changed because

—
