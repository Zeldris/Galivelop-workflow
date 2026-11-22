# 2026-11-21 · gw-implement · pending · E5

## Why

Trozo 1 de E5 (Q-32, E-16): las normas de front como dato. `front.py check` valida el JSON de tokens (DTCG reducido) y
`generate` saca de él CSS, SCSS, la config de Stylelint y la matriz de Playwright, de forma determinista para que
`generated` (E72) pueda compararla.

## Alternatives

Ejecutar Style Dictionary (dependencia de npm, descartada: el repo no lleva dependencias y el generador debe probarse
con Python). Permitir alias dentro de un texto mayor (`"1px {x}"`): se rechaza para que el alias sea siempre el valor
entero y se traduzca a `var(--…)` sin ambigüedad.

## Changed because

Las claves se anidan en `front` con `browsers` parcial rellenado desde el esquema (`config.front`), porque el cargador
solo rellena claves de primer nivel. Un grupo vacío o una hoja sin `$value` falla, y el grupo de breakpoints se
comprueba antes de recorrer el árbol para dar su propio motivo. `out` por defecto: `front/generated`.
