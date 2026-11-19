# Questions

Questions for the user, one entry each; `python3 .claude/gw/scripts/questions.py` reads and rewrites this
file (format: header of scripts/questions.py). Answer by number: `questions.py answer "5. a, 6. ok"`.

## Q-1
- Refs: B9
- Status: answered
- Asked: 2026-11-18
- Question: ¿De qué tamaño es B9 en la 0.8?
- Recommendation: a) mínimo: los modelos de fuera de Anthropic entran como dato en la tabla y una guía corta de uso con opencode; leer su gasto, en la 1.x
- Answer: a
- Answered: 2026-11-18

## Q-2
- Refs: H23
- Status: answered
- Asked: 2026-11-18
- Question: ¿Hace falta una recogida nueva para la 0.8?
- Recommendation: ver si una recogida del 11-15 de noviembre cuenta para la 0.8; si no, una recogida corta
- Answer: ok
- Answered: 2026-11-18

## Q-3
- Refs: E33
- Status: answered
- Asked: 2026-11-18
- Question: ¿Crear un REVIEW.md en la raíz del repo?
- Recommendation: no: el flujo lee la plantilla instalada; dos copias se desincronizan
- Answer: ok
- Answered: 2026-11-18

## Q-4
- Refs: D142
- Status: open
- Asked: 2026-11-19
- Question: D142, al parar por modelo o esfuerzo distinto: a) en los dos sentidos (bajar para ahorrar, subir por calidad); b) solo para bajar; c) avisar y seguir
- Recommendation: a

## Q-5
- Refs: D142
- Status: open
- Asked: 2026-11-19
- Question: D142, orquestador: la sesión toma el modelo del trabajo que hace ella misma (planear, decidir, revisar; suele ser Sonnet medium) y solo pide Opus para diseño o causas nada obvias
- Recommendation: sí

## Q-6
- Refs: D142
- Status: open
- Asked: 2026-11-19
- Question: D142: el gancho de inicio compara el modelo recomendado con el del transcript y avisa, en la misma tarea
- Recommendation: sí
