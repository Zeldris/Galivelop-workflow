// The `stable` fixture: what it freezes and blocks, checked on a page that would otherwise vary.
import { test, expect, gotoStable, FIXED_TIME } from '../../../../templates/front/fixtures/stable';

test('green: the clock is fixed, motion is reduced, the animation is off, fonts are ready', async ({ page }) => {
  await gotoStable(page, 'motion.html');
  await expect(page.locator('#clock')).toHaveText(FIXED_TIME.toISOString());
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
  expect(await page.evaluate(() => getComputedStyle(document.getElementById('pulse')!).animationDuration)).toBe('0s');
  expect(await page.evaluate(() => document.fonts.status)).toBe('loaded');
});

test('green: another origin is blocked, the app origin is not', async ({ page }) => {
  await gotoStable(page, 'motion.html');
  await expect(page.locator('#external')).toHaveText('blocked');
});

test('red: a request to another origin fails', async ({ page }) => {
  await gotoStable(page, 'motion.html');
  await expect(page.goto('https://example.com/')).rejects.toThrow(/ERR_BLOCKED_BY_CLIENT/);
});
