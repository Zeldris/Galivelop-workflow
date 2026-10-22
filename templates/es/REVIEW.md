<!-- galivelop-workflow v0.2.0 -->
# Guía de revisión

Lo que el revisor (`/code-review`, o cualquier agente que revise un diff) comprueba en cada diff de {{project}},
además de los fallos de siempre. Lo mecánico ya lo hacen el check ({{check}}) y los ganchos de git; aquí está lo que
pide criterio. La rellena el proyecto; el flujo nunca la sobrescribe una vez creada.

## Un dato, un sitio

- Un dato que ya vive en un sitio (un archivo de configuración, uno de datos, una constante) no se repite a mano en
  el código, la documentación ni el README; si hay que repetirlo, todas las copias cambian en el mismo commit.
- La configuración del flujo vive solo en `.claude/gw.json` y solo la lee `.claude/gw/scripts/config.py`.

## Ganchos y scripts

- La raíz del repo se saca de la ruta del script (`$(dirname "$0")`) o de `git rev-parse --show-toplevel`, nunca de
  `$CLAUDE_PROJECT_DIR` ni del directorio actual: una sesión puede arrancar fuera del repo.
- Un gancho de subida comprueba **el commit que se sube**, no la carpeta de trabajo.
- Los ganchos **fallan cerrados** cuando les falta un dato (un commit que el clon no tiene, una API que no responde),
  con la orden que lo arregla.
- Los scripts de shell corren en bash 3.2 (macOS): nada de `mapfile` ni arrays asociativos.
- Cada cambio en un gancho o un script lleva su caso en los tests; un caso que espera un fallo comprueba el motivo,
  no solo el código de salida.

## Traído de otro repo: se adapta a los contratos de este

- El código, los scripts o las reglas traídos de otro repositorio se comprueban contra **este** repo, no contra el
  original: formatos, rutas, extensiones de archivo, patrones de nombres, constantes, claves de configuración e
  identificadores de tarea.
- Lo que viene de un proyecto que sube de otra forma (directo a la rama protegida, o por pull request) se adapta a
  cómo sube este a `{{protectedBranch}}`.
- Una tabla o un ejemplo de una guía que lee un script lo lee ese script en un test.

## Idiomas visibles

- Si `.claude/gw.json` declara `visibleLanguages`, todo texto nuevo que vea un usuario existe en cada uno de esos
  idiomas (etiquetas, textos alternativos, títulos de página, mensajes), y una traducción es de verdad, no el mismo
  texto.

## Reglas del proyecto

<!-- Las rellena el proyecto: lo que nunca se publica, reglas del dominio, accesibilidad, rendimiento, seguridad. -->
