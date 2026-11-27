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
- Status: answered
- Asked: 2026-11-19
- Question: D142, al parar por modelo o esfuerzo distinto: a) en los dos sentidos (bajar para ahorrar, subir por calidad); b) solo para bajar; c) avisar y seguir
- Recommendation: a
- Answer: a
- Answered: 2026-11-22

## Q-5
- Refs: D142
- Status: answered
- Asked: 2026-11-19
- Question: D142, orquestador: la sesión toma el modelo del trabajo que hace ella misma (planear, decidir, revisar; suele ser Sonnet medium) y solo pide Opus para diseño o causas nada obvias
- Recommendation: sí
- Answer: sí, pero teniendo siempre en cuenta las métricas de los modelos (metrics.py): quién ha funcionado mejor en cada caso o ha dado mejor calidad/coste
- Answered: 2026-11-22

## Q-6
- Refs: D142
- Status: answered
- Asked: 2026-11-19
- Question: D142: el gancho de inicio compara el modelo recomendado con el del transcript y avisa, en la misma tarea
- Recommendation: sí
- Answer: sí
- Answered: 2026-11-22

## Q-7
- Refs: D142
- Status: answered
- Asked: 2026-11-22
- Question: D142 (Q-6): ¿el aviso de modelo distinto del gancho de inicio salta también tras una compactación (matcher «compact» de SessionStart)? Hoy solo al arrancar, reanudar o tras /clear, y tras /clear el transcript es nuevo y no avisa
- Recommendation: sí: el aviso salta también tras una compactación, dentro de la misma tarea
- Answer: ok
- Answered: 2026-11-23

## Q-8
- Refs: D142
- Status: answered
- Asked: 2026-11-22
- Question: D142 (Q-6): ¿además, un aviso en cada mensaje del usuario (gancho UserPromptSubmit) mientras no cambie de modelo?
- Recommendation: no: ruido y coste en cada turno; basta con el inicio, la compactación y la regla de la skill
- Answer: ok
- Answered: 2026-11-23

## Q-9
- Refs: E77
- Status: answered
- Asked: 2026-11-19
- Question: ¿Regla general: push y check largo en segundo plano con timeout de 5400000 ms (90 min), no solo en los commits de sello?
- Recommendation: sí, una línea en «Relevos» de AGENTS.md y la nota de gw-opt-tokens.md para cualquier subida
- Answer: ok
- Answered: 2026-11-19

## Q-10
- Refs: E77
- Status: answered
- Asked: 2026-11-19
- Question: ¿Que push.sh diga el alcance (completo o relacionado) y cuánto tardó la última vez antes de empezar?
- Recommendation: no por ahora; con la regla 1 deja de importar
- Answer: no
- Answered: 2026-11-19

## Q-11
- Refs: E77
- Status: answered
- Asked: 2026-11-19
- Question: ¿La subida final de los subagentes de gw-orchestrate-dealer pasa de primer plano con 600000 ms a segundo plano con 90 min?
- Recommendation: sí, segundo plano con 90 min, en la misma tarea
- Answer: ok
- Answered: 2026-11-19

## Q-12
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12, alcance: a) una sola ficha repartida en trozos; b) partir el idioma del agente por usuario en otra tarea con Related:
- Recommendation: a: una ficha A12, repartida en 3 trozos (esquema y lectura en config.py con migración; consumidores; idioma del agente)
- Answer: a
- Answered: 2026-11-20

## Q-13
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12, forma del bloque languages en este repo (código en inglés; doc interna es+en; README y releases públicos en+es; ui vacío)
- Recommendation: sí: {"code":"en","docs":{"primary":"es","others":["en"]},"public":{"primary":"en","others":["es"]},"ui":[]}, códigos ISO 639-1
- Answer: ok
- Answered: 2026-11-20

## Q-14
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12, migración: a) apply.py --update migra y config.py acepta las claves viejas como respaldo con aviso; b) migración y sin respaldo (falla cerrado)
- Recommendation: a: apply.py --update migra (language → docs.primary y public.primary; visibleLanguages → ui; code = en) y config.py sigue leyendo las claves viejas si falta el bloque, con aviso de doctor.py
- Answer: a
- Answered: 2026-11-20

## Q-15
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12, plantillas de un idioma sin carpeta en templates/ (p. ej. gl): a) usar en y avisar; b) fallar cerrado
- Recommendation: a: plantillas por docs.primary; si no hay plantillas en ese idioma, las de en y aviso de doctor.py
- Answer: a
- Answered: 2026-11-20

## Q-16
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12: ¿el idioma de commits y textos generados por los scripts sale de docs.primary?
- Recommendation: sí: commits (trailer Siguiente/Next), bitácora, roadmap y textos de handoff.py/merge-main.py/task.py siguen a docs.primary
- Answer: sí
- Answered: 2026-11-20

## Q-17
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12, names-check con code distinto de en: a) se salta y lo dice; b) se generaliza a cualquier par de idiomas (más trabajo)
- Recommendation: a: names-check.py solo comprueba cuando code es en (hoy solo detecta nombres en español); con otro valor, lo salta y lo dice
- Answer: a
- Answered: 2026-11-20

## Q-18
- Refs: A12
- Status: answered
- Asked: 2026-11-20
- Question: A12, idioma del agente por usuario en ~/.claude/gw.json por email, anunciado por el gancho de inicio
- Recommendation: sí: ~/.claude/gw.json {"agentLanguage": {"<email>": "es"}}; el gancho SessionStart imprime 'Agent language: es' (respaldo: docs.primary); CLAUDE.md deja de fijar el idioma
- Answer: sí
- Answered: 2026-11-20

## Q-19
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4, alcance: ¿los perfiles solo eligen skills y agentes (a) o también ganchos (b)?
- Recommendation: a: los perfiles solo deciden qué skills y agentes se instalan; ganchos, scripts, plantillas y bitácora van siempre
- Answer: superada por Q-25 a Q-30 (perfiles por persona y cargo)
- Answered: 2026-11-20

## Q-20
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4, reparto de skills por perfil (el diseño solo nombraba algunas)
- Recommendation: minimal = gw-init, gw-update, gw-doctor y gw-mode; core = minimal + gw-selector, gw-orchestrate-dealer, retro, gw-opt-tokens, pr, gw-metrics, diagnosing-bugs, grilling, domain-modeling, writing-for-agents y los agentes gw-worker y gw-reviewer; full = todo lo demás (resto de mattpocock, gw-media-content(-now), gw-opt-ai, gw-scout-updates); gw-harvest sigue solo en el repo del flujo
- Answer: superada por Q-25 a Q-30 (perfiles por persona y cargo)
- Answered: 2026-11-20

## Q-21
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4, dónde vive el perfil
- Recommendation: clave install.profile en .claude/gw.json (defecto core), --profile en apply.py la escribe, --with suma skills sueltas encima
- Answer: superada por Q-25 a Q-30 (perfiles por persona y cargo)
- Answered: 2026-11-20

## Q-22
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4, proyectos ya instalados al actualizar
- Recommendation: un proyecto sin la clave conserva todo lo que tiene (no se borra nada); bajar de perfil a propósito quita solo las copias del flujo sin tocar, y gw-update lo presenta como decisión antes de --update
- Answer: superada por Q-25 a Q-30 (perfiles por persona y cargo)
- Answered: 2026-11-20

## Q-23
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4, plantillas que nombran skills ausentes
- Recommendation: las plantillas de AGENTS.md/CLAUDE.md quitan las líneas de skills no instaladas (gw-selector en minimal) con una marca por skill
- Answer: superada por Q-25 a Q-30 (perfiles por persona y cargo)
- Answered: 2026-11-20

## Q-24
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4, perfil de este repo (el flujo)
- Recommendation: full
- Answer: superada por Q-25 a Q-30 (perfiles por persona y cargo)
- Answered: 2026-11-20

## Q-25
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4: ¿los perfiles de persona y de cargo se suman por capas o se sustituyen?
- Recommendation: por capas: default → cargo → propio
- Answer: ok
- Answered: 2026-11-20

## Q-26
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4: ¿dónde se guardan las asignaciones correo→cargo/perfil y cargo→perfil?
- Recommendation: en .claude/gw.json
- Answer: ok
- Answered: 2026-11-20

## Q-27
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4: privacidad de los correos en un repo público
- Recommendation: hash del correo, no el correo
- Answer: ok
- Answered: 2026-11-20

## Q-28
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4: ¿qué obligaciones puede saltarse un perfil?
- Recommendation: cualquier clave, pero el CI siempre corre con default
- Answer: ok
- Answered: 2026-11-20

## Q-29
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4: el correo de git se falsifica y los ganchos se saltan con --no-verify; ¿se acepta?
- Recommendation: aceptado: comodidad, no control de acceso
- Answer: ok
- Answered: 2026-11-20

## Q-30
- Refs: E4
- Status: answered
- Asked: 2026-11-20
- Question: E4: ¿cómo se manejan los perfiles hasta que exista el MMC?
- Recommendation: profile.py list|new|assign|role|show; el MMC (G4) usará las mismas órdenes
- Answer: ok
- Answered: 2026-11-20

## Q-31
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: E5, alcance: los tres trozos de la ficha (dato y generador; plantillas con fixture stable() y helpers de layout; perfiles fast/full y avisos de doctor.py), con E7 (guía y plantilla de config) aparte
- Recommendation: sí; E9-E16 quedan como decisiones aplicadas dentro de E5 y se marcan hechas con ella
- Answer: Si
- Answered: 2026-11-21

## Q-32
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: E5, formato del JSON de tokens y breakpoints: a) subconjunto W3C Design Tokens ($value, $type); b) formato propio plano (colors, spacing, fontSizes, breakpoints)
- Recommendation: a, para que un proyecto con Style Dictionary lo reutilice
- Answer: a
- Answered: 2026-11-21

## Q-33
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: E5, lenguaje de las plantillas (playwright.config, fixture, helpers): a) TypeScript; b) JavaScript
- Recommendation: a, el defecto de Playwright
- Answer: a
- Answered: 2026-11-21

## Q-34
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: E5, cómo se prueba aquí, que no tiene front: a) proyecto de ejemplo en tests/fixtures/front-sample que el check corre con node y Playwright en Linux (sin node o en macOS, se omite con aviso); b) solo tests en Python del generador
- Recommendation: a; el generador lleva además tests en Python siempre
- Answer: ok
- Answered: 2026-11-21

## Q-35
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: E5, reglas de Stylelint generadas: ¿qué propiedades se limitan a tokens y con qué plugin?
- Recommendation: stylelint-declaration-strict-value para colores, espaciados y tamaños de letra; versiones de Stylelint, Playwright y axe fijadas en la plantilla
- Answer: ok
- Answered: 2026-11-21

## Q-36
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: ¿front.py escribe el sello de versión de Playwright de las capturas (run full --update-snapshots) en vez de a mano?
- Recommendation: sí, en otra tarea
- Answer: Si 35. Si
- Answered: 2026-11-21

## Q-37
- Refs: E5, E7
- Status: answered
- Asked: 2026-11-21
- Question: ¿La plantilla de CI de los proyectos corre front.py run full dentro de E7?
- Recommendation: sí, en E7
- Answer: Si
- Answered: 2026-11-21

## Q-38
- Refs: E5
- Status: answered
- Asked: 2026-11-21
- Question: front.py solo enlaza node_modules en front.dir: si front.dir importa la plantilla desde fuera, @playwright/test no se resuelve. ¿Lo documentamos o se enlaza también en la raíz de la copia?
- Recommendation: documentarlo en templates/front/README.md: la plantilla se copia dentro de front.dir
- Answer: lo recomendado (documentarlo en templates/front/README.md)
- Answered: 2026-11-21

## Q-39
- Refs: D177
- Status: answered
- Asked: 2026-11-23
- Question: D177 está apagado en este repo (pendingClosedIdCheck=false) por unos 60 falsos avisos de pending.md: ¿ampliar la excepción y encenderlo, limpiar pending.md, o dejarlo apagado?
- Recommendation: ampliar la excepción de D177 a ids dentro de «Revisión …» o de un paréntesis «(B42, …)» y encender la clave; la alternativa, dejarla apagada aquí, hace que el aviso no proteja al propio flujo
- Answer: ok, Q-7. ok, Q-8. ok
- Answered: 2026-11-23

## Q-40
- Refs: D180
- Status: answered
- Asked: 2026-11-26
- Question: D180: con wholeReadDenyPaths configurado, ¿whole-read.py rechaza lo que no entiende (comando que no sabe partir, limit enorme, claves / o ../) en vez de dejarlo pasar? a) rechazar (falla cerrado solo para rutas denegadas); b) dejar pasar y documentarlo como límite
- Recommendation: a) sí: con wholeReadDenyPaths configurado, un comando que no se sabe partir y nombra una ruta denegada se rechaza, un limit por encima del tamaño del archivo cuenta como lectura entera, y config.py validate rechaza claves como / o ../
- Answer: a
- Answered: 2026-11-26

## Q-41
- Refs: B43
- Status: open
- Asked: 2026-11-26
- Question: B43: ¿qué sección de la ficha cuenta como aceptación en trace.py? a) Acceptance o la tercera de sections; b) una clave nueva en gw.json
- Recommendation: a) Acceptance si está en taskRecord.sections; si no, la tercera

## Q-42
- Refs: B43
- Status: open
- Asked: 2026-11-26
- Question: B43: contract_errors y entry_text de task.py siguen fijando Acceptance; ¿se apunta como leve de la 0.10?
- Recommendation: apuntarlo como leve 0.10 en pending.md, fuera de B43

## Q-43
- Refs: E28
- Status: answered
- Asked: 2026-11-27
- Question: E28: ¿se arreglan ya las inyecciones de opciones, los enlaces simbólicos, el token de release.yml, persist-credentials y el .gitignore? a) sí; b) solo los medios
- Recommendation: a) arreglar A1, B1-B4, C1, C2 y C4 en esta tarea, con tests
- Answer: a
- Answered: 2026-11-27

## Q-44
- Refs: E28
- Status: answered
- Asked: 2026-11-27
- Question: E28 C3: ¿acciones de CI fijadas por SHA (también en la plantilla) o por etiqueta? a) SHA; b) etiqueta, apuntado
- Recommendation: a) fijar por SHA con comentario de versión
- Answer: a
- Answered: 2026-11-27

## Q-45
- Refs: E28
- Status: answered
- Asked: 2026-11-27
- Question: E28 D: ¿qué modelo de confianza para el repo abierto? a) de confianza, documentado, con los arreglos baratos; b) no confiable: pedir permiso antes de D1/D2 y todo D
- Recommendation: a) el repo abierto es de confianza (como make o npm); se documenta y se arreglan los baratos: D4 entorno mínimo, D5 usar is-code.sh del flujo, D3 --ignore-scripts; D1, D2, D6 y D7 quedan documentados
- Answer: a
- Answered: 2026-11-27

## Q-46
- Refs: E28
- Status: answered
- Asked: 2026-11-27
- Question: E28 E: ¿hasta dónde se endurecen careful.py y review-before-main.sh? a) los baratos y preguntar ante sustituciones; b) todo E3; c) solo documentar
- Recommendation: a) arreglar E1, E2 y E4 (gh pr edit --base, gh alias, graphql, gh api/curl a pulls) y que una sustitución $(…) o comilla invertida junto a git/gh/rm pida confirmación; documentar el resto como límite
- Answer: a
- Answered: 2026-11-27

## Q-47
- Refs: E28
- Status: answered
- Asked: 2026-11-27
- Question: E28 F: ¿los leves a pending.md? a) sí, menos F5 y F6; b) arreglarlos ya
- Recommendation: a) F1-F4 y E5 a pending.md como leves de la 0.10; F5 y F6, no
- Answer: a
- Answered: 2026-11-27

## Q-48
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 A1 (docs/records/anonymization-review-E29.md): N5 se apuntó como privado y sigue con su nombre en 25 archivos de main. a) alias private-project-N; b) ya es público, se acepta
- Recommendation: a) alias private-project-N en esta rama
- Answer: a
- Answered: 2026-11-27

## Q-49
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 A2: N6 (47 sitios, recogida del 2026-10-25) ¿es privado? a) privado, alias; b) público, se acepta
- Recommendation: a) si es privado, alias como A1; dime cuál
- Answer: a
- Answered: 2026-11-27

## Q-50
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 A3, B1, B2: N1-N5 en el historial de main y en 6 ramas viejas, 140 commits con enlaces de sesión y 3 con tu nombre completo. a) no reescribir main y borrar las ramas viejas; b) reescribir todo el historial con git filter-repo y forzar main (rompe clones y etiquetas); c) nada
- Recommendation: a) no reescribir main (rompe clones, etiquetas, releases e instalaciones, y GitHub guarda copias igual); borrar las 6 ramas viejas que aún los llevan en su árbol, tras confirmar que ninguna tiene trabajo vivo
- Answer: a
- Answered: 2026-11-27

## Q-51
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 C1: en la nube no hay gw.local.json y los nombres nunca se miran. a) variable GW_PRIVATE_NAMES en el entorno de la nube + fallo cerrado al subir a main y al recoger sin lista; b) solo fallo cerrado; c) lista con hash pública
- Recommendation: a) GW_PRIVATE_NAMES como segunda fuente y fallo cerrado en la rama protegida y en harvest
- Answer: a
- Answered: 2026-11-27

## Q-52
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 C2, C3: a) detectar enlaces de sesión, rutas personales e IP privadas (privateCheck.patterns) y revisar etiquetas en pre-push; b) solo enlaces de sesión; c) nada
- Recommendation: a) los tres patrones por defecto y revisar etiquetas y nombres de ref
- Answer: a
- Answered: 2026-11-27

## Q-53
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 C4: la marca gw-allow-private salta todo en la línea. a) acotarla a contenido y contarla; b) quitarla; c) dejarla
- Recommendation: a) sin efecto en rutas ni mensajes y recuento en --all
- Answer: a
- Answered: 2026-11-27

## Q-54
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 C5: git@ y noreply@ se admiten con cualquier dominio. a) acotar git@; b) dejarlo
- Recommendation: a) git@ solo con forma git@host:ruta; noreply@ se queda
- Answer: a
- Answered: 2026-11-27

## Q-55
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 B3: tu correo está en allowEmails (público). a) se queda; b) pasarlo a gw.local.json y usar el noreply de GitHub en adelante
- Recommendation: a) se queda: ya es público en el autor de todos los commits
- Answer: a
- Answered: 2026-11-27

## Q-56
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 A4: pistas débiles en las recogidas con alias (nombres de retro, stack). a) aceptar y anonimizar los nombres de retro en adelante; b) limpiar también las ya publicadas; c) nada
- Recommendation: a) aceptar y que harvest.py renombre los archivos de retro a retro-<fecha>-<n>
- Answer: a
- Answered: 2026-11-27

## Q-57
- Refs: E29
- Status: answered
- Asked: 2026-11-27
- Question: E29 C6: caracteres invisibles, binarios, test de merge con conflicto y aviso de privateCheck false. a) a pending.md; b) arreglarlos ya
- Recommendation: a) a pending.md como leves de la 0.10
- Answer: a
- Answered: 2026-11-27
