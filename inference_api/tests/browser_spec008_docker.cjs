/* Local Docker smoke with disposable credentials supplied through environment. */
const assert = require('assert');
const { chromium } = require('playwright');

async function main() {
  const origin = process.env.SPEC008_TEST_ORIGIN;
  const password = process.env.SPEC008_FIXTURE_PASSWORD;
  if (!origin || !password || !/^http:\/\/127\.0\.0\.1:\d+$/.test(origin)) throw new Error('Fixture origin and password are required');
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 360, height: 740 } });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(origin);
    assert.equal(await page.getByRole('navigation').count(), 0);
    await page.locator('#password').fill(password); await page.locator('#login').click();
    await page.getByRole('navigation', { name: 'Seções do painel' }).waitFor();
    await page.locator('#content .card').first().waitFor();
    assert(await page.getByText('Retrato dos dados:', { exact: false }).count());
    await page.getByRole('button', { name: 'Dados e método' }).click();
    assert(await page.getByText('Este retrato offline não consulta o DW').count());
    await page.getByRole('button', { name: 'Bancada de testes' }).click();
    await page.getByText('Nenhum modelo disponível', { exact: false }).waitFor();
    await page.locator('#runs').selectOption({ index: 1 });
    await page.locator('#run-detail').getByText('query_error').waitFor();
    assert((await page.evaluate(() => document.documentElement.scrollWidth)) <= 360);
    await page.getByRole('button', { name: 'Sair' }).click();
    await page.locator('#login').waitFor();
    assert.equal(await page.getByRole('navigation').count(), 0);
    assert.equal(errors.length, 0, errors.join('; '));
    console.log('SPEC-008 Docker browser smoke passed: login, protected BI, bancada history/offline model, mobile and logout.');
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
