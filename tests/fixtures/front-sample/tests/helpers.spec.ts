// One green and one red case per helper of templates/front. A red case asserts the message: the reason it fails.
import { test, expect, gotoStable } from '../../../../templates/front/fixtures/stable';
import { expectNoOverflow, expectNoOverlap, expectTouchTargets } from '../../../../templates/front/helpers/layout';
import AxeBuilder from '@axe-core/playwright';
import { expectNoSeriousA11y } from '../../../../templates/front/helpers/a11y';

test.describe('expectNoOverflow', () => {
  test('green: a page that fits', async ({ page }) => {
    await gotoStable(page, 'index.html');
    await expectNoOverflow(page);
  });
  test('red: a 2000px block, and only the outermost one is named', async ({ page }) => {
    await gotoStable(page, 'overflow.html');
    const error = await expectNoOverflow(page).then(() => null, (e: Error) => e);
    expect(error?.message).toMatch(/horizontal overflow at \d+px[\s\S]*div\.wide is wider than the viewport/);
    expect(error?.message).not.toMatch(/p\.inner/);
  });
  test('green: a wide table inside its own scroller is not an overflow of the page', async ({ page }) => {
    await gotoStable(page, 'scroller.html');
    await expectNoOverflow(page);
  });
});

test.describe('expectNoOverlap', () => {
  test('green: two cards side by side', async ({ page }) => {
    await gotoStable(page, 'index.html');
    await expectNoOverlap(page.getByTestId('card-a'), page.getByTestId('card-b'));
  });
  test('red: two cards on top of each other', async ({ page }) => {
    await gotoStable(page, 'overlap.html');
    await expect(expectNoOverlap(page.getByTestId('card-a'), page.getByTestId('card-b'))).rejects.toThrow(
      /div\.card\[data-testid=card-a\] overlaps div\.card\[data-testid=card-b\] by 50x50px/,
    );
  });
});

test.describe('expectTouchTargets', () => {
  test('green: a 44px button-like link', async ({ page }) => {
    await gotoStable(page, 'index.html');
    await expectTouchTargets(page);
  });
  test('red: a 10px link', async ({ page }) => {
    await gotoStable(page, 'small-targets.html');
    await expect(expectTouchTargets(page)).rejects.toThrow(/a#tiny is 10x10px, smaller than the 24x24px minimum touch target/);
  });
  test('green: a link inside a sentence and a visually hidden control are exceptions (WCAG 2.5.8)', async ({ page }) => {
    await gotoStable(page, 'touch-exceptions.html');
    await expectTouchTargets(page, 24, { exclude: ['#tiny'] });
  });
  test('red: the same page without the exclusion names only the small link', async ({ page }) => {
    await gotoStable(page, 'touch-exceptions.html');
    const error = await expectTouchTargets(page).then(() => null, (e: Error) => e);
    expect(error?.message).toMatch(/a#tiny\S* is 10x10px/);
    expect(error?.message).not.toMatch(/a#terms|hidden-box/);
  });
  test('red: the minimum is a parameter', async ({ page }) => {
    await gotoStable(page, 'index.html');
    await expect(expectTouchTargets(page, 70)).rejects.toThrow(/a\.cta is \d+x\d+px, smaller than the 70x70px minimum/);
  });
});

test.describe('expectNoSeriousA11y', () => {
  test('green: the sample page', async ({ page }) => {
    await gotoStable(page, 'index.html');
    await expectNoSeriousA11y(page);
  });
  test('green: a moderate violation alone does not block (E-13), and axe does find it', async ({ page }) => {
    await gotoStable(page, 'a11y-moderate.html');
    const { violations } = await new AxeBuilder({ page }).analyze();
    expect(violations.map((v) => `${v.id}:${v.impact}`)).toContain('heading-order:moderate');
    await expectNoSeriousA11y(page);
  });
  test('red: an image without alt text (critical)', async ({ page }) => {
    await gotoStable(page, 'a11y-bad.html');
    await expect(expectNoSeriousA11y(page)).rejects.toThrow(/serious or critical[\s\S]*img \[image-alt, critical\]/);
  });
});
