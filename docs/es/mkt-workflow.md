# Cómo trabaja Galivelop con agentes de IA

[English](../en/mkt-workflow.md)

Galivelop desarrolla software con agentes de programación (Claude Code) siguiendo **Galivelop-workflow**: un método
propio, público y versionado, en el que las reglas no dependen de la buena voluntad del agente, sino de
**comprobaciones automáticas que las hacen cumplir**.

## Qué resuelve para tu proyecto

- **Continuidad.** Una sesión de IA puede cortarse en cualquier momento; el trabajo no se pierde. Todo se sube al
  repositorio en cada punto estable, con una bitácora que dice dónde va y qué sigue.
- **Calidad.** Nada llega a la versión publicada sin revisión del código, tests en verde y tu confirmación.
- **Coste controlado.** Cada tarea usa el modelo de IA que pide, y el gasto se mide en lugar de suponerse.
- **Trazabilidad.** Cada cambio se puede seguir desde la tarea del plan hasta el commit que la hizo.

## Cómo se trabaja

1. **Plan y tareas.** El trabajo se reparte en tareas con un identificador, en un plan que tú puedes leer.
2. **Desarrollo en una rama.** El agente trabaja fuera de la versión publicada y sube su trabajo a menudo, con la
   bitácora al día en el mismo commit.
3. **Comprobación continua.** Cada subida pasa el check del proyecto (tests, formato, datos privados) sobre el
   código exacto que se sube.
4. **Revisión antes de publicar.** Revisión del código, repaso del proceso y marca de revisión atada a ese código.
5. **Publicación con tu visto bueno.** La versión publicada solo cambia cuando tú lo confirmas.

## Qué garantiza, y cómo

| Garantía | Qué la hace cumplir |
|---|---|
| Nada se pierde entre sesiones | Subida constante; un gancho no deja cerrar la sesión con trabajo sin subir |
| Nada sin revisar se publica | Marca de revisión atada al commit; sin ella, la subida se rechaza |
| Los tests prueban algo de verdad | Un test nuevo tiene que fallar sin su arreglo |
| No se filtran claves ni datos privados | Comprobación de secretos en cada commit y en cada subida |
| Un CI que no arranca no cuenta como verde | Se trata como rojo y se te avisa |
| Cada cambio es trazable | Formato de commit con el id de la tarea y el siguiente paso |

## Lo que recibes

Tu repositorio, con todo el historial y la bitácora; el plan con el estado de cada tarea; y cada versión con su
lista de cambios. El método es público: puedes revisarlo en
[github.com/Zeldris/Galivelop-workflow](https://github.com/Zeldris/Galivelop-workflow).
