# Prompts del piloto en Tarkor (Fase 6)

Dos prompts, uno por repo. Cada uno se pega en una sesión abierta con **ese repo como carpeta de trabajo** (sin
registrar Galivelop-workflow como raíz de la sesión). VeriNews_AI queda fuera: se aplicará en la Fase 8, sin agente.

Lo común a los dos (leído el 2026-10-22): ya llevan una copia anterior del flujo (17 skills, `.claude/hooks/`,
`.githooks/`, `tools/qa/`), la marca en `.claude/revision-main.sha`, bitácora `docs/registros/traspaso.md` con una
fila por rama, `main` solo por PR y dos cuentas que se relevan.

## World-Maker-Fantasy

```text
Vas a aplicar Galivelop-workflow v0.2.0 a este repo (World-Maker-Fantasy) como piloto: es la Fase 6 del plan del
flujo. Tienes mi permiso para modificar este repo en una rama nueva, claude/piloto-galivelop-workflow; este cambio
de entorno queda aprobado aunque el entorno esté congelado. A main, solo por PR con mi confirmación y siguiendo las
tres fases del flujo.

1. Clona https://github.com/Zeldris/Galivelop-workflow (etiqueta v0.2.0) en /home/user/Galivelop-workflow, solo para
   leer, y léelo con un subagente. No lo registres como raíz de la sesión: sus skills taparían las de este repo.
2. Sigue paso a paso /home/user/Galivelop-workflow/docs/es/aplicar.md (es el «proyecto existente»).
3. Lo propio de WMF, para .claude/gw.json:
   - pushToProtected: pr; protectedBranch: main; language: es; docs solo en español (sin pares ES/EN);
   - install: «npm ci» en backend/ y en frontend/;
   - check: lo que hoy corre el pre-push (tsc, lint, tests de backend y frontend, tools/roadmap/cobertura.py,
     tools/qa/{matriz-pruebas.py --comprobar,bitacora.py,enlaces-md.py,mapa-agente.py}, los unittest de tools/qa);
     decide conmigo qué va en check y qué en relatedTests (fast/slow) para que el push no se vuelva más lento;
   - log: docs/registros/traspaso.md con logRows: true (BITACORA_COMPARTIDA se conserva si el flujo no la cubre);
   - roadmap: true; plan: los roadmaps de docs/producto/; taskId con los prefijos de tools/roadmap/cobertura.py;
   - reviewMark: elige conmigo entre mantener .claude/revision-main.sha o pasar a docs/registros/revisado.txt;
   - protectedPaths: docs/rpgtarkor/ (el lore no lo edita un agente);
   - las skills opt-ai y scout-updates, con su parte propia en .claude/gw/ (Ollama real, bench-ia.sh, host.sh de la
     Steam Deck, donde la sesión local no tiene gh).
4. Sustituye la copia actual del flujo (.claude/skills, .claude/hooks, .claude/settings.json, .githooks, tools/qa) por
   la de Galivelop-workflow. Lo que WMF tenga propio y el flujo no traiga (matriz-pruebas, mapa-agente.py,
   comprobar-escenarios.sh, el mock de Ollama, .opencode/) se queda. Lo duplicado se quita solo tras comprobar que el
   flujo hace lo mismo. AGENTS.md hoy son reglas de lore para OpenCode: se fusiona, no se pisa. Los *.gw-nuevo se
   revisan conmigo.
5. Hecho cuando: el check y el CI (.github/workflows/ci.yml) en verde; pre-push, marca de revisado y gancho de PR
   funcionando (prueba del paso 6 de aplicar.md); doctor.py sin FAIL; un relevo entre cuentas sin perder nada
   (la otra cuenta retoma solo con la bitácora).
6. Apunta cada fricción, fallo o cosa que le falte al flujo en docs/registros/piloto-galivelop-workflow.md, con una
   sección «## For Galivelop-workflow» para que gw-harvest la recoja desde el repo del flujo.
7. Commit + push en cada punto estable, con la bitácora al día. Al acabar, dime qué ha quedado y qué falta.
```

## Instalador-WMF-Tarkor

```text
Vas a aplicar Galivelop-workflow v0.2.0 a este repo (Instalador-WMF-Tarkor) como piloto: es la Fase 6 del plan del
flujo. Tienes mi permiso para modificar este repo en una rama nueva, claude/piloto-galivelop-workflow (sale de main;
la rama de FLU-1 no se toca). A main, solo por PR con mi confirmación y siguiendo las tres fases del flujo.

1. Clona https://github.com/Zeldris/Galivelop-workflow (etiqueta v0.2.0) en /home/user/Galivelop-workflow, solo para
   leer, y léelo con un subagente. No lo registres como raíz de la sesión: sus skills taparían las de este repo.
2. Sigue paso a paso /home/user/Galivelop-workflow/docs/es/aplicar.md (es el «proyecto existente»).
3. Lo propio del instalador, para .claude/gw.json:
   - pushToProtected: pr; protectedBranch: main; language: es; docs solo en español (sin pares ES/EN);
   - stack Tauri v2 + Rust + asistente React/Vite en app/: hace falta Node 22, Rust stable y webkit2gtk en Linux;
   - install: «cd app && npm ci» (y lo que pida cargo);
   - check: lo que hoy corre el pre-push (tsc -b, cargo clippy --workspace --all-targets -D warnings,
     tools/qa/enlaces-md.py, los unittest de tools/qa); relatedTests.fast con «npx vitest related» y cargo test -p
     tarkor-nucleo; decide conmigo qué va en cada sitio;
   - log: docs/registros/traspaso.md con logRows: true; plan: docs/05-plan-de-trabajo.md; taskId: (INS|FLU)-\d+;
   - reviewMark: elige conmigo entre mantener .claude/revision-main.sha o pasar a docs/registros/revisado.txt;
   - las skills opt-ai y scout-updates, con su parte propia en .claude/gw/.
4. Sustituye la copia actual del flujo (.claude/skills, .claude/hooks, .claude/settings.json, .githooks, tools/qa) por
   la de Galivelop-workflow. Lo propio que el flujo no traiga se queda; lo duplicado se quita solo tras comprobar que
   el flujo hace lo mismo. No hay AGENTS.md: se crea desde la plantilla y CLAUDE.md pasa a importarlo. El CI
   (.github/workflows/comprobar.yml) se conserva; si el flujo trae el suyo, deja uno. Los *.gw-nuevo se revisan
   conmigo.
5. Hecho cuando: el CI en verde (linux, windows y qa); pre-push, marca de revisado y gancho de PR funcionando (prueba
   del paso 6 de aplicar.md); doctor.py sin FAIL; un relevo entre cuentas sin perder nada.
6. Apunta cada fricción, fallo o cosa que le falte al flujo en docs/registros/piloto-galivelop-workflow.md, con una
   sección «## For Galivelop-workflow» para que gw-harvest la recoja desde el repo del flujo.
7. Commit + push en cada punto estable, con la bitácora al día. Al acabar, dime qué ha quedado y qué falta.
```
