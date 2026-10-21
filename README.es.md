# Galivelop-workflow

[English](README.md)

La forma de trabajar del taller Galivelop con agentes de programación (primero Claude Code), sacada de proyectos
reales y generalizada para cualquier repositorio. Es la **fuente única y versionada** de sus skills, ganchos y
plantillas.

> **Estado: `0.1.0`, en construcción (etapa 1, fase 1).** Todavía no está listo para aplicarse. Ver el
> [plan](docs/plan.md) y la [bitácora](docs/traspaso.md).

## Qué resuelve

1. **Relevos sin pérdidas.** Una sesión puede acabarse en cualquier momento (tokens, contenedor, cambio de cuenta)
   y la siguiente sigue sin preguntar: bitácora al día, commit + push en cada punto estable.
2. **Elegir bien antes de empezar.** Un selector decide qué skill y qué modelo pide cada tarea, y los subagentes
   baratos se llevan lo mecánico.
3. **Nada sin revisar llega a `main`.** Revisión del diff, marca de revisado guardada en el repo y ganchos que no
   dejan subir código sin ella.
4. **Pocos tokens sin perder calidad.** Orquestación, compactación, recuperación tras `/clear` y retros que miden y
   proponen mejoras.

## Cómo se aplicará

- **Etapa 1:** un agente de IA aplica el flujo a tu proyecto leyendo este repo (guía + plantillas + scripts
  deterministas), y un script `doctor` confirma que queda bien montado.
- **Etapa 2:** instalación automática sin IA, para proyectos nuevos (lo recomendado) y existentes.

Las reglas del flujo viven en `AGENTS.md` (estándar abierto que lee cualquier agente); las skills siguen el formato
abierto [Agent Skills](https://github.com/agentskills/agentskills).

## Documentación

- [Visión general del flujo](docs/es/flujo.md)
- [Plan](docs/plan.md) · [Changelog](CHANGELOG.md)

## Agradecimientos

Aprendimos a trabajar así gracias al trabajo de **[Matt Pocock](https://github.com/mattpocock)**, sobre todo su
[mattpocock/skills](https://github.com/mattpocock/skills): la idea de guiar a los agentes con skills pequeñas y bien
escritas, el ciclo de revisión y retro, y muchas de las skills que se incluyen aquí, que son suyas (MIT), con su
mención en cada una y en [`CREDITS.md`](CREDITS.md). Gracias, Matt.

## Licencia

[MIT](LICENSE). Las skills de [mattpocock/skills](https://github.com/mattpocock/skills) conservan su licencia MIT
([`LICENSE-mattpocock-skills`](LICENSE-mattpocock-skills)); ver [`CREDITS.md`](CREDITS.md).
