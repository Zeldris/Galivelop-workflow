# 2026-11-18 · gw-worker · pending · C7

## Why

Revisión de C7: `config-guard.py` no preguntaba ante `mode.py set` (un agente podía apagar `careful` o el guardián de
preguntas en silencio); `mode.py` reescribía todo gw.json con `indent=2` (CRLF, tabs y secciones compactas se perdían)
y truncaba el archivo antes de escribir.

## Alternatives

Reutilizar el escritor de `models.py`: no, tiene los mismos dos fallos. Se edita el texto del valor en su sitio
(`edit_text`), con archivo temporal y `os.replace`, y se valida que el resultado equivale al config esperado.

## Changed because

El hallazgo 1 de la revisión (grave) y los 2 y 3 (medios).
