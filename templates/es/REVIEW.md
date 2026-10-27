<!-- galivelop-workflow v0.4.2 -->
# Guía de revisión

Lo que el revisor (`/code-review`, o cualquier agente que revise un diff) comprueba en cada diff de {{project}},
además de los fallos de siempre. Lo mecánico ya lo hacen el check ({{check}}) y los ganchos de git; aquí está lo que
pide criterio. La rellena el proyecto; el flujo nunca la sobrescribe una vez creada.

## Cómo se informa

- Antes de dar un hallazgo, intenta refutarlo: busca el código, el test o el gancho que ya lo cubre. Solo se informa
  de lo que sobrevive, con la ruta y la línea.
- Los hallazgos se escriben también en un archivo fuera del árbol (el scratchpad, o
  `"$(git rev-parse --git-dir)/review.md"`), no solo en la conversación: una compactación o un relevo se los lleva, y
  de ese archivo salen los encargos de los arreglos y los leves que se apuntan en la bitácora.
- Un dato que caduca (una versión, un precio, una cuota, un límite de un servicio externo) escrito en el diff lleva su
  fecha y su fuente; si no, es un hallazgo.
- La revisión acaba con un veredicto, uno de tres: `SHIP` (nada que arreglar), `SHIP WITH FIXES` (hay arreglos, ninguno
  bloquea) o `DO NOT SHIP` (algo grave o que rompe).

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
- Una carpeta con nombre fijo en un directorio compartido (`$TMPDIR`, `/tmp`) es por usuario, se crea con permisos 700
  y se rechaza si ya existe como symlink o de otro usuario; los archivos sueltos, con `mktemp`.
- Cada cambio en un gancho o un script lleva su caso en los tests; un caso que espera un fallo comprueba el motivo,
  no solo el código de salida. Los scripts de `.claude/gw/scripts/` se prueban en el repo del flujo y no se editan
  aquí (un cambio va al flujo como propuesta, con `gw-harvest`); esta regla vale para los scripts propios del proyecto.
- Un gancho que pregunta o bloquea se revisa **probando cómo saltárselo**: envoltorios con opciones que llevan valor
  (`sudo -u X`, `sudo -uX`, `env -u X`, `nice -n 5`, `timeout 5`, `xargs -I{}`), el destino de los copiadores (`cp`,
  `install`, `rsync`, `dd of=`, `-t DIR`), una carpeta antecesora de la protegida y una ruta relativa o con `..`; y
  los falsos positivos habituales (leer o copiar **desde** la carpeta, `git restore --staged`). Cada forma, su caso.
- `pkill -f <patrón>` (y `pgrep -f`) casa también con la orden que lo lanza cuando el patrón va en ella
  (`bash -c "… pkill -f servidor"`), y la mata: un pidfile, `pgrep -x` o un patrón que no se case a sí mismo
  (`[s]ervidor`).
- Un runbook o encargo que sigue una tarea programada (una sesión sin persona delante) se revisa como código, aunque
  case con `content`: lo que dice se ejecuta tal cual.

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
