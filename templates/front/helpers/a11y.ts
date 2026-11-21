// Accessibility check (E-13): axe blocks on serious or critical violations only; minor and moderate are not reported.
import AxeBuilder from '@axe-core/playwright';
import type { Page } from '@playwright/test';

/** Fails when axe finds a serious or critical violation; the message names each element, its rule and the reason. */
export async function expectNoSeriousA11y(page: Page): Promise<void> {
  const { violations } = await new AxeBuilder({ page }).analyze();
  const blocking = violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
  if (blocking.length === 0) return;
  const lines = blocking.flatMap((v) =>
    v.nodes.map((n) => `${n.target.join(' ')} [${v.id}, ${v.impact}]: ${v.help} (${n.failureSummary?.split('\n').slice(1).join(' ').trim() || v.description})`),
  );
  throw new Error(`${blocking.length} serious or critical accessibility violation(s):\n  ` + lines.join('\n  '));
}
