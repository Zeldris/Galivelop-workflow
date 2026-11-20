# 2026-11-20 · gw-orchestrate-dealer · pending · A12

## Why

Trozo 1 de A12 (Q-10 a Q-16): el bloque `languages` sustituye a `language` y `visibleLanguages` con la migración
`schemaVersion` 1 → 2 en `config.py`, validación ISO 639-1 y el accesor `languages()`.

## Alternatives

Migrar sin vistas en memoria (rompía a los consumidores del trozo 2); se dejan `language` y `visibleLanguages`
derivadas y de solo lectura en `load()` (`compat_views`, «A12 chunk 2 removes this»), nunca escritas al disco. Con el
bloque y las claves viejas a la vez, manda el bloque; con `schemaVersion` 2 y claves viejas, falla cerrado.

## Changed because

Los fixtures de `test_apply`, `test_doctor` y `test_templates` pasan al formato 2 (`languages`, `schemaVersion` 2).
