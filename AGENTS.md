# Galivelop-workflow — instrucciones para agentes

Este repo es la fuente del flujo de trabajo Galivelop-workflow y **se trabaja con su propio flujo**: si algo de
estas reglas estorba aquí, estorba en todos los proyectos que lo usen (plan §4.1). El plan está en
[`docs/plan.md`](docs/plan.md) ([English](docs/plan.en.md)); la investigación, en `docs/investigacion/`.

Se trabaja por relevos: una sesión puede acabarse en cualquier momento (tokens, contenedor, cambio de cuenta) y la
siguiente tiene que seguir **sin perder nada y sin preguntar por dónde iba**.

## Al empezar cualquier sesión

1. Lee [`docs/traspaso.md`](docs/traspaso.md): rama, fase en curso, pendiente y siguiente paso.
2. `git fetch origin <rama>` y comprueba que el último commit coincide con lo que dice la bitácora.
3. Si la bitácora dice que hay tests, comprueba que están como dice antes de tocar nada.
4. Sigue por el **siguiente paso** de la bitácora, salvo que el usuario pida otra cosa.
5. Al empezar cada tarea, trae `main` si existe (`git fetch origin main` y `git merge origin/main`; merge, nunca
   rebase: las ramas están subidas).

## Relevos: commit y push constantes

- **Lo que no está subido no existe.** Commit + push en cada punto estable, nunca más de 30-45 minutos sin subir.
- **La bitácora se actualiza en el mismo commit** que el trabajo que describe.
- Si hay que parar con algo a medias o en rojo: commit igualmente con `WIP:` al principio y, en la bitácora, qué
  falla y por qué.
- Push a la rama de trabajo (`git push -u origin <rama>`); si falla por red, reintentar con espera 2, 4, 8 y 16 s.
- Tras una llamada interrumpida o rechazada, `git status` y `git diff` antes de repetirla.
- **Al cerrar cada fase**, se para y se informa al usuario de qué queda hecho y cuál es la siguiente.
- Si el usuario dice que se para, se para: se sube lo que haya y se deja la bitácora al día.

## Mensajes de commit

- En español. Primera línea: qué cambia (con la fase, p. ej. `Fase 1: …`).
- Cuerpo: qué se hizo, qué queda y estado de los tests.
- **Última línea: `Siguiente: <próximo paso concreto>`**, en el mismo bloque final que las líneas de atribución.

## Ramas y `main`

- Se trabaja en la rama que indique la bitácora (hoy `claude/galivelop-workflow-inicio`).
- **A `main` solo con confirmación del usuario**, y antes `/code-review` del diff contra `origin/main`.
- Este repo, una vez publicado, es lo que instalan otros proyectos: `main` = última versión publicada (plan §7).

## Reglas del proyecto

- **Idiomas:** documentación para personas en español e inglés, emparejada (`docs/es/` ↔ `docs/en/`, `README.md` ↔
  `README.es.md`); las `SKILL.md`, solo en inglés; los mensajes de los scripts, en inglés con la orden que arregla
  el fallo.
- **Otros repos se leen, nunca se modifican** desde aquí (Portal-Galivelop, World-Maker-Fantasy,
  Instalador-WMF-Tarkor). Se leen con un subagente que devuelve un resumen con rutas.
- **Un dato, un sitio:** la versión solo en `.claude-plugin/plugin.json`; el config del proyecto solo lo lee
  `scripts/config.py`.
- **Ganchos y scripts** (plan §4.3 y §12): raíz desde la ruta del script o `git rev-parse --show-toplevel`, nunca
  desde `$CLAUDE_PROJECT_DIR` ni el directorio actual; un gancho de subida comprueba el commit que se sube; fallan
  cerrados si les falta un dato; cada cambio lleva su caso en los tests.
- **Lo comprobable lo hace un script**, no un agente; las skills y guías solo deciden lo que exige criterio.
- **Calidad primero:** un ahorro de tokens que empeora el resultado no es ahorro.
