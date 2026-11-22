# 2026-11-22 · gw-orchestrate-dealer · pending · D142

## Why

Arreglos de la revisión de D142 (4 hallazgos): límite conocido de la cola del transcript documentado; la línea del
selector tiene que empezar por `Session:`, se saltan las filas `isSidechain` y una palabra que no es modelo no tapa una
línea anterior; `family()` reconoce `opus-5.5` y `Opus 5.5`; el párrafo del dealer recupera su ajuste de línea.

## Alternatives

- Subir `subagentTranscriptBytes` para el aviso: no; el límite queda documentado.

## Changed because

—
