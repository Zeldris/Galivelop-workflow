# Revisión de anonimización E29 (2026-11-27)

Tres lectores de solo lectura sobre `ccr-96d7a385-yx2p8o` (`a24b3ca`): el historial entero (1435 commits, 14 ramas
remotas, 20 etiquetas), los documentos del árbol y el diseño de `private-check` con sus excepciones.

**Este registro es público:** no copia ningún dato privado. Los nombres de proyectos privados van como **N1-N6**, y un
archivo cuyo nombre lleva uno de ellos se escribe con `<Nn>` en su lugar. La correspondencia está solo en la máquina
del usuario y en el bloc temporal de la sesión.

**Limpio:** claves y tokens (en el árbol y en el historial), correos distintos del del dueño y de los de ejemplo,
rutas personales, IP (solo `127.0.0.1`), teléfonos, enlaces de sesión en el árbol y el registro de tokens (solo ramas
`ccr-*` de este repo, ids de sesión de 8 caracteres, modelo y tokens). Los unos 420 usos de `private-project-N` están
bien.

Severidad: alta, media, baja. «Decisión» la rellena el usuario (pregunta de la columna).

## A. Nombres privados publicados

| Id | Dónde | Sev. | Problema | Arreglo propuesto | Decisión |
|---|---|---|---|---|---|
| A1 | `main`: 10 recogidas `docs/proposals/2026-11-xx-<N5>.md` y otros 15 archivos (25 en total) | alta | N5, apuntado como privado el 2026-10-27, sigue con su nombre real en el árbol de `main`: nunca se le puso alias porque el check de nombres nunca corrió | alias `private-project-N`: `git mv`, títulos, cuerpos, CHANGELOG y `state.json` de las recogidas | a (Q-48) |
| A2 | 47 sitios: `docs/proposals/2026-10-25-<N6>.md`, recogidas «sin novedades» y `CHANGELOG.md` | media | N6 aparece sin alias; no se sabe si es público | si es privado, como A1; si es público, se acepta | a (Q-49) |
| A3 | historial de `main` (N1: 40 commits, N2: 19, N3: 14, N4: 9, N5: 27) y el árbol de 6 ramas viejas (`version/1.0.0`, `ccr-05edcf12-0gntze`, `ccr-6dfbc880-ddr41g`, `ccr-76251061-b1yiwq`, `claude/galivelop-workflow-inicio`, `agent/A10-mkt-sheet`) | alta | N1-N4 se cambiaron por alias en `0cb929bc` (2026-11-02) sin reescribir el historial («El historial no se reescribe»): siguen en los commits viejos y en el árbol de esas ramas | ver Q-50 | a (Q-50) |
| A4 | recogidas de `private-project-1..3` (líneas «Fuente») | baja | los nombres de archivo de sus retros dicen el tema, y algunas nombran el stack y el hosting: pistas débiles, sin nombre, dominio ni cliente | aceptar; que `harvest.py` cambie los nombres de archivo de retro por `retro-<fecha>-<n>` | a (Q-56) |
| A5 | `docs/records/pending.md` («proyectos nuevos para la próxima recogida», `c948e9bf`, 2026-11-28; en la rama, no en `main`) | media | tras los alias de W1, uno de N5/N6 vuelve a salir con su nombre real, como repo público con `.claude/gw.json` | si sigue siendo privado, su alias `private-project-N`; si ya es público, aceptarlo y quitarlo de la lista local | a (Q-58): `private-project-6` |

## B. Metadatos del historial

| Id | Dónde | Sev. | Problema | Arreglo propuesto | Decisión |
|---|---|---|---|---|---|
| B1 | 140 commits de `main` (`3e46544d`..`40b32a00`, 2026-10-21 a 2026-10-26) | media | trailers `Co-Authored-By: Claude` y `Claude-Session:` con 3 ids de sesión reales, de antes de la regla «sin firmas» | solo reescribiendo el historial (Q-50) | a (Q-50) |
| B2 | `c470a573`, `b7063f13`, `91fdddbe` (2026-10-31, ediciones del README en la web de GitHub), en `main` | media | el autor lleva el nombre completo del dueño, no `Zeldris` | solo reescribiendo el historial (Q-50); para adelante, nombre público en la cuenta de GitHub o editar desde local | a (Q-50) |
| B3 | `.claude/gw.json` (`privateCheck.allowEmails`), `AGENTS.md` y el autor de casi todos los commits | baja | el correo del dueño es público; ya lo era por los commits | aceptar, o pasarlo a `gw.local.json` y usar el correo `noreply` de GitHub en adelante | a (Q-55) |

## C. Huecos de `private-check`

| Id | Dónde | Sev. | Problema | Arreglo propuesto | Decisión |
|---|---|---|---|---|---|
| C1 | `scripts/private-check.py` (sin `gw.local.json`), `tests/check.sh` y el CI (`--no-names`), `scripts/harvest.py:74,498` | alta | en un contenedor en la nube no hay lista local: los nombres no se miran (solo un aviso) y `harvest.py` publica sin anonimizar. Es la causa de A1 y A2 | segunda fuente para la lista: una variable de entorno (`GW_PRIVATE_NAMES`) puesta en el entorno de la nube, nunca en el repo; sin ninguna de las dos, la subida a la rama protegida y la recogida fallan cerradas (`privateCheck.requireNames`) | a (Q-51) |
| C2 | `scripts/private-check.py` | media | no hay detector de enlaces de sesión (`claude.ai/code/session_`), rutas personales (`/Users/<x>`, `/home/<x>`) ni IP privadas | `privateCheck.patterns` con esos tres por defecto y `allowPatterns`; sin teléfonos (demasiados falsos positivos) | a (Q-52) |
| C3 | `templates/githooks/pre-push:427,439` | media | las etiquetas no se revisan: ni los commits que suben con ellas ni su mensaje; tampoco el nombre de la rama | revisar los commits nuevos de una etiqueta, su mensaje y el nombre de la ref | a (Q-52) |
| C4 | `scripts/private-check.py` (`gw-allow-private`) | media | la marca salta todas las comprobaciones de la línea, también en rutas y mensajes de commit; fuera de tests y docs no se usa | sin efecto en rutas ni mensajes; `--all` cuenta las marcas y lo dice | a (Q-53) |
| C5 | `scripts/private-check.py` (correos admitidos) | baja | `git@` y `noreply@` valen con cualquier dominio | `git@` solo con forma SSH `git@host:ruta`; `noreply@` se queda | a (Q-54) |
| C6 | `scripts/private-check.py`, `scripts/doctor.py` | baja | variantes con caracteres invisibles o letras parecidas; binarios sin leer; sin test de merge con conflicto; `privateCheck: false` sin aviso | leves, a `pendingFile` | a (Q-57) |

## Fuera de alcance o sin comprobar

- Lo que GitHub guarda fuera de las ramas: commits inalcanzables, `refs/pull/*`, forks y cachés. Reescribir el
  historial no los borra; solo el soporte de GitHub puede purgarlos.
- Si N5 y N6 son hoy públicos: sin acceso a la API de GitHub desde la nube.
- Un dominio que `0cb929bc` dice haber quitado de las recogidas, sin identificar.
