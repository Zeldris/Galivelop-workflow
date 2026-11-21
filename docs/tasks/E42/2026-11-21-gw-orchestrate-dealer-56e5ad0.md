# 2026-11-21 · gw-orchestrate-dealer · pending · E42

## Why

La revisión de `da48833` halló 13 fallos de `check_seo.py` y de las referencias (5 medios, 8 leves): sitemaps índice, URLs
limpias, base del sitio, fechas parciales, hreflang regional, mensajes con supuestos del portal y datos sin fuente.

## Alternatives

Umbrales y `DEFAULT_IGNORE` como claves de `.claude/gw.json`: descartado, el script lee solo sus flags y la nota del
proyecto dice la orden que corre; una clave por umbral habría exigido config, esquema y docs para algo que solo usa esta
skill. Las URLs limpias se resuelven con un alias por página, no reescribiendo la URL canónica de la página.

## Changed because

Revisión de `da48833`: cada hallazgo tiene su caso en `TestReviewFindings`.
