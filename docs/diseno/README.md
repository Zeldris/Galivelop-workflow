# Sesión de diseño de la `1.0.0` (abierta el 2026-10-30)

Lo que el usuario pidió entre el 2026-10-30 y el 2026-11-01, **apuntado antes de diseñar nada**. Cada bloque se
diseña por separado (uno a uno, o juntos los que dependen entre sí) y, cerrado, deja su archivo en esta carpeta
(`<bloque>-<tema>.md`) con lo decidido. Al acabar todos: el roadmap y el mapa de versiones (bloque H).

Regla de la sesión (usuario, 2026-11-01): **se cierra el diseño de todo esto antes de empezar ningún desarrollo.**
Lo que esté aquí sin su archivo de bloque sigue en bruto, no decidido.

## Orden propuesto

| # | Bloque | Por qué en este orden | Estado |
|---|---|---|---|
| 1 | **A. Marco:** público, nombres, versionado | Fija el marco en el que se decide todo lo demás | borrador: [`A-marco.md`](A-marco.md) |
| 2 | **F. Referencias a revisar** | Investigación que se lanza ya (subagentes) y alimenta B, D y G | notas hechas (2026-11-01): `docs/investigacion/ref-*.md`; falta repasarlas con el usuario |
| 3 | **D. Git:** entornos, releases, tags, trazabilidad, roles | Estructura: decide dónde vive y cómo se enlaza lo que se apunta | pendiente |
| 4 | **B. Medición de gasto y modelos** | El bloque funcional mayor; usa D (dónde se guarda, cómo se etiqueta) | pendiente |
| 5 | **C. Preguntas y modo restrictivo** | Pequeño y cerrado; comparte «modos» con B6 | pendiente |
| 6 | **E. Reglas deterministas, pruebas de front, documentación** | Limpieza y calidad; usa A (público) y D (dónde) | pendiente |
| 7 | **G. Management Center (MMC)** | Consume todo lo anterior; el final del roadmap | pendiente |
| 8 | **H. Roadmap y mapa de versiones** | Reparte lo diseñado en versiones `1.0.0+` | pendiente |

## A. Marco (decisiones ya tomadas por el usuario; se apuntan, no se discuten)

- **Todo público** (2026-10-30/31): los repos del usuario, este incluido, son públicos. La versión privada
  desaparece: la `1.0.0` se trata como producto, pero público. Lo que importa es la implementación, la mejora y la
  difusión, no la monetización: usarlo bien exige perfil técnico, aún más cuando esté todo configurable desde el MMC.
  Impacto: el plan (§1, §2, §7, §10) habla de repo privado, `1.0.0` solo como plugin y versiones siguientes privadas;
  hay que revisarlo. Revisar toda la documentación: sin «basura», sin nada privado o complejo de más, y ajustada a lo
  que hay hoy.
- **README:** el usuario le dio una pasada (en `main`, `91fdddb`..`c470a57`); hay que dejarlo correcto y al día.
- **Nombres:** todo archivo o skill del flujo pasa a empezar por `gw-` y, por convención, todo en inglés, como las
  skills.
- **Versionado de todo:** un sistema de versiones para que todo lo que salga del flujo quede versionado. El diseño de
  esta sesión se reparte en versiones `1.0.0+`; las mejoras que no son evolutivos pero forman parte del flujo de la
  `0.4` también se reparten en versiones.

## B. Medición de gasto y modelos

- **B1. Escuchador de costes:** algo que esté todo el rato acumulando los totales de coste por modelo y guardándolos
  (memoria/estado), para que las skills de informe sirvan lo guardado sin recalcular.
- **B2. Skills de informe por periodo:** uso por modelo diario, semanal, mensual y trimestral; guardan el informe en
  `docs/mediciones/` con carpetas `daily/`, `weekly/`, `monthly/`, `quarterly/`.
- **B3. Skills de comparación:** del mismo tipo que el informe (diaria, semanal…), dicen las diferencias de gasto
  entre modelos: hoy frente a ayer, esta semana frente a la anterior… Y otras que permiten elegir dos días, dos
  semanas, dos meses… y compararlos.
- **B4. Aviso y desactivación de modelos:** cuando un modelo se sale de la media acumulada, se avisa al usuario
  («X está gastando más de lo normal»); una skill activa o desactiva cualquier modelo, para sacarlo de la ecuación
  en el resto del desarrollo y volver a meterlo después.
- **B5. Tabla determinista de modelos por necesidad:** se dejan las interpretaciones sobre qué modelo usar y de
  dejar que el agente decida. Con las estadísticas de los informes, una tabla determinista con cifras reales
  (consumo y resultado) que diga qué modelo conviene para cada cosa. Mapa inicial del usuario, a contrastar con lo
  que dicen los expertos (ver el apéndice).
- **B6. El `selector` recomienda también el orquestador:** solo recomienda, el modelo y el esfuerzo del agente
  principal de la sesión (una ronda de pruebas ya documentada o un desarrollo claro no necesitan modelo grande ni
  esfuerzo alto). **Modo restringido de tokens:** activo, siempre se recomiendan los cambios de orquestador; inactivo,
  al usuario no le importa gastar de más.
- **B7. Palancas de Claude Code:** `CLAUDE_CODE_SUBAGENT_EFFORT=low` (los subagentes ya no corren a esfuerzo
  máximo en tareas pequeñas) y `CLAUDE_CODE_SUBAGENT_MODEL` (todos los subagentes a un modelo más barato) se
  apilan; tenerlas en cuenta en el flujo. Y el patrón «scouts»: muchos Haiku en paralelo leen, buscan y resumen
  (0,10/0,50 $ por millón), Opus solo ve lo que los scouts señalan (4/20 $), cada afirmación se comprueba contra la
  fuente antes de seguir y no se escribe nada hasta que pasa (una búsqueda de 20k/1k: 0,0025 $ en Haiku, 0,10 $ en
  Opus, 40×). Va en la línea de `orchestrate-dealer`.
- **B8. Marketing, ahorro medido:** con las mediciones que ya hay se sabe la media de gasto por tarea; medir qué
  porcentaje de tokens ahorra usar el flujo frente a no usarlo, para la cantidad de tareas realizadas.

## C. Preguntas y modo restrictivo

- Pasa que se lanza una pregunta, los agentes siguen a lo suyo, la respuesta no se concreta y las preguntas se
  acumulan y se pintan una y otra vez en cada iteración.
- **Modo restrictivo** (el usuario lo cambia desde una skill): activo, con preguntas abiertas no se continúa el
  desarrollo hasta responderlas; inactivo, las preguntas se acumulan, pero en vez de repetirlas queda un aviso
  («Hay X preguntas por responder antes de implementar nada»). Al tocar implementar con preguntas sin contestar, se
  recomienda responderlas; si el usuario decide seguir, aprueba los riesgos que puedan presentarse (un warning).
- **Concepto del flujo** (nunca se impone, se guía o recomienda): resolver todas las dudas antes de desarrollar.
  «No puedo hacer un puzzle si no tengo todas las piezas»: sería imposible acabarlo.

## D. Git: entornos, releases, tags, trazabilidad, roles

- **Trabajar por entornos:** hoy es `main` y una rama un nivel por debajo. Estructurarlo bien: releases controladas
  y versionadas, y la posibilidad de entornos (`dev`, `uat`, `prod`…).
- **Tags en commits:** relacionar tareas con tickets y con el objetivo (fix, evo…). Niveles bien controlados, cada
  parte con su significado. Hay que pensarlo bien.
- **Trazabilidad entre todo:** un método de tags que viva en todos los niveles y relacione doc, bitácoras, commits,
  PR… todos los elementos, para que un implicado nunca se pierda entre el ruido. Vivimos de lo que apuntamos, y lo
  apuntado tiene que estar estructurado: su localización para leerlo y para actualizarlo siempre clara y accesible.
- **Roles** (pensado para el MMC, bloque G): un rol DEV trabaja sobre `dev`, QA sobre `uat`, ADMIN hace todo; las
  cuentas de GitHub se incluyen en la configuración del flujo y viven bajo un rol, y cada entorno tiene su uso
  dedicado al rol de cada cuenta.
- **Worktrees:** revisar <https://code.claude.com/docs/en/worktrees> (lo que Claude Code trae ya frente a lo que
  hace el flujo).

## E. Reglas deterministas, pruebas de front, documentación

- **`CLAUDE.md` y `AGENTS.md` limpios:** sin un bucle de reglas infinito o tan largo que sea imposible cumplirlo.
  Ya se aplica; el principio: todo lo que se pueda controlar de forma determinista sale del razonamiento del modelo
  y vive en un check, como las reglas.
- **Pruebas de front con la fiabilidad de las de back:** hoy todo depende de Playwright. Buscar más herramientas que
  cubran la arquitectura de estilos, el responsive, el adaptative, las animaciones y transiciones. Lo que esté
  escrito o identificado como norma queda registrado y aplicado como regla.
- **Documentación:** revisión completa (ver A: pública, sin basura, coherente con lo que hay).

## F. Referencias a revisar

Cada una se lee con un subagente que devuelve qué aporta al flujo (y a qué bloque); sus notas, en
`docs/investigacion/`.

| Qué | Para qué | Bloque |
|---|---|---|
| [GitHub agentic workflows](https://github.blog/ai-and-ml/automate-repository-tasks-with-github-agentic-workflows/) | Sacar ideas para la parte de GitHub y de Actions | D, G |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | Revisar | B, G |
| [opencode](https://github.com/anomalyco/opencode) | Asegurar que el flujo encaja con su estructura; abrirle la puerta | A, E |
| [openai/codex](https://github.com/openai/codex) | Abrirle la puerta; sacar cosas para el flujo | A, E |
| [JetBrains thinkrail](https://github.com/JetBrains/thinkrail) | Parece algo similar al flujo: comparar | todos |
| [Aider](https://github.com/Aider-AI/aider) | La parte de commits y diff | D |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Revisar | D, G |
| [Claude Code worktrees](https://code.claude.com/docs/en/worktrees) | Revisar | D |
| [garrytan/gstack](https://github.com/garrytan/gstack) | 23 herramientas con roles (CEO, diseñador, release manager…) | B5, G |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | Revisar | todos |
| Tuits (capturas del usuario) | `CLAUDE_CODE_SUBAGENT_EFFORT`/`_MODEL`; patrón scouts Haiku + Opus | B7 |

## G. Management Center (MMC): el final del roadmap

Una vista simple para el flujo, tipo CRM: un panel de control del flujo y del proyecto sobre el que trabaja. Hay
que pensarlo mucho y diseñarlo lo mejor posible.

- **Configuración:** todo lo configurable vive en el MMC (activar, desactivar, editar, añadir…): restricciones y
  modos (C, B6), modelos activos (B4), roles y cuentas (D). **Perfiles:** uno global (el que viene del repo del
  flujo) y uno privado (el del repo donde está), alternables; y perfiles guardados con configuraciones distintas
  para cada situación.
- **Datos:** toda la información que genera el flujo: tasa de consumo de tokens, mediciones de `opt-tokens` por PR,
  gasto diario total y por agente o subagente, informes generados (B2, B3), retros… Todos los casos de los datos que
  sirven las skills.
- **Git:** ver el árbol de git, entornos y releases (D).

## H. Roadmap y mapa de versiones

Con todo diseñado: el roadmap y el mapa de versiones de todas las implementaciones hasta la `1.0.0` y después, con
qué va en cada versión; las mejoras de la `0.4` que no son evolutivos, también repartidas. Lo que ya espera:
`docs/registros/pendiente-1.0.0.md`.

## Apéndice: mapa inicial de modelos por necesidad (del usuario, 2026-10-30; B5)

A contrastar con lo que consideran mejor los expertos y, después, con las cifras reales de los informes.

```
ORQUESTACIÓN Y PLANIFICACIÓN
- Planificador / Lead:        Claude Fable 5.1, Claude Opus 5.5, GPT-6 Astra
- Descomposición de tareas:   Claude Opus 5.5, GPT-6.1 Sol, Gemini 4 Argon
- Enrutador de modelos:       Claude Haiku 4.5, Gemini 3.1 Flash

ARQUITECTURA Y DISEÑO DE SISTEMA
- Arquitecto de software:     Claude Opus 5.5, GPT-6 Astra, Claude Fable 5.1
- Diseño de API/contratos:    Claude Opus 5.5, GPT-6.1 Sol, DeepSeek V4 Pro
- Diseño de base de datos:    Claude Opus 5.5, Gemini 4 Argon, GLM-5.1

FRONTEND
- Componentes UI:             Claude Sonnet 5.5, Gemini 4 Argon, Kimi K3
- Estilos y diseño visual:    Gemini 4 Argon, GPT-6 Sol, Claude Sonnet 5.5
- Estado y lógica cliente:    Claude Sonnet 5.5, DeepSeek V4 Pro, Qwen 3.6 Plus
- Refactor de UI:             Claude Sonnet 5.5, Kimi K3, GLM-5.1

BACKEND
- Endpoints y controladores:  Claude Sonnet 5.5, DeepSeek V4 Pro, GPT-6 Sol
- Lógica de negocio densa:    Claude Opus 5.5, GPT-6 Astra, DeepSeek V4 Pro
- Servicios y microservicios: Claude Sonnet 5.5, GPT-6.1 Sol, GLM-5.1
- Integración con BD:         Claude Opus 5.5, DeepSeek V4 Pro, Qwen 3.6 Plus

TESTING Y CALIDAD
- Tests unitarios:            Claude Sonnet 5.5, DeepSeek V4 Pro, Kimi K3
- Tests de integración/E2E:   Claude Sonnet 5.5, GLM-5.1, GPT-6 Sol
- Generación de mocks:        Claude Haiku 4.5, Gemini 3.1 Flash, Qwen 3.6 Plus
- Cobertura y análisis:       Claude Haiku 4.5, DeepSeek V4 Pro

SEGURIDAD
- Revisión de seguridad:      Claude Fable 5.1, Gemini 4 Carbon, Claude Opus 5.5
- Auditoría de dependencias:  Claude Haiku 4.5, GPT-6.1 Sol, GLM-5.1
- Pentesting asistido:        Gemini 4 Carbon, Claude Fable 5.1

DEVOPS E INFRAESTRUCTURA
- CI/CD y pipelines:          Claude Sonnet 5.5, GPT-6 Sol, Gemini 3.1 Flash
- Infraestructura como código: Claude Opus 5.5, GPT-6 Astra, DeepSeek V4 Pro
- Contenedores y despliegue:  Claude Sonnet 5.5, GLM-5.1, Qwen 3.6 Plus

DATOS Y MIGRACIONES
- Migraciones de esquema:     Claude Opus 5.5, DeepSeek V4 Pro, GPT-6 Astra
- Scripts de datos/ETL:       Claude Sonnet 5.5, Qwen 3.6 Plus, GLM-5.1
- Optimización de consultas:  Claude Opus 5.5, DeepSeek V4 Pro, Gemini 4 Argon

DOCUMENTACIÓN Y EXPLORACIÓN
- Documentación técnica:      Claude Haiku 4.5, Gemini 3.1 Flash, Qwen 3.6 Plus
- Exploración de repositorio: Claude Haiku 4.5, Gemini 3.1 Flash, Kimi K3
- Resúmenes y clasificación:  Claude Haiku 4.5, Gemini 3.1 Flash, Qwen 3.6 Plus

MANTENIMIENTO Y REFACTORIZACIÓN
- Refactor multiplataforma:   Claude Sonnet 5.5, DeepSeek V4 Pro, Kimi K3
- Deuda técnica:              Claude Opus 5.5, GPT-6.1 Sol, GLM-5.1
- Actualización de dependencias: Claude Haiku 4.5, Qwen 3.6 Plus

AGENTES AUTÓNOMOS Y TAREAS LARGAS
- Coding agéntico general:    Claude Sonnet 5.5, GPT-5.5 Codex, Gemini 4 Carbon
- Tareas de larga duración:   GPT-5.5 Codex, Claude Fable 5.1, Devin
- Trabajo en paralelo:        Claude Haiku 4.5, Gemini 3.1 Flash, Cline

MODELOS OPEN-SOURCE / AUTOALOJADOS
- Código general:             DeepSeek V4 Pro, Qwen 3.6 Plus, GLM-5.1
- Razonamiento y algoritmia:  DeepSeek-R1, Qwen 3.6 Max, Kimi K3
- Código especializado:       Codestral, StarCoder2-15B, Qwen2.5-Coder
- Despliegue local/privado:   Qwen2.5-Coder, DeepSeek-R1, Codestral
```
