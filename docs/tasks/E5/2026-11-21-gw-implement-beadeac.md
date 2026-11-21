# 2026-11-21 · gw-implement · pending · E5

## Why

Revisión del trozo 1 (11 hallazgos y 2 observaciones): el generador producía SCSS que Sass rechaza (alias antes de su
destino, `16.`, `nan`), nombres que Sass confunde (`_` y `-`), pesos con nombre que CSS descarta, un fragmento de
Stylelint que dejaba pasar `rgb(…)` y las abreviadas, y valores que podían inyectar CSS.

## Alternatives

Escribir en SCSS el valor ya resuelto en vez de la variable del alias: pierde la relación entre tokens al leer el
archivo; se prefirió ordenar por profundidad de alias. Validar la sintaxis de color completa: demasiado para un
subconjunto, se rechazan solo los caracteres y marcadores que rompen la salida.

## Changed because

`front` pasa a `PROFILE_DENIED`: sus claves deciden los bytes de lo generado, que deben ser los mismos para todos y el
CI. Las listas de Stylelint, `ignoreValues` y el alto por defecto salen del script a `front` (todo configurable).
