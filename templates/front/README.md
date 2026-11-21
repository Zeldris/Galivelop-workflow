<!-- galivelop-workflow v0.8.1 -->
# Front tests template (E5)

Playwright (layout, accessibility, visual) and Stylelint for a project with a front end, fed by the files
`scripts/front.py generate` writes from the project's design tokens. Written in TypeScript. Copy this folder into the
project (or a subfolder of it) and keep the pinned versions of `package.json` together with `package-lock.json`.

## Install

```sh
npm ci                          # exact versions from package-lock.json; needs node 22+
npx playwright install chromium # once per machine (browsers are not part of the package)
python3 .claude/gw/scripts/front.py generate   # tokens.css, _tokens.scss, stylelint.tokens.json, playwright.projects.json
```

## Run

```sh
npx playwright test --trace off        # one project per breakpoint and browser (playwright.projects.json)
npx playwright test --project 'chromium-*'
npx stylelint "**/*.{css,scss}"        # colours, spacing and font sizes must be tokens
```

`GW_PLAYWRIGHT_PROJECTS` overrides the path of `playwright.projects.json` (default
`front/generated/playwright.projects.json`, the default `front.out`). `.stylelintrc.json` extends
`./front/generated/stylelint.tokens.json`: change it if `front.out` is elsewhere.

## What is here

| File | What it gives |
|---|---|
| `playwright.config.ts` | `gwConfig(overrides)`: the generated projects, `animations: 'disabled'` on screenshots |
| `fixtures/stable.ts` | `test` with the automatic `stable` fixture (reduced motion, fixed clock, only the app's origin on the network, no animations); `gotoStable(page, url)` also waits for `document.fonts.ready` |
| `helpers/layout.ts` | `expectNoOverflow(page)`, `expectNoOverlap(a, b)`, `expectTouchTargets(page, minPx = 24)` |
| `helpers/a11y.ts` | `expectNoSeriousA11y(page)`: axe, blocks only on serious or critical |
| `.stylelintrc.json` | the standard SCSS config plus the generated strict-value rules |

Every failure message names the element and the reason. Set `baseURL` (and a `webServer`) through
`gwConfig({ use: { baseURL }, webServer })`. Screenshots (`toHaveScreenshot`) are compared only on Linux or in Docker
(E-9): baselines are per platform and are not part of this template yet.

## Pinned versions

Checked on 2026-11-21 against the npm registry (`registry.npmjs.org`): `@playwright/test` 1.63.0 (released
2026-09-04; the Chromium build it needs is the one preinstalled in the workflow's Linux environment; newer ones exist),
`playwright-core` 1.63.0 (pinned so axe and the tests share one copy), `@axe-core/playwright` 4.14.0, `stylelint` 18.1.0, `stylelint-config-standard-scss` 18.0.0 (requires stylelint 18),
`stylelint-declaration-strict-value` 1.13.0, `postcss` 8.5.33, `typescript` 5.9.3 (last 5.x), `@types/node` 22.20.5.
Update them together and run the sample (`tests/fixtures/front-sample` in the workflow repo) before accepting.
