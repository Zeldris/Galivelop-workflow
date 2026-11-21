// One green and one red case per helper of templates/front. A red case asserts the message: the reason it fails.
import { test, expect, gotoStable } from '../../../../templates/front/fixtures/stable';
import { expectNoOverflow, expectNoOverlap, expectTouchTargets } from '../../../../templates/front/helpers/layout';
import { expectNoSeriousA11y } from '../../../../templates/front/helpers/a11y';

test.describe('expectNoOverflow', () => {
  test('green: a page that fits', async ({ page }) => {
    await gotoStable(page, 'index.html');
    await expectNoOverflow(page);
  });
  test('red: a 2000px block', async ({ page }) => {
    await gotoStable(page, 'overflow.html');
    await expect(expectNoOverflow(page)).rejects.toThrow(/horizontal overflow at \d+px[\s\S]*div\.wide is wider than the viewport/);
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
  test('red: an image without alt text (critical)', async ({ page }) => {
    await gotoStable(page, 'a11y-bad.html');
    await expect(expectNoSeriousA11y(page)).rejects.toThrow(/serious or critical[\s\S]*img \[image-alt, critical\]/);
  });
});
