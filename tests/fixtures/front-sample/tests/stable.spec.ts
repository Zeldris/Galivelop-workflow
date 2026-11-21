// The `stable` fixture: what it freezes and blocks, checked on a page that would otherwise vary.
import { test, expect, gotoStable, FIXED_TIME, appOrigin } from '../../../../templates/front/fixtures/stable';

test('green: the clock is fixed, motion is reduced, the animation is off, fonts are ready', async ({ page }) => {
  await gotoStable(page, 'motion.html');
  await expect(page.locator('#clock')).toHaveText(FIXED_TIME.toISOString());
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
  expect(await page.evaluate(() => getComputedStyle(document.getElementById('pulse')!).animationDuration)).toBe('0s');
  expect(await page.evaluate(() => document.fonts.status)).toBe('loaded');
});

test('green: another origin is blocked by the fixture, the app origin is not', async ({ page }) => {
  const failed: string[] = [];
  page.on('requestfailed', (request) => {
    if (request.url().startsWith('https://example.com/')) failed.push(request.failure()?.errorText ?? '');
  });
  await gotoStable(page, 'motion.html');
  await expect(page.locator('#external')).toHaveText('blocked');
  expect(failed).toHaveLength(1);
  expect(failed[0]).toMatch(/^net::ERR_BLOCKED_BY_CLIENT/);
  await expect(page.locator('#clock')).not.toBeEmpty();
});

test('green: the animation style is in place before the first script of the page runs', async ({ page }) => {
  await gotoStable(page, 'motion.html');
  await expect(page.locator('html')).toHaveAttribute('data-early', 'yes');
});

test('red: without a baseURL the fixture says so instead of blocking the app', () => {
  expect(() => appOrigin(undefined)).toThrow(/set `baseURL` in the Playwright config/);
  expect(() => appOrigin('')).toThrow(/set `baseURL`/);
  expect(appOrigin('http://127.0.0.1:4173/site/')).toBe('http://127.0.0.1:4173');
});

test('red: a request to another origin fails', async ({ page }) => {
  await gotoStable(page, 'motion.html');
  await expect(page.goto('https://example.com/')).rejects.toThrow(/ERR_BLOCKED_BY_CLIENT/);
});
