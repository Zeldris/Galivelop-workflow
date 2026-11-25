# 2026-11-25 · gw-selector · pending · B53

## Why

El grep del contenido rechazaba código corriente cuya docstring o prosa nombraba un test. Se decide por la ruta (`redWithoutFix.testPathRegex`) y el contenido solo cuenta con marcadores anclados al inicio de línea.

## Alternatives

`testMap`: descartado, va de fuente a tests y no se puede invertir para reconocer un archivo de test. Quitar el contenido del todo: descartado, perdería los tests en línea (`#[test]` en Rust).

## Changed because

Sin cambios respecto al plan, salvo no usar `testMap`.
