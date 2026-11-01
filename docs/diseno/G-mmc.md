# G. Management Center (MMC)

**Estado:** cerrado (2026-11-01): las 10 preguntas, aprobadas por el usuario según la recomendación del agente («Del 1 al 10 todo ok»). Nada se implementa hasta cerrar el diseño (bloque H).

Fuentes: [`README.md`](README.md) (bloque G); lo que el MMC tiene que mostrar o configurar sale de los bloques B, C y D
(medición, modos, entornos, roles, `trace.py`); ideas de OpenHands, thinkrail y opencode en `docs/investigacion/ref-*.md`.

## Preguntas (se responden por número)

Cada punto lleva la recomendación del agente (**Rec.**).

1. **Qué es el MMC:** hay cuatro opciones.
   - (a) Una web local: `python3 scripts/mmc.py` la abre en el navegador, servida desde `127.0.0.1`.
   - (b) Una interfaz de terminal.
   - (c) Una página alojada fuera.
   - (d) Una extensión de editor.

   **Rec.:** (a), con Python estándar y una sola página HTML con JS sin compilar: sin npm, sin servidor externo y en
   cualquier sistema.
2. **Datos separados de la interfaz** (idea de OpenHands): **Rec.:**
   - El MMC no calcula nada: pide los datos a los scripts del flujo (`config.py`, `metrics.py`, `trace.py`,
     `questions.py`…) en JSON.
   - Así, lo que ves en el MMC es lo mismo que obtiene un agente o el CI.
   - El MMC declara la versión mínima del flujo que necesita.
3. **En la nube:** el `127.0.0.1` del contenedor no se abre desde tu navegador. **Rec.:** `mmc.py --static` genera un
   único HTML de solo lectura, con los datos del momento, que se puede abrir o publicar.
4. **Cómo guarda los cambios de configuración:** **Rec.:**
   - Escribe solo a través de `config.py`: un dato, un sitio.
   - Te enseña el diff antes de guardar.
   - No hace commit: el cambio queda en la rama como cualquier otro, y pasa por los ganchos.
5. **Perfiles:** **Rec.:** capas, y cada una pisa a la anterior:
   1. los valores por defecto del flujo (el perfil global);
   2. el `gw.json` del proyecto (el privado);
   3. el perfil guardado activo (`.claude/gw-profiles/<nombre>.json`);
   4. el archivo local que no se sube (`gw.local.json`, E-2).

   El MMC muestra de qué capa sale cada valor, y alterna perfiles con un clic.
6. **Qué datos muestra:** **Rec.:**
   - gasto por día, modelo, subagente y tarea, con los informes y las comparaciones (B);
   - avisos de gasto anómalo y modelos desactivados (B4);
   - medidas de `opt-tokens` por PR y retros;
   - preguntas abiertas (C);
   - la ficha de cada tarea con `trace.py` (D-14);
   - el estado del roadmap.
7. **Git:** **Rec.:** árbol de ramas, entornos (D-9), etiquetas y releases, y el estado del check y del CI, todo de
   solo lectura. Fusionar, subir a `main` o crear una release siguen siendo acciones de la sesión, con tu confirmación
   y los ganchos. El MMC no se salta las tres fases.
8. **Entornos y roles** (D-9, D-17): **Rec.:**
   - El MMC edita la lista de entornos (añadir, quitar, qué rama, qué rol) y las cuentas de GitHub de cada rol.
   - El gancho `pre-push` comprueba que el usuario de git puede subir a ese entorno.
   - El control fuerte lo da la protección de ramas de GitHub. El MMC dice cómo configurarla; no la toca, porque
     necesitaría la API.
9. **Por fases:** **Rec.:**
   - MMC 1: panel de solo lectura (datos y git).
   - MMC 2: edición de la configuración y de los modos.
   - MMC 3: perfiles, entornos y roles.

   Cada fase, en una menor `1.x`; el reparto lo hace el bloque H.
10. **Un proyecto o varios:** **Rec.:** primero, un MMC por proyecto. Después, una vista que reúna los proyectos que
    usan el flujo, con la lista de `gw-harvest`. Los repos privados (A-2) solo se ven en local.
