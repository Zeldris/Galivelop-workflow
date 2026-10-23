<!-- galivelop-workflow v0.3.0 -->
# Bitácora (traspaso)

> Léela entera al empezar cualquier sesión. Lo que no está subido no existe: commit + push en cada punto estable,
> con esta bitácora actualizada en el mismo commit. El flujo nunca la sobrescribe una vez creada.

## Estado actual

| Campo | Valor |
|---|---|
| **Rama** | _(rama de trabajo)_ |
| **Fase / tarea** | _(fase y tarea en curso)_ |
| **Último punto estable** | _(último commit con el check en verde, y qué trajo)_ |
| **Siguiente paso** | _(el próximo paso concreto, para que la siguiente sesión no tenga que preguntar nada)_ |
| **Check** | {{check}}: _(verde / rojo, y qué falla)_ |

Con `logRows` en `.claude/gw.json`, cada rama escribe solo en su fila de esta tabla, como mucho 600 caracteres, con
la forma ``| **Tarea en curso · `<rama>`** | tarea, qué falta y siguiente paso |``; el push lo comprueba.

## Para la próxima publicación

_(lo que va a `{{protectedBranch}}` a continuación, y a qué espera)_

## Hecho (5 últimas)

1. _(fecha — qué se cerró, en dos líneas como mucho: el detalle está en el commit; la más antigua sale cuando hay más
   de 5, el historial está en git)_

## Pendiente

- _(decisiones de la persona que bloquean algo, problemas conocidos, ideas sin planificar)_

## Comprobar el estado

- Últimos commits: `git fetch origin <rama> && git log --oneline -5 origin/<rama>`.
- El check: {{check}}.
- Flujo bien montado: `python3 .claude/gw/scripts/doctor.py`.
- Estado de la bitácora tal como lo recibe una sesión nueva: `python3 .claude/gw/scripts/recuperar.py --estado`.
