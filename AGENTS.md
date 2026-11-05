# Galivelop-workflow — instrucciones para agentes

Este repo es la fuente del flujo de trabajo Galivelop-workflow y **se trabaja con su propio flujo**: si algo de
estas reglas estorba aquí, estorba en todos los proyectos que lo usen (plan §4.1). El plan está en
[`docs/plan.md`](docs/plan.md) ([English](docs/plan.en.md)).

Se trabaja por relevos: una sesión puede acabarse en cualquier momento (tokens, contenedor, cambio de cuenta) y la
siguiente tiene que seguir **sin perder nada y sin preguntar por dónde iba**.

Cada regla de abajo que tiene un check lo nombra entre paréntesis; las demás son de criterio.

## Al empezar cualquier sesión

1. Lee [`docs/handoff.md`](docs/handoff.md): rama, fase en curso, pendiente y siguiente paso. Si el gancho
   `SessionStart` ya mostró su estado, lee solo lo que recortó (`… (trimmed …)`).
2. `git fetch origin <rama>` y comprueba que el último commit coincide con lo que dice la bitácora.
3. Comprueba que el check está en verde antes de tocar nada: `bash tests/check.sh`.
4. Sigue por el **siguiente paso** de la bitácora, salvo que el usuario pida otra cosa.
5. Al empezar cada tarea, trae `main` (`git fetch origin main` y `git merge origin/main`; merge, nunca rebase: las
   ramas están subidas).

## Relevos: commit y push constantes

- **Lo que no está subido no existe.** Commit + push en cada punto estable, nunca más de 30-45 minutos sin subir
  (el gancho `Stop`, `before-stop.py`, avisa de lo que queda sin subir).
- **La bitácora se actualiza en el mismo commit** que el trabajo que describe (su formato, `commit-msg`).
- Si hay que parar con algo a medias o en rojo: commit igualmente con `WIP:` al principio y, en la bitácora, qué
  falla y por qué.
- Push con `git push -u origin <rama>`; si falla por red, reintentar con espera 2, 4, 8 y 16 s. El push y el check
  largo van en segundo plano y se espera su aviso, sin bucles de espera.
- Tras una llamada interrumpida o rechazada, `git status` y `git diff` antes de repetirla.
- **Al cerrar cada fase, tarea o PR**, se para y se informa al usuario de qué queda hecho y qué sigue; con la
  bitácora al día, se recomienda `/clear` (la bitácora basta para retomar).
- **La sesión se abre desde la carpeta del repo**; si no, no carga `.claude/settings.json` (`doctor.py` lo detecta).
- **Al cerrar cada bloque o fase, mira el CI de la última subida** (`python3 scripts/ci-status.py`; `ciIgnore`). Un CI
  que no arranca (sin cuota de Actions) cuenta como rojo y se dice al usuario. Solo si él lo confirma vale el check
  pasado en local sobre el mismo commit, apuntado en la bitácora como «comprobado solo en local»; un CI que arrancó y
  falló nunca se sustituye así. Para un PR, `python3 scripts/ci-local.py --record` corre el CI en local y deja la
  línea que acepta el gancho.
- Si el usuario dice que se para, se para: se sube lo que haya y se deja la bitácora al día.

## Comprobar

- **Check del repo:** `bash tests/check.sh` (qué comprueba, en sus `== …`); lo corre el CI en Linux y macOS en
  cada push que no sea a `main` y en cada PR. **Antes de subir, `bash scripts/check.sh`**: lo corre y apunta el
  verde para que el `pre-push` no lo repita (límites en [`docs/es/config.md`](docs/es/config.md)).
- **Un solo archivo de tests:** `python3 -B -m unittest discover -s tests -p 'test_X.py'` (`tests/` no es un
  paquete).
- Los scripts de shell, compatibles con **bash 3.2** (macOS): nada de `mapfile` ni arrays asociativos (el CI en
  macOS).

## Mensajes de commit

Los comprueba el `commit-msg` (`commitFormat`, `commitRefs`, `commitNext` y `agentSignatures` de `.claude/gw.json`).

- En español. Primera línea con Conventional Commits y el id del roadmap como ámbito: `feat(D12): …`; `WIP: `
  delante si va en rojo. Una tarea sin id toma el siguiente libre de su bloque.
- Cuerpo: qué se hizo, qué queda y estado de los tests.
- **Último párrafo, solo trailers:** `Refs: <id>[, <id>]` y, al final, **`Siguiente: <próximo paso concreto>`**.
- Un subagente puede firmar con `Agent: <skill>` (nunca un modelo); sus ramas, `agent/<id>-<tema>`.
- **Sin firmas del agente** (usuario, 2026-10-26): commits, PR y comentarios van a nombre de `Zeldris`, sin
  trailers, pies ni enlaces de sesión de Claude. El autor no lo comprueba ningún gancho: en un contenedor nuevo,
  antes del primer commit, `git config user.name Zeldris` y `git config user.email cordproinf@gmail.com`.

## Ramas y `main`

- Se trabaja en la rama que indique la bitácora.
- **A `main` solo con confirmación del usuario**, y antes las tres fases del flujo:
  1. **Código:** `/code-review` del diff contra `origin/main` (con `git fetch` antes); arreglos subidos con sus tests.
  2. **Entorno:** `/gw-opt-tokens` y `/retro`; sus propuestas se presentan al usuario y lo que confirme se aplica en la
     rama (lo general para el flujo se aplica aquí mismo: este repo es el flujo). Si el usuario pidió ir a `main` y no
     está para decidir la retro: todo listo (retro con `**Estado:** pendiente`, check en verde sobre la fusión con
     `main`, descripción del PR) y se para antes de `reviewed.sh`; no se decide por él.
  3. **Cierre:** si la fase 2 trajo código, `/code-review` de esos commits; luego `bash scripts/reviewed.sh` y la
     subida (el `pre-push` exige la marca).
- `main` = última versión publicada: es lo que instalan otros proyectos (plan §7).
- **Tras la subida a `main`**, se escribe `docs/records/release-vX.Y.Z.md` (como `release-v0.4.0.md`) con el título
  y el cuerpo de la release, cada uno en un bloque listo para pegar, y se dan al usuario sin que los pida (él crea
  la etiqueta y la release a mano).
- **Cada versión empieza con una recogida** (usuario, 2026-10-23): `gw-harvest` sobre los proyectos que usan el
  flujo, y sus propuestas, al usuario (`version.py --release`, en el `pre-push` a `main`, exige su archivo). Al
  cerrarla, otra recogida es opcional (usuario, 2026-11-05).
- **Solo la última menor publicada recibe parches** (usuario, 2026-11-01, plan §7): de una recogida, los arreglos van
  a su siguiente parche y los evolutivos, a la siguiente menor; el reparto, en [`docs/roadmap.md`](docs/roadmap.md).

## Reglas del proyecto

- **Idiomas:** documentación para personas en español e inglés, emparejada (`docs/es/` ↔ `docs/en/`, `README.md` ↔
  `README.es.md`; el check); las `SKILL.md`, solo en inglés; los mensajes de los scripts, en inglés con la orden que
  arregla el fallo.
- **Nombres, siempre en inglés** (usuario, 2026-11-02, A8), también en `docs/es/`; solo el contenido para personas
  va en el idioma del documento (`names-check.py`; un nombre viejo aceptado va en su `EXCEPTIONS`, con el motivo).
- **Otros repos se leen, nunca se modifican** desde aquí (Portal-Galivelop, World-Maker-Fantasy,
  Instalador-WMF-Tarkor, private-project-1): nunca commit, push, edición de archivos ni reescritura del historial en
  ellos; actualizar un clon dedicado y limpio con fetch + fast-forward sí se puede. Se leen con un subagente que
  devuelve un resumen con rutas.
- **Un dato, un sitio:** la versión solo en `.claude-plugin/plugin.json`; el config del proyecto solo lo lee
  `scripts/config.py`.
- **Todo configurable** (usuario, 2026-11-04): cada umbral, ruta o comportamiento nuevo es una clave de
  `.claude/gw.json` con su valor por defecto, leída por `config.py` y explicada en `docs/es/config.md`, para que el
  MMC de la `1.0` (G4) la edite sin tocar código.
- **Ganchos y scripts** (plan §4.3 y §12): raíz desde la ruta del script o `git rev-parse --show-toplevel`, nunca
  desde `$CLAUDE_PROJECT_DIR` ni el directorio actual; un gancho de subida comprueba el commit que se sube; fallan
  cerrados si les falta un dato; cada cambio lleva su caso en los tests, y un caso que espera un fallo comprueba el
  motivo, no solo el código de salida.
- **Mapa para agentes:** [`docs/agent-map.md`](docs/agent-map.md) dice dónde está cada contrato, qué lo implementa
  y qué no leer; los encargos a subagentes apuntan a él en vez de a varios documentos.
- **Reparto a subagentes autorizado:** el trabajo de más de un paso se reparte con la skill `gw-orchestrate-dealer`
  sin preguntar cada vez; la sesión principal planea, decide y revisa.
- **Lo comprobable lo hace un script**, no un agente; las skills y guías solo deciden lo que exige criterio. Este
  archivo tiene tope de líneas (`instructionLines` de `.claude/gw.json`, `doctor.py`).
- **Calidad primero:** un ahorro de tokens que empeora el resultado no es ahorro.
