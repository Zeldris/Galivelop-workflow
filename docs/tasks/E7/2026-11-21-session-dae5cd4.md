# 2026-11-21 · session · pending · E7

## Why

Un proyecto con `front.tokens` no corría la visual ni la matriz entera en su CI: solo el `pre-push` (`run fast`)
y el cierre en local (Q-35).

## Alternatives

Sacar los navegadores del config con un script en línea en cada CI (como hacía el de este repo): descartado,
`front.py install --matrix` lo hace con tests y un solo sitio. Meter `run full` en los comandos de `check`: no, el
proyecto los escribe y el paso aparte se salta solo sin `front.tokens`.

## Changed because

—
