# Galivelop-workflow — instrucciones para agentes

Este repo es la fuente del flujo de trabajo Galivelop-workflow y **se trabaja con su propio flujo**: si algo de
estas reglas estorba aquí, estorba en todos los proyectos que lo usen (plan §4.1). El plan está en
[`docs/plan.md`](docs/plan.md) ([English](docs/plan.en.md)); la investigación, en `docs/investigacion/`.

Se trabaja por relevos: una sesión puede acabarse en cualquier momento (tokens, contenedor, cambio de cuenta) y la
siguiente tiene que seguir **sin perder nada y sin preguntar por dónde iba**.

## Al empezar cualquier sesión

1. Lee [`docs/traspaso.md`](docs/traspaso.md): rama, fase en curso, pendiente y siguiente paso. Si el gancho
   `SessionStart` ya mostró su estado, lee solo lo que recortó (`… (trimmed …)`).
2. `git fetch origin <rama>` y comprueba que el último commit coincide con lo que dice la bitácora.
3. Comprueba que el check está en verde antes de tocar nada: `bash tests/comprobar.sh`.
4. Sigue por el **siguiente paso** de la bitácora, salvo que el usuario pida otra cosa.
5. Al empezar cada tarea, trae `main` si existe (`git fetch origin main` y `git merge origin/main`; merge, nunca
   rebase: las ramas están subidas).

## Relevos: commit y push constantes

- **Lo que no está subido no existe.** Commit + push en cada punto estable, nunca más de 30-45 minutos sin subir.
- **La bitácora se actualiza en el mismo commit** que el trabajo que describe.
- Si hay que parar con algo a medias o en rojo: commit igualmente con `WIP:` al principio y, en la bitácora, qué
  falla y por qué.
- Push a la rama de trabajo (`git push -u origin <rama>`); si falla por red, reintentar con espera 2, 4, 8 y 16 s.
  El push y el check largo se lanzan en segundo plano y se espera su aviso, sin bucles de espera.
- Tras una llamada interrumpida o rechazada, `git status` y `git diff` antes de repetirla.
- **Al cerrar cada fase**, se para y se informa al usuario de qué queda hecho y cuál es la siguiente; con la bitácora
  al día, se recomienda `/clear` antes de la siguiente (la bitácora basta para retomar). Igual al cerrar cada tarea o PR.
- **La sesión se abre desde la carpeta del repo** (`cd Galivelop-workflow && claude`): abierta en otra no carga
  `.claude/settings.json` (ni la compactación a 200k ni los ganchos); `python3 scripts/doctor.py` lo detecta. En la
  nube, que arranca en `/home/user`, la compactación va en las variables del entorno (`doctor.py` avisa si falta).
- **Al cerrar cada bloque o fase, mira el CI de la última subida.** Un CI que no arranca (por ejemplo, sin cuota de
  Actions) cuenta como rojo: se dice al usuario y no se da nada por comprobado en el CI. Entonces vale el check
  pasado en local sobre el mismo commit (`bash tests/comprobar.sh`, o el del `pre-push`) **solo si el usuario lo
  confirma**, y se dice y se apunta en la bitácora como «comprobado solo en local». Un CI que arrancó y falló nunca
  se sustituye así.
- Si el usuario dice que se para, se para: se sube lo que haya y se deja la bitácora al día.

## Comprobar

- **Check del repo:** `bash tests/comprobar.sh` (sintaxis y shellcheck de scripts, Python, JSON, manifiestos,
  versión con entrada en el CHANGELOG, pares ES/EN). Lo corre el CI (`.github/workflows/comprobar.yml`, Linux y
  macOS) en cada push que no sea a `main` y en cada PR.
- **Un solo archivo de tests:** `python3 -B -m unittest discover -s tests -p 'test_X.py'` (`-m unittest tests.test_X`
  falla: `tests/` no es un paquete).
- Los scripts de shell, compatibles con **bash 3.2** (macOS): nada de `mapfile` ni arrays asociativos.

## Mensajes de commit

- En español. Primera línea: qué cambia (con la fase, p. ej. `Fase 1: …`).
- Cuerpo: qué se hizo, qué queda y estado de los tests.
- **Última línea: `Siguiente: <próximo paso concreto>`**.
- **Sin firmas del agente** (usuario, 2026-10-26): commits y PR van a nombre del usuario de git (`Zeldris`), nunca
  como Claude; ni `Co-Authored-By`, ni `Claude-Session`, ni «Generated with Claude Code» ni enlaces de sesión, en
  ningún sitio (mensajes, PR, comentarios, archivos). En un contenedor nuevo, antes del primer commit:
  `git config user.name Zeldris` y `git config user.email cordproinf@gmail.com`.

## Ramas y `main`

- Se trabaja en la rama que indique la bitácora.
- **A `main` solo con confirmación del usuario**, y antes las tres fases del flujo:
  1. **Código:** `/code-review` del diff contra `origin/main` (con `git fetch` antes); arreglos subidos con sus tests.
  2. **Entorno:** `/opt-tokens` y `/retro`; sus propuestas se presentan al usuario y lo que confirme se aplica en la
     rama (lo general para el flujo se aplica aquí mismo: este repo es el flujo). Si el usuario pidió ir a `main` y no
     está para decidir la retro: todo listo (retro con `**Estado:** pendiente`, check en verde sobre la fusión con
     `main`, descripción del PR) y se para antes de `revisado.sh`; no se decide por él.
  3. **Cierre:** si la fase 2 trajo código, `/code-review` de esos commits; luego `bash scripts/revisado.sh` y la
     subida (el `pre-push` exige la marca).
- Este repo, una vez publicado, es lo que instalan otros proyectos: `main` = última versión publicada (plan §7).
- **Tras la subida a `main`**, se escribe `docs/registros/release-vX.Y.Z.md` (como `release-v0.4.0.md`): el título y
  el cuerpo de la release, cada uno en un bloque listo para pegar, y se dan al usuario sin que los pida (él crea la
  etiqueta y la release a mano).
- **Cada versión empieza con una recogida** (usuario, 2026-10-23): al abrir una versión nueva, `gw-harvest` sobre los
  proyectos que usan el flujo, y sus propuestas se presentan al usuario. `python3 scripts/version.py --release` (lo
  corre el `pre-push` de una subida a `main`) exige un `docs/propuestas/*.md` que empiece por `# Harvest` añadido
  desde la última etiqueta `vX.Y.Z`; una recogida sin nada nuevo también deja su archivo.
- **La `0.4` solo recibe correcciones** (usuario, 2026-10-25, plan §7): de una recogida, los arreglos van a un parche
  `0.4.x` y los evolutivos se apuntan para la `1.0.0` (nunca una `0.5`).

## Reglas del proyecto

- **Idiomas:** documentación para personas en español e inglés, emparejada (`docs/es/` ↔ `docs/en/`, `README.md` ↔
  `README.es.md`); las `SKILL.md`, solo en inglés; los mensajes de los scripts, en inglés con la orden que arregla
  el fallo.
- **Otros repos se leen, nunca se modifican** desde aquí (Portal-Galivelop, World-Maker-Fantasy,
  Instalador-WMF-Tarkor, VeriNews_AI): nunca commit, push, edición de archivos ni reescritura del historial en ellos;
  actualizar un clon dedicado y limpio con fetch + fast-forward sí se puede (es como se ve su último estado). Se leen
  con un subagente que devuelve un resumen con rutas.
- **Un dato, un sitio:** la versión solo en `.claude-plugin/plugin.json`; el config del proyecto solo lo lee
  `scripts/config.py`.
- **Ganchos y scripts** (plan §4.3 y §12): raíz desde la ruta del script o `git rev-parse --show-toplevel`, nunca
  desde `$CLAUDE_PROJECT_DIR` ni el directorio actual; un gancho de subida comprueba el commit que se sube; fallan
  cerrados si les falta un dato; cada cambio lleva su caso en los tests, y un caso que espera un fallo comprueba el
  motivo, no solo el código de salida.
- **Mapa para agentes:** [`docs/mapa-agente.md`](docs/mapa-agente.md) dice dónde está cada contrato y qué lo
  implementa; los encargos a subagentes apuntan a él en vez de a varios documentos.
- **Reparto a subagentes autorizado:** el trabajo de más de un paso se reparte a subagentes con la skill
  `orchestrate-dealer` sin preguntar cada vez; la sesión principal planea, decide y revisa.
- **Lo comprobable lo hace un script**, no un agente; las skills y guías solo deciden lo que exige criterio.
- **Calidad primero:** un ahorro de tokens que empeora el resultado no es ahorro.
