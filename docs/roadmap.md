# Roadmap

> Mapa de versiones de Galivelop-workflow ([English](roadmap.en.md)). Sale del diseño cerrado el 2026-11-01
> ([`diseno/H-roadmap.md`](diseno/H-roadmap.md), «mapa nuevo»), que lleva el detalle y las respuestas del usuario.
> La regla de versiones está en el plan §7: solo la última menor publicada recibe parches y los evolutivos van a la
> siguiente menor; **todo lo que rompe va en la `0.5`**.

## Identificadores

Cada tarea lleva la letra de su bloque de diseño y un número (`B3`, `D12`): el de su pregunta numerada en
`docs/diseno/` (`B3` = `B-3`, la pregunta 3 del bloque B), nunca el de un apartado (`## A2.`, `B1` entre paréntesis).
Una tarea nueva toma el siguiente número libre de su bloque (en el A, desde `A7`) y **un número nunca se
reutiliza**. Este archivo, en español, es la única fuente de ids (D13): `trace.py` y el `commit-msg`
los leen de aquí. Los evolutivos que traen las recogidas esperan en [`registros/pendiente.md`](registros/pendiente.md)
con su versión y toman id al entrar en la versión.

| Bloque | Tema | Diseño |
|---|---|---|
| A | Marco: público, nombres, versionado | [`A-marco.md`](diseno/A-marco.md) |
| B | Medición de gasto y modelos | [`B-medicion.md`](diseno/B-medicion.md) |
| C | Preguntas y modo restrictivo | [`C-preguntas.md`](diseno/C-preguntas.md) |
| D | Git: entornos, releases, trazabilidad, roles | [`D-git.md`](diseno/D-git.md) |
| E | Reglas deterministas, pruebas de front, documentación | [`E-calidad.md`](diseno/E-calidad.md) |
| G | Management Center (MMC) | [`G-mmc.md`](diseno/G-mmc.md) |
| H | Roadmap y mapa de versiones | [`H-roadmap.md`](diseno/H-roadmap.md) |

## Mapa

| Versión | Nombre | Rama | Estado |
|---|---|---|---|
| `0.4.4` | Parche | `ccr-6dfbc880-ddr41g` | pendiente (otro día, cadencia A6) |
| `0.5` | Base | `version/0.5.0` | **en curso** |
| `0.6` | Medir | — | — |
| `0.7` | Preguntar | — | — |
| `0.8` | Front y otros agentes | — | — |
| `0.9` | Estable | — | — |
| `1.0` | MMC 1 (solo lectura) | — | — |
| `1.1` | MMC 2 (config) | — | — |
| `1.2` | MMC 3 (perfiles, entornos, roles) | — | — |

Casillas: `[ ]` pendiente, `[x]` hecha (con la fecha; el commit lo da `git log -S`).

### `0.4.4` — parche

- [ ] **D6:** `worktree.baseRef: "head"` en el `settings.json` que instala el flujo.
- [ ] **Retro 0.4.2 P5:** la regla QUOTED del `pre-commit`, sin falsos positivos en `.md` (un secreto real sigue
  bloqueado).

### `0.5` «Base» — todo lo que rompe

En este orden, porque cada paso usa el anterior:

1. **Plan y roadmap**
   - [x] **H14** (2026-11-02): regla de versiones nueva en `AGENTS.md` y plan §7.
   - [x] **D13** (2026-11-02): este roadmap, con su par en inglés.
   - [x] **H12** (2026-11-02): `pendiente-1.0.0.md` pasa a `pendiente.md`, con la versión en cada línea.
   - [ ] **A7:** el plan reescrito según la tabla del apartado A1 (§1, §2, §7, §9, §10).
2. **Nombres**
   - [ ] **A8:** `gw-` en las skills propias (las de terceros conservan su nombre, A3) y scripts en inglés (apartado A2).
   - [ ] **A4:** rutas del proyecto en inglés (`docs/handoff.md`, `docs/records/`…), configurables en `gw.json`, también
     en los proyectos en español. `gw-update` renombra y los ganchos aceptan los dos nombres durante la `0.x`.
3. **Config versionado**
   - [ ] **A9:** `schemaVersion` en `gw.json` y su migración en `gw-update` (apartado A3, punto 2).
4. **Trazabilidad**
   - [ ] **D11:** tipo de Conventional Commits en la primera línea (`fix(B1): …`) y `version.py` sugiere el salto.
   - [ ] **D12:** trailer `Refs: <id>` obligatorio en el `commit-msg` (salvo merges), validado contra este archivo.
   - [ ] **D15:** trailer `Agent: <skill>` opcional, sin modelo.
   - [ ] **D16:** ramas de subagente `agent/<id>-<tema>` y `fusionar.sh` copia `Refs:` al commit de fusión.
5. **Repo público**
   - [ ] **E2:** check de datos privados en el `pre-push` (correos, claves, repos privados; lista en
     `.claude/gw.local.json`).
   - [ ] **E3 / D3:** recogidas anonimizadas (`private-project-1`) y repaso de las ya publicadas.
6. **Reglas deterministas**
   - [ ] **E1:** auditoría de `AGENTS.md` y `CLAUDE.md`, con un check de tope de líneas.
   - [ ] **E6:** cada regla de `REVIEW.md` nombra su check o dice «criterio».
7. **Lo que ya esperaba:** los puntos de [`registros/pendiente.md`](registros/pendiente.md) marcados `0.5`.

### `0.6` «Medir»

- [ ] **B1, B2, B3:** gancho `Stop` que lee los logs de sesión y escribe `docs/metrics/ledger.jsonl` (tokens por modelo
  y tipo, fecha, rama, `Refs`, subagente); precios en tabla con fecha.
- [ ] **B4, B5, B6:** `metrics.py report --period …`, `compare` y la alerta de 1,5× en el `SessionStart`; skill
  `gw-metrics`.
- [ ] **B7, B8, B10, B11:** `models.disabled` con su gancho, señales de calidad, el `selector` recomienda modelo y
  esfuerzo de la sesión principal, modelo y esfuerzo por agente.

### `0.7` «Preguntar»

- [ ] **C1-C8, C10:** `docs/questions.md`, modo restrictivo con su gancho, `gw-mode`, `modes.careful` activo por
  defecto; los subagentes devuelven sus preguntas.
- [ ] **D14:** `trace.py <id>`.

### `0.8` «Front y otros agentes»

- [ ] **E4:** perfiles de instalación (minimal/core/full, `core` por defecto).
- [ ] **E5, E7, E9-E16:** pruebas de front: guía en `patrones.md`, plantilla de config y los checks que deciden
  E9-E16.
- [ ] **D7, B9:** `AGENTS.md` legible sin `@include`, skills también en `.agents/skills`; modelos no Anthropic vía
  opencode.

### `0.9` «Estable»

- [ ] **E8:** repaso completo de la documentación, por subagentes.
- [ ] **G2:** lo que el MMC necesita de los scripts: salidas JSON con versión mínima.

### `1.0` «MMC 1»

- [ ] **G1, G3, G6, G7:** solo lectura: `mmc.py` en 127.0.0.1, `--static` para la nube, vistas de datos y de git.

### `1.1` «MMC 2»

- [ ] **G4:** config desde el MMC a través de `config.py`, con el diff y sin commit.

### `1.2` «MMC 3»

- [ ] **G5, G8, D9, D10, D17:** perfiles por capas, entornos configurables y nuevos con etiquetas `rc` para `uat`,
  roles con la comprobación del usuario de git por entorno.

## Después, sin número

Sale cuando exista lo que necesita, y entonces se le pone versión:

- **B13:** tabla determinista de modelos y publicación de la tendencia con un A/B, sobre las señales de B8; necesita
  cuatro semanas de ledger.
- **G10:** MMC multiproyecto. **C9:** `modes.freeze`. **B12:** patrón de exploradores en `orchestrate-dealer`.
  **B1** (opción): OpenTelemetry.
- **R3:** recogida de los repos privados (`galivelop-image-generator`, `galivelop-voice-generator`), cuando haya acceso
  de lectura.
