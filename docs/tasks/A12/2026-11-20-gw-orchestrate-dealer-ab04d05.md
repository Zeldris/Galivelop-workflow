# 2026-11-20 · gw-orchestrate-dealer · pending · A12

## Why

Arreglar los 6 hallazgos de la revisión del trozo 1 (respaldo de plantillas, validación semántica en `--init`, `ui`
con BCP 47, migración con `languages` no objeto, pista de `load()`, `--code-language` único).

## Alternatives

Limitar `docs.primary` a idiomas con plantillas (descartado: Q-15 manda el respaldo `en`); normalizar los tags de
`visibleLanguages` en la migración (descartado: `ui` admite BCP 47 como `visibleLanguages`).

## Changed because

Decisión del coordinador sobre cada hallazgo; el aviso de `doctor.py` por idioma sin plantillas sigue en el trozo 2.
