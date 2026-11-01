# Bloque A. Marco: público, nombres y versionado

**Estado:** borrador (2026-11-01). Propuestas del agente y preguntas para el usuario; nada decidido salvo lo marcado
como «decidido». Se cierra cuando el usuario responda las preguntas de la última sección.

## A1. Todo público (decidido por el usuario, 2026-10-30/31)

Este repo es el producto: público, y todas sus versiones también. Se busca difusión y uso, no venta.

**Qué cambia en el plan** (se reescribe al cerrar el bloque, no antes):

| Sitio | Hoy dice | Pasa a decir |
|---|---|---|
| §1 «Fin del camino» | La `1.0.0` sola, en un repo público aparte; las siguientes, privadas; solo como plugin | Este repo es el público; cada versión se publica aquí; plugin y copia gestionada valen los dos |
| §2, tabla | «siempre privado»; «solo la `1.0.0` es pública» | Público; publicación de cada versión con su release |
| §2, nota del plugin | La licencia controla el uso; la de la `1.0.0`, abierta | Licencia fijada (ver pregunta A-1) |
| §7 | «Por decidir: si la `1.0.0` llega a `main` antes de cumplir la §10» | Se decide en A3 |
| §9, Fase 10 «Público» | Copia a un repo público | Pasa a «Lanzamiento»: ficha en el portal, npm si se hace, publicaciones (`gw-media-content`) |
| §10, «Nada privado» | Criterio para la `1.0.0` | **Requisito ya, en cada subida**: el repo ya es público |

**Consecuencia inmediata de A1:** lo que hoy hay en el repo y no debería estar en uno público se revisa ya, no en
la `1.0.0`. Encontrado al preparar este bloque:

- `AGENTS.md` lleva el correo personal del usuario (la orden `git config user.email …`).
- `docs/propuestas/` tiene diez recogidas con el nombre y el contenido de proyectos del usuario (Tarkor, portal,
  VeriNews…), y dos de ellos eran privados el 2026-10-27 (`galivelop-image-generator`, `galivelop-voice-generator`).
- La limpieza completa de la documentación (sin «basura», ajustada a lo que hay) es del bloque E; aquí solo se
  decide el criterio.

**Propuesta:** un check (`scripts/`) que falle si una subida añade datos personales o nombres de la lista de repos
privados que declare el config; el correo pasa a una variable o a un archivo local sin versionar.

## A2. Nombres: `gw-` y todo en inglés (decidido el principio, falta el alcance)

Hoy:

- **Skills propias** (6 sin prefijo): `selector`, `orchestrate-dealer`, `opt-tokens`, `opt-ai`, `scout-updates`, y
  las `gw-` que ya lo llevan (`gw-doctor`, `gw-harvest`, `gw-init`, `gw-update`, `gw-media-content`,
  `gw-media-content-now`).
- **Skills de terceros** (15, de mattpocock/skills, MIT): `retro`, `research`, `pr`, `grilling`, `to-spec`,
  `wayfinder`, `writing-for-agents`… Se copian sin cambios y `scout-updates` sigue su origen por el nombre.
- **Scripts** con nombre en español: `bitacora.py`, `revisado.sh`, `fusionar.sh`, `recuperar.py`, `antes-de-parar.py`,
  `rojo-sin-arreglo.sh`, `tope-subagentes.py`… Se copian a `.claude/gw/scripts/` de cada proyecto.
- **Rutas que el flujo crea en un proyecto**, en español: `docs/traspaso.md`, `docs/registros/`, `docs/propuestas/`.
  En inglés ya: `.claude/gw.json` y sus claves, los mensajes de los scripts, las `SKILL.md`.

**Propuesta:**

1. Skills propias: todas con `gw-` (`gw-selector`, `gw-dealer` o `gw-orchestrate-dealer`, `gw-opt-tokens`…).
2. Skills de terceros: conservan su nombre original (crédito, licencia y seguimiento con `scout-updates`); el
   prefijo marca lo que es del flujo, no lo que trae. Alternativa: `gw-` también, con el nombre original en
   `metadata.source` (ver pregunta A-3).
3. Scripts: nombres en inglés (`handoff.py`, `reviewed.sh`, `merge-branch.sh`, `recover.py`, `before-stop.py`…). Sin
   `gw-` porque ya viven en `.claude/gw/`.
4. Rutas en el proyecto: en inglés y configurables en `gw.json` (como ya es `log`): `docs/handoff.md`,
   `docs/records/`, `docs/proposals/`. El contenido sigue en el idioma del proyecto (`language`).
5. Este repo: lo mismo para lo que se instala; sus documentos para personas siguen emparejados en `docs/es/` y
   `docs/en/`. Los internos (`docs/diseno/`, `docs/investigacion/`, `docs/registros/`) pasan a inglés de nombre.
6. **Migración:** es un cambio que rompe (plan §7: mayor), así que va en la `1.0.0`. `gw-update` renombra en el
   proyecto lo que encuentre con el nombre viejo, y los ganchos aceptan los dos nombres durante la `1.x`.

## A3. Sistema de versionado (decidido el principio: todo versionado)

Lo que ya existe: SemVer en `plugin.json` (un dato, un sitio), CHANGELOG ES/EN obligatorio, etiqueta `vX.Y.Z`,
recogida al abrir versión, `metadata.version` en cada skill y cabecera de versión en scripts y plantillas.

**Propuesta:**

1. **Una sola versión de producto.** Cada pieza lleva la versión del producto en la que cambió por última vez, no
   una SemVer propia: con 30 skills, versiones sueltas serían 30 números que nadie mira.
2. **Versión del config.** `gw.json` lleva un `schemaVersion` y `gw-update` sabe migrarlo; así un proyecto
   viejo nunca queda roto en silencio.
3. **Líneas:** la `0.4.x` solo con arreglos hasta que salga la `1.0.0`; después, solo la última menor recibe
   parches. Las ramas de línea (`version/1.0.0`) y los entornos los decide el bloque D.
4. **Mapa de versiones** (`docs/roadmap.md`, bloque H): cada cosa diseñada lleva un identificador (bloque D) y la
   versión a la que va; el CHANGELOG lo cita, así se sigue de la idea a la release.
5. **Cadencia:** a lo sumo una publicación al día (lo que dijiste al aplazar el parche `0.4.3`) y los parches se agrupan. Un arreglo
   grave del flujo puede saltársela, con tu confirmación.
6. **Cuándo es `1.0.0`:** cuando esté hecho lo que el mapa de versiones asigne a la `1.0.0`. Los criterios de la §10
   (tres proyectos, cuatro semanas…) pasan a medir la madurez de la línea `1.x`, sin bloquear la etiqueta.

## Preguntas para el usuario

- **A-1. Licencia:** ¿se queda la MIT? Es la que más ayuda a la difusión y la que ya tienen las skills de terceros.
- **A-2. Lo privado que ya está publicado:** ¿qué repos siguen privados hoy? ¿Se quita tu correo de `AGENTS.md` y se
  revisan las recogidas de `docs/propuestas/` (ahora, en un parche, o en el bloque E)?
- **A-3. Prefijo de las skills de terceros:** ¿conservan su nombre (propuesta) o todas llevan `gw-`?
- **A-4. Rutas del proyecto en inglés** (`docs/handoff.md`, `docs/records/`…): ¿sí, también en los proyectos en
  español?
- **A-5. La `1.0.0`:** ¿sale cuando esté hecho su alcance del mapa, o sigue esperando a los criterios de la §10?
- **A-6. Cadencia:** ¿una publicación al día como máximo, con excepción para lo grave?

## Respuestas del usuario (2026-11-01)

- **A-1:** licencia MIT, se queda.
- **A-2:** siguen privados `galivelop-voice-generator`, `galivelop-developer` y VeriNews_AI, siempre (por confirmar que
  «toveriai» es VeriNews_AI). Falta decidir cuándo se quita el correo de `AGENTS.md` y se revisan las recogidas.
- **A-3:** las skills de terceros conservan su nombre; `gw-` solo en lo que creamos nosotros.
- **A-4:** rutas del proyecto en inglés, también en los proyectos en español.
- **A-5:** decidida (2026-11-01): la recomendación del agente (abajo).
- **A-6:** decidida (2026-11-01): la recomendación del agente (abajo): como mucho una publicación al día.
- **Abierto:** lo que queda de A-2 va en la lista de preguntas de [`D-git.md`](D-git.md) (puntos 1-4).

### Recomendación del agente para A-5

La `1.0.0` lleva **todo lo que rompe compatibilidad y la base de la medición**; lo demás va en menores `1.x`, con el
mapa entero de versiones decidido ahora (bloque H). Así todo lo decidido en esta sesión tiene versión desde hoy, pero
la `1.0.0` no espera al Management Center.

Motivos:

1. SemVer: lo que añade sin romper (una skill, un informe, el panel) cabe en una menor; lo que rompe (nombres, rutas,
   config) tiene que ir junto en la mayor, para migrar una sola vez.
2. Algunas piezas dependen de datos que aún no existen: la tabla determinista de modelos (B5) necesita semanas de
   informes del escuchador (B1, B2). No pueden salir en la misma versión.
3. Mientras no salga la `1.0.0`, la `0.4` solo recibe arreglos: una `1.0.0` enorme deja meses sin nada nuevo.

### Explicación de A-6 (cadencia)

La cadencia es cada cuánto se publica una versión (subida a `main`, etiqueta y release). Ejemplo: el `0.4.1` y el
`0.4.2` salieron casi seguidos, y el `0.4.3` lo aplazaste para no subir demasiadas versiones en un día. La propuesta
convierte eso en regla: como mucho una publicación al día; los arreglos que lleguen después esperan en la rama y salen
juntos en la siguiente; solo un arreglo grave (un gancho que bloquea subidas buenas, pérdida de datos) sale antes, con
tu confirmación. La alternativa es un calendario fijo, como gstack: publicar ciertos días de la semana con un mínimo de
horas entre una versión y la siguiente.
