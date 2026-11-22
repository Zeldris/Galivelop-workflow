# 2026-11-22 · gw-orchestrate-dealer · pending · D142

## Why

Q-6: el gancho de inicio avisa si el modelo de la sesión no es el que recomendó el `gw-selector`. Lo más robusto y
mínimo: la última línea `Session: <modelo> <esfuerzo>` de un texto del asistente en la cola del transcript, contra el
`model` de la entrada del gancho o, si no viene, el del último mensaje del asistente; solo familias (opus, sonnet,
haiku, fable), porque el esfuerzo no queda en el transcript.

## Alternatives

- Comparar también el esfuerzo: no hay dato fiable en el transcript; se descartó.
- Un gancho `UserPromptSubmit` que avise en cada turno: más ruido y coste; queda como pregunta.
- Correr `session-start.sh` también en `compact`: cambia el matcher de los ajustes; queda como pregunta.

## Changed because

—
