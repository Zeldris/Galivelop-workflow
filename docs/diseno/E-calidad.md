# E. Reglas deterministas, pruebas de front, documentación

**Estado:** cerrado (2026-11-01): las 8 preguntas, aprobadas por el usuario según la recomendación del agente. La
investigación de la 5 ya está hecha; sus preguntas, de la 9 a la 16, siguen abiertas.

Fuentes: [`README.md`](README.md) (bloque E), A-1 de [`A-marco.md`](A-marco.md) (todo público), D-3 y D-8 de
[`D-git.md`](D-git.md) (recogidas publicadas, perfiles de instalación).

El principio: lo que se puede controlar de forma determinista sale del razonamiento del modelo y vive en un check.

## Preguntas (se responden por número)

Cada punto lleva la recomendación del agente (**Rec.**).

1. **`AGENTS.md` y `CLAUDE.md` limpios:** **Rec.:** una auditoría en la `1.0.0`. Cada línea de `AGENTS.md` queda en
   uno de estos tres casos:
   - apunta al check que la hace cumplir, y se acorta a una línea;
   - es de criterio, y se queda;
   - sobra, y se borra.

   Además, un check pone un tope de líneas a los dos archivos, configurable, para que no vuelvan a crecer sin
   control.
2. **Check de datos privados** (A-1): antes de subir, busca correos, claves y nombres de repos privados en lo que se va
   a publicar. Problema: si la lista de nombres privados está en el repo, ya los publica. **Rec.:** la lista va en un
   archivo local que no se sube (`.claude/gw.local.json`), y el gancho `pre-push` la usa; el CI solo busca claves y
   correos. Tu correo queda permitido (D-2).
3. **Las recogidas publicadas** que nombran proyectos privados (D-3): **Rec.:** se anonimizan (`private-project-1`).
   El contenido general se conserva y lo que es propio de cada proyecto se quita. No se borran, porque
   `version.py --release` y la historia de las versiones las citan.
4. **Perfiles de instalación** (D-8): **Rec.:** en una `1.x`, como opción de `gw-init` y `gw-update`.
   - `minimal`: los ganchos, la bitácora y el check.
   - `core`: lo de `minimal` más `selector`, `orchestrate-dealer`, `retro`, `opt-tokens` y `pr`.
   - `full`: todo, incluidas las skills de mattpocock, las de redes y `gw-harvest`.

   Por defecto, `core`.
5. **Pruebas de front:** hoy todo depende de Playwright. **Rec.:** antes de decidir, una investigación como la del
   bloque F, con un subagente y fuentes oficiales, sobre herramientas para cada aspecto:
   - arquitectura de estilos (Stylelint y sus reglas de tokens);
   - regresión visual (capturas de Playwright, BackstopJS, Lost Pixel);
   - responsive y adaptative (una matriz de viewports y dispositivos);
   - animaciones y transiciones (`reducedMotion`, `document.getAnimations()`);
   - accesibilidad (axe-core).

   Se lanza ahora, mientras diseñamos G, y vuelve con sus propias preguntas.
6. **De norma escrita a regla aplicada:** **Rec.:** el patrón vale para todo, no solo para el front. Cada regla de
   `REVIEW.md` o de las normas de front de un proyecto dice qué check la hace cumplir, o «criterio» si no lo hay. Un
   script lista las reglas mecánicas que aún no tienen check, y la `retro` las propone como checks.
7. **Dónde viven las pruebas de front:** este repo no tiene front. **Rec.:** el flujo da una guía en `docs/es/patrones.md`
   (y su par en inglés) y una plantilla de config que los proyectos con front (Portal-Galivelop, World-Maker-Fantasy)
   activan; no hay una skill nueva hasta que haga falta.
8. **Revisión completa de la documentación:** **Rec.:** una pasada al final de la `1.0.0`, después de los cambios de
   nombres y rutas (A-2 y A-4), que tocan casi todos los documentos. Se reparte a subagentes, un documento cada uno,
   con una lista fija: público, sin basura, coherente con el código, ES y EN emparejados. La sesión principal revisa
   cada resultado.

## Preguntas de la investigación de front (E-5)

Salen de [`ref-pruebas-front.md`](../investigacion/ref-pruebas-front.md). Algunos dominios no resolvían desde el
entorno; lo no confirmado va marcado `[NC]` en la nota, y se trata como en D-5. Cada punto lleva la recomendación del
investigador (**Rec.**).

9. **Capturas visuales:** ¿se generan y comparan solo en Docker o Linux, en local y en el CI, o se acepta una base por
   cada sistema? **Rec.:** solo en Docker o Linux. En macOS, la prueba visual corre en Docker o se omite con un aviso.
10. **Cuándo corre la prueba visual:** ¿en el `pre-push` o solo en el CI y antes de `main`? **Rec.:** solo en el CI y en
    la fase de cierre. El `pre-push` lleva Stylelint, las pruebas de layout y axe.
11. **Dónde viven los tokens y breakpoints de cada proyecto:** **Rec.:** en un JSON enlazado desde `gw.json`. De él se
    generan las reglas de Stylelint y los viewports.
12. **Preprocesadores:** **Rec.:** CSS y SCSS desde el principio. Less o CSS-in-JS solo si un proyecto real lo exige.
13. **Accesibilidad:** **Rec.:** axe bloquea por defecto (ninguna violación grave o crítica). Lighthouse CI solo
    informa.
14. **Dónde se guardan las capturas de referencia:** **Rec.:** en git mientras sean pocas y pequeñas, y en Git LFS si
    pasan de un umbral que fija el flujo.
15. **Servicios de pago** (Percy, Chromatic, Lost Pixel Platform): **Rec.:** no. El flujo funciona sin cuentas externas.
16. **Matriz mínima:** **Rec.:** Chromium en todos los breakpoints. WebKit y Firefox solo en el escritorio y el móvil
    principales.

**Respuestas del usuario (2026-11-01):** E-9..E-16 aprobadas según la recomendación. El bloque E queda cerrado.
