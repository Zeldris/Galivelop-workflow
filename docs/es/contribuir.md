# Cambiar el flujo

> [English](../en/contributing.md)

Cómo se modifica Galivelop-workflow. Este repo **se trabaja con su propio flujo**: si una regla estorba aquí,
estorba en todos los proyectos. Lee primero [`AGENTS.md`](../../AGENTS.md) y la bitácora
([`docs/traspaso.md`](../traspaso.md)); el plan está en [`docs/plan.md`](../plan.md).

## El ciclo de un cambio

1. **Parte de la rama de trabajo** que diga la bitácora, con `main` traído (`git fetch origin main` y
   `git merge origin/main`).
2. **Edita las fuentes**: `scripts/`, `skills/`, `templates/`, `schema/`, `docs/`. Nunca edites a mano la copia
   aplicada (`.claude/gw/`, `.claude/skills/`, `.githooks/`, `.claude/settings.json`): se genera.
3. **Refresca la copia de este repo**:

   ```bash
   python3 scripts/aplicar.py .
   python3 scripts/aplicar.py --check .      # debe salir con 0
   ```

   Sin esto, `tests/comprobar.sh` falla («workflow copy in sync»): la copia tiene que ser idéntica a las fuentes.
4. **Añade el caso de prueba** (abajo) y corre el check:

   ```bash
   bash scripts/check.sh      # corre bash tests/comprobar.sh y apunta el verde: el pre-push no lo repite
   ```

5. **Entrada en el CHANGELOG**, **bitácora**, commit y push, en el mismo commit (abajo).

## Pruebas por cada cambio

- **Cada cambio de un gancho o script lleva su caso en los tests** (`tests/test_*.py`, que crean un repo git
  temporal): `test_ganchos.py`, `test_revision_main.py`, `test_doctor.py`, `test_aplicar.py`… Un cambio nuevo en
  `doctor.py` es un caso nuevo en `test_doctor.py`.
- **Una prueba nueva debe fallar sin su arreglo.** Compruébalo con el arreglo aún sin commitear:

  ```bash
  bash scripts/rojo-sin-arreglo.sh "python3 -m unittest tests.test_doctor.Clase.test_caso" scripts/doctor.py
  ```

  Opciones: `--fails-with REGEX` (el fallo sin el arreglo debe imprimir REGEX, para que no falle por otro motivo) y
  `--ran-one REGEX` (la ejecución con el arreglo debe imprimir exactamente una línea que case con REGEX, la que tu
  ejecutor saca por cada test, p. ej. `'^ok '`: si el filtro no casa con nada o ejecuta más de un test, falla).

- Una **skill** nueva o cambiada pasa `tests/test_skills.py` (nombre = carpeta, `description` de 1 a 1024 caracteres,
  `license`, `compatibility`, `metadata.version`, menos de 200 líneas). Se escribe en **inglés** y aplicando la skill
  `writing-for-agents`.
- **Plantillas:** `tests/test_plantillas.py` aplica el flujo a un repo vacío y comprueba lo esperado y que repetirlo
  no cambia nada.
- **bash 3.2** (macOS): nada de `mapfile` ni arrays asociativos. El CI corre en Linux y macOS.

## Reglas del repo (resumen de `AGENTS.md`)

- **Ganchos y scripts:** la raíz se saca de la ruta del script o de `git rev-parse --show-toplevel`, nunca de
  `$CLAUDE_PROJECT_DIR` ni del directorio actual; un gancho de subida comprueba **el commit que se sube**; fallan
  **cerrados** si les falta un dato; cada mensaje, en inglés y con la orden que arregla el fallo.
- **Un dato, un sitio:** la versión solo en `.claude-plugin/plugin.json`; el config del proyecto solo lo lee
  `scripts/config.py`.
- **Idiomas:** documentación para personas en español e inglés **emparejada** (`docs/es/` ↔ `docs/en/`, `README.md` ↔
  `README.es.md`, con el enlace al par en las primeras líneas); `SKILL.md` solo en inglés.
- **Lo comprobable lo hace un script**, no un agente; las skills y guías solo deciden lo que exige criterio.
- **Otros repos se leen, nunca se modifican** desde aquí; se leen con un subagente que devuelve un resumen con rutas.
- **Calidad primero:** un ahorro de tokens que empeora el resultado no es ahorro.

## Versión y CHANGELOG

La versión sigue [SemVer](https://semver.org/lang/es/) y vive **solo** en `.claude-plugin/plugin.json`:

| Cambio | Sube |
|---|---|
| El config o una plantilla cambian de forma que obliga a tocar los proyectos que ya lo usan | **mayor** |
| Skill o gancho nuevos, o una mejora compatible | **menor** |
| Arreglos | **parche** |

La `0.4` es la última menor `0.x` (plan §7): una recogida manda las correcciones a un parche `0.4.x` y apunta los evolutivos para la `1.0.0` y siguientes.

Cada versión tiene una entrada en [`CHANGELOG.md`](../../CHANGELOG.md) con `### ES` y `### EN`, ambas con el mismo
contenido; el check falla si la versión de `plugin.json` no tiene entrada. Al subir la versión, el `metadata.version` de
**todas** las skills (lo exige `test_skills.py`) y las cabeceras `# galivelop-workflow vX.Y.Z` de scripts y plantillas se mueven con
ella, y los proyectos la recogen con `/gw-update`. No se tocan a mano: `python3 scripts/version.py X.Y.Z` los mueve
todos y deja la entrada del CHANGELOG por rellenar; sin argumento, comprueba que ninguno se ha quedado atrás.

**Todo cambio en un archivo copiable** (`scripts/`, `skills/`, `templates/`, `schema/`) entre dos publicaciones **sube
la versión**, aunque sea un parche: un proyecto que copió entre las dos vería «ediciones locales» que no hizo.
`python3 scripts/version.py --release` lo comprueba contra la última etiqueta `vX.Y.Z` alcanzable desde el commit
(necesita las etiquetas: `git fetch --tags origin`), y el `check` de este repo lo corre en cada subida a `main`
(`GW_PUSH_PROTECTED`).

**Publicar una versión:** en `main` (con las tres fases hechas), la entrada del CHANGELOG con fecha en vez de
«Unreleased», y la etiqueta: `git tag vX.Y.Z && git push origin vX.Y.Z`. El workflow `release.yml` comprueba que la
etiqueta, `plugin.json` y los marcadores coinciden y que la versión subió, pasa el check y crea la release con esa entrada.

## Commit, bitácora y `main`

- **Commit y push en cada punto estable**, nunca más de 30-45 minutos sin subir; **la bitácora en el mismo commit**.
- Mensaje en español; primera línea con la fase (`Fase 4: …`); cuerpo con qué se hizo, qué queda y estado de los
  tests; **última línea `Siguiente: <próximo paso concreto>`**, en el mismo bloque final que la atribución.
- Si hay que parar con algo en rojo: commit con `WIP:` al principio y, en la bitácora, qué falla y por qué.
- **A `main` solo con confirmación de la persona**, y antes `/code-review` del diff contra `origin/main`. `main` es la
  última versión publicada, la que instalan otros proyectos.
- **Al cerrar cada fase** se para y se informa de qué queda hecho y cuál es la siguiente.

## Propuestas de los proyectos

Las mejoras que llegan de los proyectos entran por `gw-harvest` ([patrones](patrones.md#recoger-mejoras-de-vuelta)):
cada una es un archivo en `docs/propuestas/` que la persona aprueba; la aprobada se hace con este mismo ciclo.
