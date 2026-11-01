# Referencia: pruebas de front fiables y deterministas

Fecha: 2026-11-01. Rama `version/1.0.0`. Investigación para el bloque E (pruebas de front como las de back).

**Alcance de las fuentes.** Desde el entorno resolvían `raw.githubusercontent.com` y `registry.npmjs.org`, pero **no**
`playwright.dev`, `stylelint.io` ni la API/páginas de GitHub. Por eso: versiones y fechas salen del registro de npm
(primario); la documentación de Playwright, de su `docs/src/*.md` en GitHub (primario); lo demás, de los README de
los repos. Lo que no se pudo confirmar va marcado **[NC]**.

## Resumen

- Todo lo necesario existe en libre y encaja en un flujo local + GitHub Actions: Stylelint (normas CSS),
  `toHaveScreenshot` (visual), proyectos/`devices` de Playwright (responsive), `@axe-core/playwright` (accesibilidad).
- La fiabilidad visual depende del **entorno de render**, no de la herramienta: Playwright avisa de que el render varía
  con SO, versión, ajustes, hardware y modo headless. Un baseline por plataforma (`-chromium-linux.png`, `-darwin.png`)
  o, mejor, **un solo baseline generado en el contenedor oficial** y comparado solo en CI/Docker.
- Las animaciones se hacen deterministas con tres capas: `animations: "disabled"` (por defecto en
  `toHaveScreenshot`), `reducedMotion: 'reduce'` y `page.clock`.
- Una norma escrita de front solo es checable si se **expresa como dato** (tokens + breakpoints en un archivo) y de ahí
  se generan reglas de Stylelint y matriz de viewports; la norma en prosa no es un check.
- Pagos: ninguno es obligatorio. Lost Pixel tiene plataforma gestionada opcional; Percy/Chromatic/Applitools son SaaS.

## 1. Arquitectura de estilos y normas de CSS

| Herramienta | Versión (npm) | Qué cubre |
|---|---|---|
| `stylelint` | 17.16.0 (2026-10-01), MIT | Linter de CSS/SCSS/Less; reglas por núcleo y plugins |
| `stylelint-config-standard` | 40.0.0 (2026-01-15) | Convenciones base (estilo); opcional |
| `stylelint-declaration-strict-value` | 1.12.1 (2026-08-24), MIT | Exige variable/función en una propiedad |
| `stylelint-use-logical` | 2.1.3 (2026-02-04), CC0 | Propiedades lógicas (RTL) en vez de left/right |
| `stylelint-no-unsupported-browser-features` | 8.1.2 (2026-09-09) | Rechaza features fuera de browserslist |
| `stylelint-plugin-defensive-css` | 2.9.7 (2026-09-06) | Patrones defensivos (desbordes, flex-wrap) |

- **Determinista:** sí, análisis estático; mismo resultado en Linux y macOS. Corre en milisegundos, apto para
  pre-push. Salida JSON/formatters para el CI.
- **Valores prohibidos / solo tokens.** `stylelint-declaration-strict-value` (README): regla
  `scale-unlimited/declaration-strict-value` con propiedades como opción primaria (`"color"`, regex, lista) y
secundarios
  `ignoreValues`, `ignoreFunctions`, `ignoreVariables`, `expandShorthand`, `message`, autofix. Con `color`, rechaza
  `#FFF` y `currentColor` y acepta `var(--color-white)`. Cubre también `font-size`, `z-index`, `margin`, etc.
- **Núcleo de Stylelint** [NC: reglas leídas de memoria, la página de reglas no resolvía]: `color-named`,
  `color-no-hex`, `declaration-property-value-(allowed|disallowed)-list`, `property-disallowed-list`,
  `unit-allowed-list`, `function-disallowed-list`, `media-feature-name-allowed-list`, `custom-property-pattern`.
  Sirven para listas cerradas (p. ej. solo `rem` y `%`; prohibido `!important` con `declaration-no-important`).
- **Breakpoints:** `@media (min-width: …)` con valor literal se limita con `media-feature-name-*` y
  `at-rule-prelude-allowed-list` [NC]; lo robusto es prohibir el literal y exigir una variable de preprocesador o
  `@custom-media` (los custom properties no valen dentro de `@media`).
- Alternativas: `@projectwallace/css-analyzer`, `cssstats`, Parker (métricas, no normas) [NC]; ESLint no cubre CSS puro;
  `@eslint/css` existe [NC]. Stylelint es el estándar de facto.
- **Encaje:** `npx stylelint "**/*.{css,scss}"` en pre-push y CI; solo requiere Node. Fijar versión en lockfile.

## 2. Regresión visual

| Herramienta | Versión / fecha | Coste | Notas |
|---|---|---|---|
| Playwright `toHaveScreenshot` | 1.64.1 (2026-10-14), Apache-2.0 | Libre | Integrado; pixelmatch; sin servicio |
| BackstopJS | 6.3.25 (2024-09-07), MIT | Libre | Puppeteer/Playwright; informe HTML; poco movimiento |
| Lost Pixel | 3.22.0 (2024-11-14), MIT | Núcleo libre; **plataforma de pago/freemium** | Storybook/Ladle/páginas |
| reg-suit | 0.14.5 (2025-08-26), MIT | Libre | Solo compara y publica; requiere almacén (S3/GCS) |
| pixelmatch / odiff-bin | 8.0.0 (2026-10-06) / 4.5.0 (2026-07-23) | Libre | Motores de diff, no flujo |
| Percy (`@percy/cli`) | 1.32.12 (2026-10-21) | **SaaS de pago** [NC precios] | Render en su nube |

- **`toHaveScreenshot` (docs oficiales, `test-snapshots`):** la primera ejecución genera el baseline; toma capturas
  hasta
  que dos consecutivas coinciden. Nombre `<test>-<proyecto>-<so>.png`, así que **hay un baseline por plataforma**.
  Opciones: `threshold` (0 estricto a 1 laxo; defecto 0.2, aceptable perceptual por píxel), `maxDiffPixels`,
  `maxDiffPixelRatio`, `stylePath` (CSS inyectado para ocultar lo volátil), `mask`, `caret`, `animations`
  (defecto `"disabled"`). Actualizar: `--update-snapshots`. Mover el ratón a (-1,-1) evita hovers.
  Los umbrales se fijan global o por proyecto en `expect.toHaveScreenshot` del config.
- **Determinismo entre SO:** **no** lo garantiza (fuentes, antialiasing, GPU). Prácticas: (a) baselines solo del
  contenedor oficial `mcr.microsoft.com/playwright` [NC: nombre/versión de imagen sin verificar] fijado a la misma
  versión que `@playwright/test`; (b) tanto el pre-push local en macOS como el CI ejecutan las visuales **dentro de
  Docker**, o las visuales corren solo en CI y local las omite; (c) fuentes web locales y `fonts.ready` esperado.
- **Anti-flakiness:** umbral 0 con Docker fijado es posible; con SO mixto hay que subir `threshold`/`maxDiffPixels`,
  lo que oculta regresiones pequeñas. Preferible no mezclar SO.
- **BackstopJS:** escenarios JSON, viewports en config, informe HTML; su última versión es de 2024-09 (sin movimiento
  desde hace ~14 meses). Añade un runner más al lado de Playwright: poco valor si ya se usa `toHaveScreenshot`.
- **Lost Pixel:** README: núcleo abierto y «Lost Pixel Platform» gestionada (aprobación, UI de revisión, monorepo
  son **solo plataforma**). Última versión 2024-11. Útil sobre todo con Storybook.
- **reg-suit:** compara carpetas de imágenes y comenta el PR; necesita plugin de almacenamiento (nube propia).
- **Encaje:** `toHaveScreenshot` no añade dependencias ni cuentas. Los baselines son binarios en git: pesan; valorar
  Git LFS o artefactos de CI [NC sobre costes de LFS].

## 3. Responsive y adaptativo

- **Playwright:** `devices` (registro de perfiles con viewport, `deviceScaleFactor`, `isMobile`, `hasTouch`,
  userAgent) y **proyectos** en `playwright.config.ts`: un proyecto por celda de la matriz, cada uno con su baseline
  `-<proyecto>-<so>`. Nota: el emulador de móvil emula viewport y UA, no el motor de Safari; para WebKit real hay que
  incluir un proyecto `webkit` (corre en Linux y macOS). Versión de referencia: 1.64.1.
- **Matriz recomendada:** derivar los viewports **de los breakpoints declarados** (`ancho-1`, `ancho`, `ancho+1` de
  cada breakpoint) más 1-2 dispositivos reales (móvil, tableta). Un script genera los proyectos desde un JSON.
- **Comprobaciones de layout** (código propio, deterministas): sin desborde horizontal
  (`document.documentElement.scrollWidth <= clientWidth`), ningún elemento visible con `getBoundingClientRect().right >
  innerWidth`, objetivos táctiles >= 24x24 CSS px (WCAG 2.2 AA, criterio 2.5.8 [NC: texto WCAG no consultado]), sin
  solape entre bloques declarados (comparar rectángulos de pares `data-testid` con `boundingBox()`), `overflow`
  controlado. Se escriben como un `expect.poll`/`evaluate` reutilizable y corren en toda la matriz.
- **Galen Framework** (`galenframework/galen`): su README lo define como «open-source tool for testing layout and
  responsive design» sobre Selenium con lenguaje de especificaciones propio. No está en npm con ese nombre en el
registro
  consultado; el README aún enlaza a Travis CI y no pude ver fecha de último commit ni release → **[NC]**, y todo apunta
  a **no mantenido**. Descartado: Selenium + Java, otro runner. Sus ideas (specs «A a la izquierda de B») se replican
con
  `boundingBox()` en Playwright.

## 4. Animaciones y transiciones

- `toHaveScreenshot({ animations: 'disabled' })` (defecto): las animaciones/transiciones **finitas** se llevan a su
  estado final y las infinitas se cancelan al estado inicial [NC: texto exacto de la opción no leído; esto es el
  comportamiento documentado de la API]. También `caret: 'hide'` (defecto).
- `reducedMotion: 'reduce'` (opción de contexto/`use`, también `page.emulateMedia`): activa
  `prefers-reduced-motion`. Verificado en `params.md` (valores `reduce|no-preference`, defecto `no-preference`).
  Sirve para dos cosas: pruebas deterministas **y** comprobar que el CSS respeta la preferencia.
- `page.clock` (`docs/src/clock.md`): `install`, `setFixedTime`, `pauseAt`, `fastForward`, `runFor`, `resume`. Sustituye
  `Date`, `setTimeout`, `setInterval`, `requestAnimationFrame`, `requestIdleCallback`, `performance`, `Event.timeStamp`.
  Orden obligatorio: `install` antes de cualquier otra llamada relacionada con el reloj. Recomendado: `setFixedTime`
  si basta; `install` + `pauseAt` para avanzar a mano el tiempo de timers/rAF.
- **Web Animations API** `document.getAnimations()` [NC: MDN no resolvía]: devuelve las animaciones activas
  (CSS y WAAPI); para estados intermedios, `a.pause(); a.currentTime = t` en cada una y luego capturar. Para esperar el
  fin: `await Promise.all(document.getAnimations().map(a => a.finished))`. Cuidado con las infinitas (nunca terminan).
- **Receta de determinismo:** `reducedMotion: 'reduce'` + `animations: 'disabled'` + `page.clock` + esperar
  `document.fonts.ready` e imágenes + `stylePath` que oculta carruseles/vídeos + red simulada (`page.route`).
  Una prueba **de la animación** (que exista, dure X ms) va aparte, con `getAnimations()` y sin captura.

## 5. Accesibilidad

| Herramienta | Versión / fecha | Licencia | Notas |
|---|---|---|---|
| `axe-core` | 4.14.0 (2026-10-05) | MPL-2.0 | Motor de reglas WCAG; determinista |
| `@axe-core/playwright` | 4.14.0 (2026-10-15) | MPL-2.0 | `new AxeBuilder({ page }).analyze()` |
| `pa11y` | 10.0.0 (2026-08-28) | LGPL-3.0 | CLI sobre Puppeteer; usa HTML_CodeSniffer o axe [NC] |
| `@lhci/cli` | 0.15.1 (2025-06-25) | Apache-2.0 | Lighthouse en CI con aserciones; score + perf |

- **`@axe-core/playwright` (README oficial):** API encadenable: `include`, `exclude`, `withTags` [NC lista completa],
  `analyze()`. Versionado = major.minor de axe-core, **no SemVer**: fijar versión exacta. Se integra en el mismo test
  que ya navega, sin runner nuevo; encaja con la matriz de proyectos (axe por viewport/tema).
- Límite conocido: las pruebas automáticas solo detectan una parte de los problemas (Deque cita cifra en torno al 57 %
  [NC]); no sustituyen la revisión manual. Contraste dependiente de fondos con imágenes o gradientes da «incompleto».
- Pa11y: útil como CLI sin código de prueba; para un proyecto que ya usa Playwright, duplica navegador y no aporta nada
  que axe no dé. Licencia LGPL: sin problema por ser herramienta de desarrollo.
- Lighthouse CI: aserciones por categoría/puntuación; las **puntuaciones de rendimiento varían** con la máquina, así que
  solo el apartado de accesibilidad es razonable como bloqueante; el servidor LHCI es opcional [NC alcance del
  servidor]. Más pesado que axe; valor añadido: SEO y buenas prácticas.

## 6. De norma escrita a check automático

1. **Fuente única de datos:** `tokens.json` (colores, espaciados, tipografías, z-index) y `breakpoints.json`. La norma
   en prosa enlaza al archivo, no repite los valores («un dato, un sitio»).
2. **Generar, no copiar:** un script produce (a) el CSS `:root{--…}` o el Sass de variables, (b) la configuración de
   `declaration-strict-value` por propiedad (`color`, `background-color`, `border-color`, `font-size`, `z-index`…),
   (c) los proyectos de viewport de Playwright. Si una norma cambia, cambia el JSON y los tres siguen.
3. **Tres niveles de check:** estático (Stylelint sobre fuente), de runtime (en Playwright, `getComputedStyle` de los
   elementos y comprobar que cada color calculado ∈ paleta; atrapa estilos en línea y CSS de terceros) y visual.
4. Cada regla con **caso de test negativo** (un CSS con `#fff` debe fallar con el mensaje esperado), como pide
   AGENTS.md para los scripts.
5. Excepciones explícitas y escasas: `/* stylelint-disable-next-line … -- motivo */` con
   `reportNeedlessDisables` e `reportInvalidScopeDisables` [NC: nombres exactos] para no acumular silencios.
6. Lo que no se puede automatizar (jerarquía, «se ve bien») queda como lista de revisión humana, no como regla vacía.

## Tabla comparativa

| Aspecto | Herramienta recomendada | Libre | Determinista | Linux + macOS | Pre-push (rápido) |
|---|---|---|---|---|---|
| Normas CSS | Stylelint + strict-value | Sí | Sí | Sí | Sí (s) |
| Visual | `toHaveScreenshot` en Docker | Sí | Sí, en el mismo entorno | Solo con Docker | Parcial: lento |
| Responsive | Proyectos `devices` + check de layout | Sí | Sí | Sí | Sí, subconjunto |
| Animaciones | reducedMotion + animations + clock | Sí | Sí | Sí | Sí |
| A11y | `@axe-core/playwright` | Sí | Sí | Sí | Sí |
| A11y/perf extra | Lighthouse CI | Sí | Perf no | Sí | No, solo CI |
| Visual alternativa | BackstopJS / Lost Pixel / reg-suit | Núcleo sí | Igual de dependiente del entorno | Sí | No |
| Layout Galen | Galen Framework | Sí | n/a | Selenium/Java | Descartado [NC mantenimiento] |

## Ideas para el diseño (bloque E)

1. Un solo runner (Playwright) para visual, responsive, animación y a11y; Stylelint como único añadido.
2. `gw.json` declara `front: { tokens, breakpoints, viewports }`; un script del flujo genera config de Stylelint y
   proyectos de Playwright (lo comprobable lo hace un script, no un agente).
3. Perfiles de check: `rapido` (Stylelint + layout + axe en 2 viewports) en pre-push; `completo` (visual en Docker +
   matriz entera) en CI y antes de `main`.
4. Baselines visuales: un único SO (Linux/Docker). `doctor.py` avisa si hay baselines `-darwin` o de otra versión de
   Playwright; en macOS las visuales se ejecutan por Docker o se omiten con aviso explícito (falla cerrado, no verde
falso).
5. Fixtures compartidas: `estable()` que aplica `reducedMotion`, `page.clock.install`, `fonts.ready`, `stylePath`
   y bloqueo de red; todo test visual la usa y un check estático lo exige.
6. Helpers de layout (`sinDesborde`, `sinSolape`, `objetivosTactiles`) y de color calculado ∈ paleta, con sus tests
   rojos.
7. Plantilla de proyecto: `.stylelintrc`, `playwright.config.ts` con proyectos derivados, workflow de Actions con el
   contenedor oficial fijado a la versión de Playwright.
8. Política de actualización de baselines: solo con `--update-snapshots` explícito y diff revisado; ningún commit
   automático de imágenes; la bitácora anota qué se aceptó y por qué.

## Preguntas para el usuario

1. ¿Las capturas visuales se generan y comparan solo en Docker/Linux (local y CI), o se acepta un baseline por SO?
   Recomendación: solo Docker/Linux; macOS ejecuta la visual vía Docker o la omite avisando.
2. ¿La visual corre en el pre-push o solo en CI y antes de `main`? Recomendación: solo CI y fase de cierre; el
   pre-push lleva Stylelint, layout y axe.
3. ¿Dónde viven los tokens y breakpoints de cada proyecto (JSON propio, CSS, Tailwind/theme)? Recomendación: JSON
   en `gw.json` o archivo enlazado, y de él se generan reglas y viewports.
4. ¿Qué proyectos usan Sass/Less/CSS-in-JS además de CSS puro? Recomendación: soportar CSS y SCSS de inicio; el
   resto solo si un proyecto real lo exige.
5. ¿Se bloquea con a11y por defecto (axe, sin violaciones graves/críticas) y se deja Lighthouse CI como opcional?
   Recomendación: sí a axe bloqueante, Lighthouse solo informativo.
6. ¿Los baselines van en git, Git LFS o artefactos de CI? Recomendación: en git mientras sean pocos y pequeños; LFS
   si superan un umbral que fije el flujo.
7. ¿Se admite un servicio de pago o SaaS visual (Percy, Chromatic, Lost Pixel Platform)? Recomendación: no; el flujo
   debe funcionar sin cuentas externas.
8. ¿Qué matriz mínima de dispositivos y navegadores exige el flujo (chromium + webkit móvil/escritorio)? Recomendación:
   chromium en todos los breakpoints, webkit y firefox solo en el viewport escritorio y móvil principal.

## Fuentes

- Playwright, visual comparisons:
  https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/test-snapshots-js.md
- Playwright, clock: https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/clock.md
- Playwright, parámetros (reducedMotion):
  https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/api/params.md
- Playwright, aserciones de página:
  https://raw.githubusercontent.com/microsoft/playwright/main/docs/src/api/class-pageassertions.md
- Stylelint strict-value: https://raw.githubusercontent.com/AndyOGo/stylelint-declaration-strict-value/master/README.md
- axe-core npm, Playwright:
  https://raw.githubusercontent.com/dequelabs/axe-core-npm/develop/packages/playwright/README.md
- Lost Pixel: https://raw.githubusercontent.com/lost-pixel/lost-pixel/main/README.md
- Galen: https://raw.githubusercontent.com/galenframework/galen/master/README.md
- Lighthouse CI: https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/docs/getting-started.md
- Versiones y fechas: https://registry.npmjs.org/<paquete> (stylelint, @playwright/test, @axe-core/playwright, axe-core,
  pa11y, @lhci/cli, backstopjs, lost-pixel, reg-suit, pixelmatch, odiff-bin, @percy/cli, stylelint-*).
- No resueltos desde el entorno (hay que permitirlos en la red de la sesión para cerrar los [NC]): playwright.dev,
  stylelint.io, developer.mozilla.org, w3.org, github.com y api.github.com.
