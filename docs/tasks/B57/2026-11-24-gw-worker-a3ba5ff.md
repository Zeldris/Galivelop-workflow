# 2026-11-24 · gw-worker · pending · B57

## Why

El gancho `Stop` deja parar con el CI del `HEAD` subido en cola o en marcha, y nada despierta a la sesión para leerlo (el fallo de B50). Con `HEAD` subido pregunta a `ci-status.py --json` (con el plazo `stopCiTimeout`, por defecto 30 s, que mata también a los hijos `gh`/`curl`) y, si el estado es `pending`, bloquea una vez por commit (marca `<git dir>/gw-ci-warn` con los últimos 32 shas: el aviso es del commit, no de la sesión) con la orden de programar la comprobación o esperarla con `Monitor`. La clave es `stopSeverity.ciPending` (`block` por defecto, `warn`, `off`), dentro de `stopSeverity` como pide la ficha.

## Alternatives

- Una clave de primer nivel aparte: descartada, la ficha pide la clave en `stopSeverity`; se amplía su enum con `off` solo para `ciPending`.
- Bloquear también con el estado `none` (sin CI registrado aún): descartado, la ficha pide «sin veredicto (cola o en marcha)» y `none` también es un proyecto sin CI, que nunca se resolvería.
- Avisar en `warns` cuando falta `ci-status.py`: descartado, se calla (un proyecto que no lo instaló no tiene nada que leer); solo los fallos de lectura se anotan.

## Changed because

Sin cambios respecto al plan.
