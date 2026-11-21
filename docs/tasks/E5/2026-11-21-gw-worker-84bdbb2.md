# 2026-11-21 · gw-worker · pending · E5

## Why

`test_waits` no admite un `timeout=` literal en los tests: el límite de `run` en `test_front_sample.py` pasa por `waits.timeout` para que `GW_TEST_TIMEOUT_SCALE` lo escale.

## Alternatives

Marcarlo `# not a wait`: no escalaría en máquinas lentas.

## Changed because

—
