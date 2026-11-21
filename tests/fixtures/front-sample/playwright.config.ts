// The sample's config: the template's, with the folder served here as the app (a static site).
import { gwConfig } from '../../../templates/front/playwright.config';

// The port comes from GW_SAMPLE_PORT (tests/test_front_sample.py picks a free one, so parallel runs do not clash).
const port = Number(process.env.GW_SAMPLE_PORT ?? 4173);

export default gwConfig({
  testDir: 'tests',
  use: { baseURL: `http://127.0.0.1:${port}/site/` },
  webServer: {
    command: `python3 -m http.server ${port} --bind 127.0.0.1 --directory .`,
    url: `http://127.0.0.1:${port}/site/index.html`,
    reuseExistingServer: false,
    stdout: 'ignore',
  },
});
