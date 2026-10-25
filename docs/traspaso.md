# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El plan está en [`docs/plan.md`](plan.md)
> ([English](plan.en.md)).

## Estado actual

| Campo | Valor |
|---|---|
| Rama | `ccr-6dfbc880-ddr41g`; `main` = `ea81c9f` = **release `v0.3.0`** (2026-10-23). `claude/galivelop-workflow-inicio` está **obsoleta** (se quedó en `0f36412`): no se trabaja en ella |
| Check | `bash tests/comprobar.sh` en verde; CI y `release.yml` en verde sobre `9b97d7b` (Linux y macOS) con el repo público un rato; en privado el CI espera a que se renueve el cupo de Actions |
| Fase en curso | **6 cerrada** y `0.3.0` publicada en `main` (2026-10-23); P7 del instalador aplicada en la rama (`0.4.0`, sin publicar); recogida de la `0.4.0` hecha y decidida (P1, P3, P4, P5 aplicadas; P2 aplazada). Próxima: **7. Rodaje etapa 1** |
| Último punto estable | `gw-media-content` (b2 de 3): `skills/gw-media-content/plantilla/` (pieza genérica: `ficha.md`, `x.md`, `reddit.md`, `linkedin.md`, `discord.md` y 7 fuentes HTML autónomas en `medios/fuente/`: tarjeta, diagrama, métricas, cita, código, antes-después y carrusel, con la paleta en variables CSS y el tamaño en `<meta name="gw-size">`) y `scripts/render.mjs` (Playwright resuelto desde la carpeta actual o `GW_PLAYWRIGHT_DIR`, ImageMagick con WebP; escribe `<n>.webp`, `<n>-mini.webp` y `<n>.png`, y `carrusel*.html` a PDF; falla cerrado y avisa de lo que desborda o de imágenes rotas) con `test_render.py` (60 casos; probado también con Chromium real). Arreglos de la revisión de `render.mjs` hechos (2026-10-25): se ejecuta también por un enlace simbólico; detecta elementos con scroll y elementos o texto fuera de la caja de contenido del cuerpo o del `.slide` (capacidad real de `codigo.html`: 10 líneas de unos 65 caracteres); falla con errores de la página (`pageerror`) y con huecos `{{` en el texto; red bloqueada (una petición abortada cuenta como recurso que no carga); `gw-size` sin depender del orden de atributos, con `×`, sin mirar comentarios y fallando si no se entiende; el PDF toma el tamaño solo de `gw-size` (sin `preferCSSPageSize` ni `@page{size}`) y se cuenta que tenga tantas páginas como `section.slide`; el render real tiene casos que fallan (titular largo, línea de 120 caracteres, imagen rota). Prefijos de tarea de `comprobar.py`: solo los genéricos, más `--prefijos-tarea A,B,…`. Arreglos de la revisión de `comprobar.py` hechos (2026-10-25): idiomas obligatorios y sin secciones repetidas, `CLAVES` de `reglas.json` validadas al cargar, LinkedIn con `.png/.jpg/.gif` (`linkedin.imagen_formatos`, P), cada fila de `## Imágenes` validada contra cada canal de su celda, imágenes truncadas, peso de X con secuencias de emoji, hilos con `**n/m**`, menos falsos positivos de jerga y la orden completa de `render.mjs` en los mensajes; `discord.md` de la plantilla titula con `###` (un `##` cierra la sección del idioma). Faltan b3 (SKILL.md de `gw-media-content` y `-now`, `cifras.py`). Antes: b1 (`reglas.json`, `comprobar.py` + `test_comprobar.py`) y la segunda recogida del 2026-10-25 decidida (`docs/propuestas/2026-10-25-world-maker-fantasy-2.md`), investigación de redes en `docs/investigacion/redes-sociales.md` |
| Siguiente paso | Tanda de la segunda recogida, en este orden: (a) verificar los datos NV de X, Reddit, LinkedIn y Discord en `docs/investigacion/redes-sociales.md`; (b) portar `gw-media-content` (hasta 10 propuestas) y crear `gw-media-content-now` (una pieza a `<carpeta>/AAAA-MM-DD-<tema>/`), redes X, Reddit, LinkedIn y Discord, origen WMF `.claude/skills/gw-media-content/` @ `a9eb7bbf`; (c) P2; (d) P4. Luego la `0.4.0` sigue hasta el **2026-10-30** (otra recogida y publicar). Aplazada a la Fase 7: P3 de Labs (`to-spec`, `wayfinder`) |

### Fases

- [x] 0. Verificar (2026-10-21)
- [x] 1. Esqueleto (2026-10-21)
- [x] 2. Skills (2026-10-21)
- [x] 3. Ganchos y scripts (2026-10-22; CI en verde en Linux y macOS)
- [x] 4. Plantillas y aplicación (2026-10-22)
- [x] 5. Piloto: Portal-Galivelop (2026-10-22; cerrada con el usuario)
- [x] 6. Piloto: Tarkor e instalador (2026-10-23; VeriNews, en la Fase 8)
- [ ] 7. Rodaje etapa 1
- [ ] 8. Instalador sin IA (etapa 2)
- [ ] 9. Plugin y npm
- [ ] 10. Público

## Para la próxima publicación

`0.4.0`: abierta hasta el 2026-10-30 (usuario, 2026-10-23); antes de publicarla, otra pasada de `gw-harvest` sobre lo de
esa semana.

`0.2.0` publicada (etiqueta y release a mano en GitHub, título `Galivelop-workflow vX.Y.Z`, notas de la entrada del CHANGELOG). Para la siguiente: `release.yml` con lanzamiento manual desde Actions que cree la etiqueta (la
sesión en la nube no puede subir etiquetas: 403 del proxy).

## Hecho (5 últimas)

1. 2026-10-25 — Recogida de Tarkor (`4d54eeaf`..`076fe877`) y primera de Labs-Log-Detective (`bc501f91`, instaló la
   `0.3.0`): `docs/propuestas/2026-10-25-world-maker-fantasy.md` (P1 `commit-msg` con `bitacora.py check`, P2 precondición
   en tandas, P3 fases en la fila de tarea) y `2026-10-25-labs-log-detective.md` (P1 bug de `doctor.py`, P2-P3 skills
   `wait-what`, `to-spec`, `wayfinder`, P4 `/clear` por tarea, P5 migrar desde copia a mano). Aprobadas y aplicadas todas menos P3 de Labs (aplazada a la Fase 7).
2. 2026-10-23 — Recogida de la `0.4.0` decidida: P1 (`recoger.py` informa de las líneas «Propuesta para el flujo»,
   con su test), P3 (`recuperar.py` espera 3 s el transcript del gancho y avisa al caer al más nuevo), P4
   (plantilla «lo elige») y P5 (menores a «Pendiente») aplicadas; P2 (`ci.setup`/`ci.after`) aplazada.
3. 2026-10-23 — Recogida de la `0.4.0` (portal, WMF, instalador, VeriNews): 5 propuestas del portal en
   `docs/propuestas/2026-10-23-portal-galivelop.md`; los otros tres, nada nuevo. Regla nueva: cada versión empieza con
   una recogida (`AGENTS.md`, plan §7, skill), y `version.py --release` la exige.
4. 2026-10-23 — P7 del instalador aplicada (`0.4.0`, sin publicar): sin CI, el check en local vale con la confirmación
   de la persona («comprobado solo en local»), en `AGENTS.md` y plantillas; el gancho lo nombra al bloquear.
5. 2026-10-23 — **`0.3.0` publicada en `main`** (ea81c9f). El usuario decide la P7: un check que pasó en local vale
   cuando Actions no arranca.

## Pendiente

- El render real (`RenderReal` en `test_render.py`) no lo cubre el CI: el CI no tiene Playwright, Chromium ni
  ImageMagick y añadirlos gasta cupo de Actions. Se corre en local (`GW_PLAYWRIGHT_DIR` + `magick` con WebP) antes de
  tocar `render.mjs` o las fuentes de la plantilla; sin ellos esos casos se saltan.
- Menores de la revisión de render.mjs (gw-media-content), no se revisan otra vez en esta tanda: ImageMagick
  interpreta `[]*?` en nombres; solo se limita el ancho (capturas muy altas superan los píxeles de LinkedIn y el máximo
  de WebP); `antes.png`/`despues.png` usados por `antes-despues.html` se renderizan como capturas; el fallo de
  `chromium.launch` por librerías del sistema sugiere `install` en vez de `install-deps`; los errores de `magick` no
  dan orden; renders a medias quedan mezclados; no comprueba la versión de Node; una fuente pedida por nombre en una
  carpeta de fecha exige que exista en todas las piezas.
- Menores de la revisión de comprobar.py (gw-media-content), no se revisan otra vez en esta tanda: marca C sin
  leyenda en §5 y título de Reddit fuera de §5.2; los límites NV/C fallan sin decir que no están verificados; piezas
  mal nombradas sin ficha se saltan en silencio; render sin fuente y falta de medios/fuente/ pasan; nombres de
  `## Canales` sin validar; el alt `es: Sí / no: nada` se parte mal; UTF-8 inválido da traceback.
- [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) revisado (2026-10-25): 4 propuestas sin
  decidir en `docs/propuestas/2026-10-25-codegraph.md` (P1 gancho que inyecta la fila del mapa, P2 comprobador
  genérico del mapa, P3 anti-patrones en `writing-for-agents`, P4 probar la herramienta en WMF, se recomienda aplazar).
- Diez repos de una lista de X revisados (2026-10-25): 10 propuestas en `docs/propuestas/2026-10-25-repos-x.md`. P4
  (regex) y P7 (skills e instrucciones) aplicadas (eea8892) y el arreglo posterior (gancho de `main` con tabuladores y
  saltos escapados; ZWJ en emojis); el resto en curso, la siguiente es P5 (`recuperar.py`): P1 gancho `Stop`, P2 guarda
  de config, P3 tope de subagentes, P5 `recuperar.py`, P6 dealer, P8 disparo de skills, P9 `REVIEW.md`, P10 apuntes 9-10.

- Propuestas aprobadas para `v0.2.0`, en orden: `docs/propuestas/2026-10-22-reparto.md` (la de 2026-10-21, toda hecha).

- Menores de la revisión de la tanda A (no se revisan otra vez en este PR): `non_capturing` toca paréntesis en
  comentarios `(?x)`/`(?#…)`; `--ran-one` cuenta dos veces si el ejecutor repite el nombre del test en el resumen;
  `header_version` solo mira las 5 primeras líneas.
- Menores de la revisión de la tanda B: sin python3, `revision-antes-de-main.sh` deja pasar
  `gh api …/pulls -f title=` (crear el PR por la API; el hueco ya existía) y bloquea `gh pr view 3 && echo create`
  (exceso de celo).
- Menores de la revisión del vigilante (89fdf09): el KILL de los 5 s podría dar con un pgid reutilizado (se acepta:
  el vigilante se detiene si la orden acaba antes).
- Menores de la revisión de la tanda E: el aviso de ventanas mezcladas de `opt-tokens/medir.py` salta con un
  `/compact` manual o una etapa muy corta; `opt-ai/medir.py` ignora un `app.turn` 0 o vacío y su clave sintética
  choca con una tarea llamada «turn»; `instant` descarta sin avisar un `ts` que `fromisoformat` no lee (Python <3.11);
  `quality_bench.py` envía un `format` de texto como `json_schema` con la API openai y `pairs` pisa en silencio un
  modelo repetido en dos `outputs.jsonl`.
- Menor de la revisión antes de `main`: `checkWrapper` se aplica en tres sitios (`pre-push` y `fusionar.sh` con
  `sed`, `config.py` con `shlex`) y la plantilla de CI no lo aplica: que lo construya solo `config.py`.
- Menores de la revisión de los arreglos antes de `main` (3b47af1): un push muerto en el mismo namespace deja su
  worktree 24 h (guardar `hostname:pid` en el marcador); `worktreeDir` con `~` o `..` no se valida en `config.py`;
  `cksum` de 32 bits puede juntar dos repos en una carpeta (el borrado sigue exigiendo 24 h y proceso muerto);
  `update_pull_request` con `state:open` y sin `base` no se juzga como reapertura; `compare.py default_root` da
  traceback sin git y, desde la caché del plugin, cae al cwd (exigir `--root`).
- Menores de la revisión del flujo 0.3.0 que hizo el portal (P5 de `docs/propuestas/2026-10-23-portal-galivelop.md`):
  `config.py related` acepta un `cwd` con `..` o absoluto en `relatedTests` (que `validate` lo rechace);
  `session-start.sh`: `kill -- -$wd` no es un grupo y el `sleep` del vigilante queda vivo hasta el tope;
  `revision-antes-de-main.sh` sondea `gh api repos/<o>/<r>` en cada llamada y juzga cambios de título o base de un PR
  cerrado; `doctor.py` da por bueno un `npm run check` citado en un comentario (y avisos del glosario repetidos por
  mayúsculas, por comprobar); `validate` no avisa de un `worktreeDir` dentro del repo ni de un `checkWrapper` que
  limpia el entorno. Con la config de la punta de `main` rota, `pre-push` y el gancho fallan cerrados a propósito: se
  sale con un PR revisado que la arregle, o la persona sube a mano.
- P2 de `docs/propuestas/2026-10-23-portal-galivelop.md` (`ci.setup`/`ci.after` y `aplicar.py --update` sin pisar un
  `comprobar.yml` con pasos propios): aplazada a la siguiente versión.
- Que el usuario cambie la rama por defecto de GitHub a `main` (Settings → Branches); no hay herramienta para ello.
- R2 de la retro: que `doctor.py` detecte skills homónimas en la sesión (sin forma fiable aún; queda en las guías).
- Opción D (plugin desde el script de entorno de la nube): queda para la Fase 9.
- La `1.0.0` solo como plugin (decidido 2026-10-22): en la Fase 9, plugin como única distribución hacia fuera y
  ganchos de git desde el plugin (sin probar); en la Fase 10, licencia de la `1.0.0` (abierta) y el portal quita su
  copia del flujo desde una sesión suya. Su historial seguirá teniendo la copia `0.2.0` (MIT).

## Comprobar el estado

```bash
git fetch origin && git status && git log --oneline -10
```
