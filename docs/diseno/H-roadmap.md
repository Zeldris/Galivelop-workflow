# H. Roadmap y mapa de versiones

**Estado:** borrador con preguntas (2026-11-01). Al cerrarlo, pasa a `docs/roadmap.md` (con su par en inglés) y se
empieza a implementar por la primera tarea de la `1.0.0`.

Reparte todo lo decidido en los bloques A-G y lo que ya esperaba en
[`pendiente-1.0.0.md`](../registros/pendiente-1.0.0.md). Criterio (A-5): la `1.0.0` lleva lo que rompe compatibilidad y
la base de la medición; lo demás va en menores `1.x`; la `0.4` solo recibe arreglos. Los identificadores son los de
cada bloque (`B-3` = pregunta 3 del bloque B) hasta que la pregunta 1 fije los del roadmap.

## Mapa de versiones (propuesta)

### `0.4.3` (listo, espera tu confirmación)

P1-P4 de la recogida de `galivelop-developer`, R2 y R4 de su retro. Rama `ccr-6dfbc880-ddr41g`, marca `01274a9`.

### `0.4.4` (arreglos, otro día por la cadencia A-6)

- **D-6:** `worktree.baseRef: "head"` en el `settings.json` que instala el flujo.
- **Retro 0.4.2 P5:** la regla QUOTED del `pre-commit` sin falsos positivos en `.md` (es un fallo, no un evolutivo;
  ver pregunta 4).

### `1.0.0` «Base»: lo que rompe y lo que mide

En este orden, porque cada paso usa el anterior:

1. **Plan y roadmap:** `docs/roadmap.md` con los identificadores (D-13) y el plan reescrito según la tabla de A1
   (§1, §2, §7, §9, §10).
2. **Nombres (A2, A-3, A-4):** `gw-` en las skills propias, scripts en inglés, rutas del proyecto en inglés y
   configurables en `gw.json`; `gw-update` renombra y los ganchos aceptan los dos nombres durante la `1.x`.
3. **Config versionado (A3.2):** `schemaVersion` en `gw.json` y su migración en `gw-update`.
4. **Trazabilidad (D-11, D-12, D-15, D-16):** tipos de Conventional Commits con `version.py` sugiriendo el salto;
   `Refs:` obligatorio en `commit-msg` salvo merges; `Agent:` opcional; ramas `agent/<id>-…` y `fusionar.sh` copia
   `Refs:`.
5. **Medición base (B-1, B-2, B-3):** gancho `Stop` que lee los logs de sesión y escribe
   `docs/metrics/ledger.jsonl` (tokens por modelo y tipo, fecha, rama, `Refs`, subagente); precios en tabla con fecha.
6. **Repo público (E-2, E-3, D-3):** check de datos privados en el `pre-push` (lista en `.claude/gw.local.json`),
   recogidas anonimizadas (`private-project-1`) y repaso de las ya publicadas.
7. **Reglas deterministas (E-1, E-6):** auditoría de `AGENTS.md`/`CLAUDE.md` con check de tope de líneas; cada regla
   de `REVIEW.md` nombra su check o dice «criterio».
8. **Lo que ya esperaba:** toda la lista de `pendiente-1.0.0.md` (DEV P5-P8, VeriNews P1-P11, INS P9-P13, Portal P4,
   R1, retro 0.4.2 P3-P4…), ver pregunta 3.
9. **Documentación (E-8):** repaso completo al final, por subagentes.

### `1.1` «Medir y preguntar»

- **Informes (B-4, B-5, B-6):** `metrics.py report --period …`, `compare` y la alerta de 1,5× en el `SessionStart`;
  skill `gw-metrics`.
- **Modelos (B-7, B-8, B-10, B-11):** `models.disabled` con su gancho, señales de calidad, el selector recomienda
  modelo y esfuerzo de la sesión principal, modelo y esfuerzo por agente.
- **Preguntas (C-1..C-8, C-10):** `docs/questions.md`, modo restrictivo con su gancho, `gw-mode`, `modes.careful`
  activo por defecto; los subagentes devuelven sus preguntas.
- **Traza (D-14):** `trace.py <id>`.

### `1.2` «Front y otros agentes»

- **Pruebas de front (E-5, E-7, E-9..E-16):** guía en `patrones.md`, plantilla de config y los checks que decidan
  E-9..E-16.
- **Perfiles de instalación (E-4):** minimal/core/full, `core` por defecto.
- **Otros agentes (D-7, B-9):** `AGENTS.md` legible sin `@include`, skills también en `.agents/skills`; modelos no
  Anthropic vía opencode.

### `1.3` «MMC 1» (G-9)

Solo lectura: `mmc.py` en 127.0.0.1 (G-1), datos por JSON de los scripts con versión mínima (G-2), `--static` para la
nube (G-3), vistas de datos (G-6) y de git (G-7).

### `1.4` «MMC 2»

Config desde el MMC a través de `config.py`, con el diff y sin commit (G-4).

### `1.5` «MMC 3»

Perfiles por capas (G-5); entornos configurables y nuevos (D-9, G-8) con etiquetas `rc` para `uat` (D-10); roles
(D-17) con la comprobación del usuario de git por entorno.

### Después, sin número todavía

Sale cuando exista lo que necesita, y entonces se le pone versión:

- Tabla determinista de modelos y publicación de la tendencia con un A/B (B5, B-13): cuatro semanas de ledger.
- MMC multiproyecto (G-10), `modes.freeze` (C-9), patrón de exploradores en `orchestrate-dealer` (B-12),
  OpenTelemetry como opción (B-1).
- Recogida de los repos privados (R3): cuando haya acceso de lectura.

## Preguntas (se responden por número)

1. **Identificadores del roadmap:** cada tarea lleva la letra de su bloque y un número (`B3`, `D12`), los mismos que
   ya usa el diseño; una tarea nueva toma el siguiente número de su bloque y nunca se reutiliza uno. **Rec.:** sí.
2. **Alcance de la `1.0.0`:** los nueve pasos de arriba, en ese orden. **Rec.:** sí; es lo que rompe más la base que
   las menores necesitan.
3. **`pendiente-1.0.0.md`:** entera en la `1.0.0` (ya prometida y son piezas pequeñas) o lo no urgente a la `1.1`.
   **Rec.:** entera en la `1.0.0`.
4. **`0.4.4`:** D-6 y la P5 de la retro 0.4.2 (falso positivo = fallo). **Rec.:** sí; R1 y P3-P4 siguen en la
   `1.0.0`, que son comprobaciones nuevas.
5. **Orden de las menores** (`1.1` medir y preguntar → `1.2` front → `1.3`-`1.5` MMC). **Rec.:** sí; el MMC va al
   final porque enseña datos que crean las anteriores.
6. **Lo de «Después»:** sin versión hasta que exista lo que necesita. **Rec.:** sí; se le pone versión al abrir la
   menor en que quepa.
7. **Dónde vive:** `docs/roadmap.md` en español con `docs/roadmap.en.md`, como el plan; `trace.py` y `commit-msg` leen
   los identificadores del español. **Rec.:** sí.
8. **Rama de implementación:** se sigue en `version/1.0.0`; los subagentes, en `agent/<id>-…` (D-16) desde el paso 4;
   antes, con los nombres de hoy. **Rec.:** sí.
9. **E-9..E-16** (pruebas de front, en `E-calidad.md`): solo afectan a la `1.2`. **Rec.:** responderlas ahora para
   cerrar el diseño entero, como pediste; si prefieres, se dejan para cuando se abra la `1.2`.
