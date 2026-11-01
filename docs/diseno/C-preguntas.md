# C. Preguntas y modo restrictivo

**Estado:** preguntas abiertas (2026-11-01). Nada se implementa hasta cerrar el bloque.

Fuentes: [`README.md`](README.md) (bloque C), B-10 de [`B-medicion.md`](B-medicion.md) (un solo interruptor de
modos) y `/careful` y `/freeze` de gstack en [`ref-thinkrail-gstack-ecc.md`](../investigacion/ref-thinkrail-gstack-ecc.md).

El problema: se lanza una pregunta, el agente sigue a lo suyo, la respuesta no llega y las preguntas se repiten en
cada iteración. El concepto del flujo es resolver las dudas antes de desarrollar, guiando y nunca imponiendo.

## Preguntas (se responden por número)

Cada punto lleva la recomendación del agente (**Rec.**).

1. **Dónde viven las preguntas:** **Rec.:** en un archivo propio, `docs/questions.md` (en inglés según A-4). Cada
   pregunta lleva:
   - un id (`Q-12`), la tarea de la que sale (`Refs: B4`, de D-12) y el estado (abierta, respondida, riesgo aceptado);
   - la recomendación, y después la respuesta con su fecha.

   La bitácora solo dice cuántas quedan abiertas. Así `trace.py` (D-14) las encuentra.
2. **Cómo se preguntan:** **Rec.:** como en esta sesión: una lista numerada, cada punto con su recomendación, y el
   usuario responde por número («5. a, 6. ok»). Así lo dice una regla corta en `AGENTS.md`, y un script pasa las
   respuestas al archivo. `to-questionnaire` sigue igual: sirve para preguntas que tiene que contestar otra persona.
3. **Sin repetir:** **Rec.:**
   - Las preguntas abiertas se muestran enteras una sola vez, al plantearlas.
   - Después, el gancho de inicio y el agente solo dicen: «Hay X preguntas por responder (`docs/questions.md`)».
   - La lista vuelve a salir entera cuando la pides o cuando se añaden preguntas nuevas.
4. **Modo restrictivo activo:** **Rec.:**
   - Un gancho rechaza editar código mientras la tarea en curso tenga preguntas abiertas que la bloqueen, y dice
     cuáles.
   - La documentación y lo que casa con `content` de `gw.json` sí se puede editar, porque escribir el diseño no es
     implementar.
   - Las preguntas de otras tareas no bloquean.
5. **Modo restrictivo inactivo:** **Rec.:**
   - Al ir a implementar con preguntas abiertas, el agente avisa y recomienda contestarlas.
   - Si decides seguir, la pregunta pasa a «riesgo aceptado», con la fecha, y deja de avisar.
6. **Valor por defecto:** **Rec.:** inactivo en los proyectos («se guía, no se impone») y activo en este repo, que se
   trabaja con su propio flujo y diseña antes de implementar.
7. **Un solo interruptor:** **Rec.:**
   - Una skill, `gw-mode`, cambia todos los modos, con un script que escribe en `gw.json`.
   - Cada modo es independiente: `modes.questions` (restrictivo o no) y `modes.tokens` (restringido o no, de B-10).
   - El gancho de inicio dice qué modos están activos.
8. **`/careful` de gstack:** antes de una orden destructiva (`rm -rf`, `git push --force`, `git reset --hard`, borrar
   una rama), pide confirmación. **Rec.:** sí, como `modes.careful`, activo por defecto; es un gancho barato.
9. **`/freeze` de gstack:** limita las ediciones a una carpeta. **Rec.:** como `modes.freeze <carpeta>` en una `1.x`.
   Sirve para que un subagente no se salga de su encargo.
10. **Preguntas de un subagente:** **Rec.:** un subagente nunca pregunta al usuario. Para, devuelve la pregunta a la
    sesión principal y esta la apunta en `docs/questions.md`, en el formato de la 2.
