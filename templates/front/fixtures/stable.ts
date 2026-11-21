// galivelop-workflow v0.8.1
// `stable`: what makes a page render the same every time (ref-front-testing, section 4): reduced motion, a fixed
// clock, fonts loaded, no network but the app's own origin, and no animations or transitions. It is an automatic
// fixture of the `test` this file exports, so every test that imports `test` from here gets it.
import { test as base, expect, type Page } from '@playwright/test';

/** The instant `page.clock` is frozen at (UTC). */
export const FIXED_TIME = new Date('2024-01-15T10:00:00Z');

const NO_MOTION = `*, *::before, *::after {
  animation-duration: 0s !important; animation-delay: 0s !important; animation-iteration-count: 1 !important;
  transition-duration: 0s !important; transition-delay: 0s !important; scroll-behavior: auto !important;
  caret-color: transparent !important;
}`;

/** Apply the stable setup to `page`; `origin` is the only origin allowed on the network (default: the baseURL's). */
export async function makeStable(page: Page, origin?: string): Promise<void> {
  const allowed = origin ?? new URL(String(test.info().project.use.baseURL ?? 'http://localhost')).origin;
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.clock.install({ time: FIXED_TIME });
  await page.clock.setFixedTime(FIXED_TIME);
  await page.route(
    (url) => /^https?:$/.test(url.protocol) && url.origin !== allowed,
    (route) => route.abort('blockedbyclient'),
  );
  // Runs in every document before its scripts: the style goes in as soon as <head> exists.
  await page.addInitScript((css) => {
    const add = () => {
      const style = document.createElement('style');
      style.dataset.gwStable = '';
      style.textContent = css;
      (document.head || document.documentElement).appendChild(style);
    };
    if (document.head) add();
    else document.addEventListener('DOMContentLoaded', add, { once: true });
  }, NO_MOTION);
}

/** Wait until the page is ready to be measured or captured: `document.fonts.ready`. Call it after `page.goto`. */
export async function whenStable(page: Page): Promise<void> {
  await page.evaluate(() => document.fonts.ready.then(() => undefined));
}

export const test = base.extend<{ stable: void }>({
  stable: [
    async ({ page, baseURL }, use) => {
      await makeStable(page, baseURL ? new URL(baseURL).origin : undefined);
      await use();
    },
    { auto: true },
  ],
});

// `page.goto` resolves on `load`; the fonts may still be loading, so wait for them as well.
export async function gotoStable(page: Page, url: string): Promise<void> {
  await page.goto(url);
  await whenStable(page);
}

export { expect };
