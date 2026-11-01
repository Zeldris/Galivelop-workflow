# Galivelop-workflow

[English](README.md)

La forma de trabajar del taller Galivelop con agentes de programación (primero Claude Code), sacada de proyectos
reales y generalizada para cualquier repositorio. Es la **fuente única y versionada** de sus skills, ganchos, scripts
y plantillas: una mejora se hace una vez aquí y llega a todos los proyectos que lo usan.

> **Estado: `0.4.2`, etapa 1 en rodaje.** Ya se aplica a proyectos reales con un agente de IA. La serie `0.4` es la
> última antes de la `1.0.0`: desde aquí solo llegan parches `0.4.x`, y lo nuevo va a la `1.0.0`. Ver el
> [plan](docs/plan.md), la [bitácora](docs/traspaso.md) y el [changelog](CHANGELOG.md).

## Qué resuelve

Trabajar con agentes de IA tiene cuatro problemas que se repiten en todos los proyectos:

1. **Las sesiones se acaban.** Por tokens, por el contenedor o por un cambio de cuenta, y la siguiente sesión no sabe
   por dónde iba la anterior.
2. **No siempre se elige bien.** Un modelo caro para una tarea mecánica, o uno barato para una que pide criterio.
3. **Lo que el agente da por bueno no siempre lo está.** Código sin revisar en la rama protegida, tests que pasan
   con el fallo y sin él, un CI que nunca llegó a arrancar.
4. **El gasto de tokens crece sin que nadie lo mida.** El contexto largo es casi todo el coste.

Galivelop-workflow responde a los cuatro con reglas escritas y, sobre todo, con **scripts y ganchos que las hacen
cumplir**.

## Lo que lo hace distinto

### Las reglas las hace cumplir un script, no la buena voluntad del agente

Un agente puede olvidar una regla escrita en un `.md`; un gancho no. Lo comprobable lo comprueba un script, y las
skills y guías quedan solo para lo que exige criterio. Si una regla se sigue rompiendo, se convierte en una
comprobación.

- El `pre-push` corre el check del proyecto **sobre el commit exacto que se sube**, no sobre lo que haya en la
  carpeta.
- Los ganchos **fallan cerrados**: si les falta un dato (sin configuración, sin git), no dejan pasar.
- El gancho `Stop` no deja que el agente acabe con commits sin subir ni con cambios que la bitácora no menciona.

### Relevos de verdad entre sesiones y entre cuentas

- **Lo que no está subido no existe.** Commit + push en cada punto estable, y la bitácora (`docs/traspaso.md`) se
  actualiza **en el mismo commit** que el trabajo que describe, nunca al final.
- Cada commit acaba con `Siguiente: <paso concreto>`: la próxima sesión sabe qué hacer sin preguntar.
- Tras una compactación o un `/clear`, `recuperar.py` devuelve el estado de la bitácora y los últimos commits, y
  busca un detalle perdido en el registro de la sesión sin tener que releerlo entero.
- **Varias sesiones a la vez** (dos cuentas, una local y otra en la nube): cada sesión tiene su propia rama, y con
  `"logRows": true` cada rama escribe solo en su fila de la bitácora; el `pre-push` rechaza tocar la de otra.
  Siempre merge, nunca rebase, porque las ramas están subidas.

### Nada sin revisar llega a la rama protegida

- **Tres fases** antes de subir: revisión del código (`/code-review` del diff contra la rama protegida), entorno
  (`opt-tokens` y `retro`, presentadas a la persona) y cierre.
- `revisado.sh` escribe una **marca de revisión atada a un commit concreto**; sin la marca del mismo commit, los
  ganchos rechazan la subida o el pull request.
- **Código y contenido se distinguen.** Cada proyecto declara con expresiones regulares qué es contenido (docs,
  datos, textos, imágenes) y no necesita revisión de código; lo demás es código y la necesita.
- Un gancho de Claude Code no deja crear ni fusionar un pull request sin la revisión del mismo código, y para
  fusionar exige el CI en verde. **Un CI que no arranca** (sin cuota, sin runners) **cuenta como rojo**.
- A la rama protegida solo se va con la confirmación de la persona.

### Tests que de verdad prueban algo

- `rojo-sin-arreglo.sh` comprueba que un test nuevo **falla sin su arreglo**: un test que pasa en los dos casos no
  prueba nada.
- Un test que espera un fallo comprueba **el motivo**, no solo el código de salida.
- El `pre-push` puede correr también los tests relacionados con lo que cambia.

### El gasto de tokens se mide, no se supone

- `selector` elige al empezar cada tarea la skill y el modelo: el de la sesión lo decide la persona, y el de los
  subagentes es el más barato que haga bien el trabajo.
- `orchestrate-dealer` convierte la sesión principal en orquestadora: reparte el trabajo a subagentes de contexto
  limpio y puede seguir horas sin `/clear`.
- `opt-tokens` mide en el registro de la sesión dónde se fue el gasto y propone cambios del entorno.
- Un gancho pregunta a la persona cuando una sesión ha lanzado muchos subagentes, para que un bucle no gaste sin
  que nadie lo vea.
- **Calidad primero:** un ahorro que empeora el resultado no es ahorro.

### El flujo aprende de los proyectos que lo usan

- Una `retro` que descubre una mejora general no parchea la copia local, que la próxima versión pisaría: la deja en
  su archivo bajo `## Para Galivelop-workflow`.
- Desde este repo, `gw-harvest` (con `recoger.py`) recorre los proyectos conectados y recoge, como propuestas, sus
  copias editadas, sus skills nuevas y lo que dicen sus retros. **Nada se aplica sin confirmación**: lo aprobado
  entra con su entrada en el CHANGELOG y una versión nueva.
- `/gw-update` lleva cada proyecto a la versión nueva y **enseña los cambios de las plantillas** antes de aplicar lo
  que la persona confirme.

### Se protege a sí mismo

- Un gancho pide permiso a la persona antes de que el agente edite la configuración del propio flujo.
- `enlaces-md.py` encuentra enlaces rotos y referencias desfasadas en el Markdown, y `mapa-agente.py` comprueba que
  el mapa para agentes no apunta a nada que ya no exista.
- El propio repo pasa **más de mil pruebas automáticas**, en Linux y macOS, y se trabaja con su propio flujo: si una
  regla estorba aquí, estorba en todos los proyectos.

## Cómo es una tarea

1. **Al empezar:** la sesión lee la bitácora, trae la rama protegida (merge, nunca rebase) y comprueba que el check
   está en verde antes de tocar nada.
2. **Antes de trabajar:** `selector` dice en una línea qué skill y qué modelo pide el caso.
3. **Mientras trabaja:** commit + push en cada punto estable, nunca más de 30-45 minutos sin subir, con la bitácora
   en el mismo commit. Lo de varios pasos va a subagentes con `orchestrate-dealer`.
4. **Antes de la rama protegida:** las tres fases, la marca con `revisado.sh` y la subida con la confirmación de la
   persona.
5. **Al cerrar una fase:** se mira el CI de la última subida y, con la bitácora al día, se recomienda `/clear`.

## Qué incluye

### Skills

24 skills en formato abierto [Agent Skills](https://github.com/agentskills/agentskills).

**Propias del flujo (11):**

| Skill | Para qué |
|---|---|
| `selector` | Elegir skill y modelos al empezar cada tarea |
| `orchestrate-dealer` | Repartir el trabajo a subagentes de contexto limpio y trabajar horas sin `/clear` |
| `opt-tokens` | Medir dónde se fue el gasto de una sesión y proponer cómo bajarlo sin empeorar el resultado |
| `opt-ai` | Opcional: medir latencia, calidad y configuración de modelos de IA locales (Ollama, llama.cpp, vLLM…) por máquina |
| `scout-updates` | Opcional: buscar actualizaciones de dependencias, imágenes, acciones de CI y modelos en fuentes primarias, solo como propuesta |
| `gw-init` | Aplicar el flujo a un proyecto nuevo o existente |
| `gw-update` | Llevar un proyecto a la versión nueva, enseñando antes los cambios |
| `gw-doctor` | Comprobar que está bien montado y explicar cada fallo con su arreglo |
| `gw-harvest` | Recoger como propuestas lo que los proyectos cambiaron o inventaron |
| `gw-media-content` | Proponer publicaciones para las redes del proyecto |
| `gw-media-content-now` | Preparar una publicación concreta, con textos por canal e imágenes |

**De [Matt Pocock](https://github.com/mattpocock) (13):** `codebase-design`, `diagnosing-bugs`, `domain-modeling`,
`grill-with-docs`, `grilling`, `improve-codebase-architecture`, `pr`, `prototype`, `research`, `retro`,
`to-questionnaire`, `wait-what` y `writing-for-agents` (ver [Agradecimientos](#agradecimientos)).

### Ganchos

- **De git:** `pre-commit` (busca secretos: archivos `.env` o `.pem` y patrones de claves conocidas), `commit-msg`
  (comprueba el mensaje) y `pre-push` (check sobre el commit que se sube, marca de revisión y reglas de la bitácora).
- **De Claude Code:** recuperar el estado al empezar, no acabar sin subir, revisión antes de un pull request, aviso
  por exceso de subagentes y guardia de la configuración.

### Scripts

Deterministas, en Python y en bash compatible con la versión de macOS: `aplicar.py` (montar el flujo), `doctor.py`
(diagnóstico con la orden que arregla cada problema), `revisado.sh` (marca de revisión), `recuperar.py` (estado
tras `/clear`), `fusionar.sh` (traer la rama de un subagente con el check en verde y limpiar su copia de trabajo),
`rojo-sin-arreglo.sh`, `recoger.py` y las comprobaciones de enlaces y del mapa para agentes.

### Patrones opcionales

Para casos que no todos los proyectos tienen ([patrones](docs/es/patrones.md)): una **tarea semanal programada** que
actualiza y publica sola, **dos cuentas que se relevan**, una **sesión local que no puede crear PR** y se lo deja a
la de la nube, **contenido para redes** y la **recogida de mejoras** de vuelta al flujo.

## Cómo se aplica

- **Etapa 1 (hoy):** un agente de IA aplica el flujo a tu proyecto, nuevo (lo recomendado) o existente, siguiendo
  la [guía de aplicación](docs/es/aplicar.md). Lo que exige criterio (idioma, check, rama protegida, qué es
  contenido…) lo decide contigo; `scripts/aplicar.py` copia y configura, y `scripts/doctor.py` confirma que queda
  bien montado. En Claude Code, `/gw-init` lo aplica, `/gw-update` lo pone al día y `/gw-doctor` lo revisa.
- Todo queda **en el repo del proyecto** (`.claude/gw/`, `.claude/skills/`, `.githooks/` y `.claude/gw.json`), así
  que funciona también en sesiones en la nube, que no cargan plugins.
- Lo propio de cada proyecto va en un solo archivo, `.claude/gw.json` ([configuración](docs/es/config.md)).
- Requisitos: `git`, `bash` y `python3` 3.8 o superior (en Windows, Git Bash o WSL).
- **Etapa 2 (más adelante):** instalación automática sin IA, para proyectos nuevos y existentes.

Las reglas del flujo viven en `AGENTS.md`, un estándar abierto que lee cualquier agente; `CLAUDE.md` lo importa y
añade lo propio de Claude Code.

## Documentación

- [Visión general del flujo](docs/es/flujo.md)
- [Aplicarlo a un proyecto](docs/es/aplicar.md) · [Configuración](docs/es/config.md) · [Patrones](docs/es/patrones.md)
- [Problemas conocidos](docs/es/problemas.md) · [Cambiar el flujo](docs/es/contribuir.md)
- [Plan](docs/plan.md) · [Mapa para agentes](docs/mapa-agente.md) · [Changelog](CHANGELOG.md)

## Agradecimientos

Aprendimos a trabajar así gracias al trabajo de **[Matt Pocock](https://github.com/mattpocock)**, sobre todo su
[mattpocock/skills](https://github.com/mattpocock/skills): la idea de guiar a los agentes con skills pequeñas y bien
escritas, el ciclo de revisión y retro, y muchas de las skills que se incluyen aquí, que son suyas (MIT), con su
mención en cada una y en [`CREDITS.md`](CREDITS.md). Gracias, Matt.

## Licencia

[MIT](LICENSE). Las skills de [mattpocock/skills](https://github.com/mattpocock/skills) conservan su licencia MIT
([`LICENSE-mattpocock-skills`](LICENSE-mattpocock-skills)); ver [`CREDITS.md`](CREDITS.md).
