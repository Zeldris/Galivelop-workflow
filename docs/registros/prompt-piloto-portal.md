# Prompt del piloto en Portal-Galivelop (Fase 5)

Para pegar en una sesión abierta con **Portal-Galivelop como carpeta de trabajo** (sin registrar Galivelop-workflow
como raíz de la sesión).

```text
Vas a aplicar Galivelop-workflow v0.1.0 a este repo (Portal-Galivelop) como piloto: es la Fase 5 del plan del flujo.
Tienes mi permiso para modificar este repo en una rama nueva, claude/piloto-galivelop-workflow. A main, solo con mi
confirmación y siguiendo las tres fases del flujo.

1. Clona https://github.com/Zeldris/Galivelop-workflow (etiqueta v0.1.0) en /home/user/Galivelop-workflow, solo para
   leer. No lo registres como raíz de la sesión: sus skills taparían las de este repo.
2. Sigue paso a paso /home/user/Galivelop-workflow/docs/es/aplicar.md (es el «proyecto existente»).
3. Lo propio del portal:
   - sube directo a main (pushToProtected: direct);
   - install «npm ci», check «npm run check»;
   - textos visibles en es, gl y en (visibleLanguages);
   - la bitácora es docs/traspaso.md;
   - la marca ya vive en docs/registros/revisado.txt;
   - la tarea programada semanal sube la rama de trabajo a main sin confirmación y tiene que seguir funcionando
     (con la marca cubriendo el código).
4. Sustituye la copia actual del flujo (.claude/skills, .claude/hooks, .claude/settings.json, tools/qa, .githooks)
   por la de Galivelop-workflow. Lo que el portal tenga propio y el flujo no traiga, se queda. Lo duplicado se quita
   solo tras comprobar que el flujo hace lo mismo. Los *.gw-nuevo se revisan conmigo.
5. Hecho cuando: «npm run check» en verde; el pre-push y la marca de revisado funcionan (prueba del paso 6 de
   aplicar.md); doctor.py sin FAIL; la tarea semanal sin cambios de comportamiento.
6. Apunta cada fricción, fallo o cosa que le falte al flujo en docs/registros/piloto-galivelop-workflow.md, con una
   sección «## For Galivelop-workflow» para que gw-harvest la recoja desde el repo del flujo.
7. Commit + push en cada punto estable, con la bitácora al día. Al acabar, dime qué ha quedado y qué falta.
```
