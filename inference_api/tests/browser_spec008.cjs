/* Browser parity and bancada smoke against a running local SPEC-008 app, with mocked API. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const origin = process.env.SPEC008_TEST_ORIGIN || 'http://127.0.0.1:8878';
const snapshot = JSON.parse(fs.readFileSync(path.join(root, 'private', 'bi_snapshot.json'), 'utf8'));
const reference = fs.readFileSync(path.join(root, '..', 'specs', 'active', 'SPEC-008', 'references', 'BI_Pesquisa_Offline.reference.html'), 'utf8');
const output = path.join(root, '.local', 'spec008-browser');
const prompts = [], criteria = [], runs = [];
let tokenValid = true, modelsOnline = true, next = 1, budgetReads = 0, runAttempts = 0;
const id = () => String(next++).padStart(8, '0') + '-0000-0000-0000-000000000000';
const respond = (route, status, body) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });

function revision(list, payload, key) {
  const previous = list.filter(item => item.name === payload.name).at(-1);
  if ((previous?.revision || 0) !== payload.expected_revision) return { status: 409, body: { error: 'revision conflict', current: previous || null } };
  const item = { id: id(), name: payload.name, revision: (previous?.revision || 0) + 1, author: 'Nicoli', created_at: '2026-10-16T00:00:00Z', [key]: payload[key] };
  list.push(item); return { status: 201, body: item };
}

function makeRun(payload) {
  const p = prompts.find(item => item.id === payload.prompt_revision_id);
  const c = criteria.find(item => item.id === payload.criteria_revision_id);
  const failure = payload.question.includes('falha de consulta') ? { stage: 'query', type: 'QueryUnavailable' } : payload.question.includes('falha') ? { stage: 'model', type: 'ModelOffline' } : null;
  const evidence = { id: `financeiro_vendas_ano:${payload.year}`, source_database: 'db_financeiro', source_table: 'vendas', source_fields: ['valor'], period: { year: payload.year }, unit: 'BRL', value: '123', record_count: 13, quality: 'available', formula: 'sum(valor)', query_template: 'SELECT sum(valor) FROM vendas WHERE ano = %s', query_parameters: [payload.year], limitation: 'Não é receita contábil.' };
  const snapshot = { schema_version: 2, status: failure ? `${failure.stage}_error` : 'answered_unverified', question_request: { question: payload.question, scope: payload.scope, year: payload.year }, route_plan: { scope: payload.scope, year: payload.year, tools: ['financeiro_vendas_ano'], choice_origin: 'researcher_declared_scope' }, prompt: { revision_id: p?.id || null, revision: p?.revision || null, system_prompt: p?.system_prompt || payload.system_prompt }, verification_criteria: { revision_id: c?.id || null, revision: c?.revision || null, config: c?.config || payload.criteria }, model: { alias: payload.model_alias, parameters: { temperature: payload.temperature, max_tokens: payload.max_tokens } }, evidence_bundle: failure?.stage === 'query' ? null : { items: [evidence], limitations: ['Sem inferência causal.'] }, model_output: failure ? null : { raw_text: `Resposta ${payload.model_alias} [evidence:${evidence.id}]`, cited_evidence_ids: [evidence.id] }, checks: failure ? [] : [{ check: 'criteria_evidence_presence', result: 'passed', detail: 'Evidence present.' }], error: failure };
  const run = { id: id(), created_at: '2026-10-16T00:00:00Z', author: 'Nicoli', snapshot }; runs.push(run); return run;
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 850 }, acceptDownloads: true });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route(`${origin}/api/**`, async route => {
    const url = new URL(route.request().url()); const pathname = url.pathname;
    const body = route.request().postDataJSON?.() || {};
    if (pathname === '/api/login') { tokenValid = true; return respond(route, 200, { token: 'fixture-session', username: 'Nicoli' }); }
    if (!tokenValid || route.request().headers().authorization !== 'Bearer fixture-session') return respond(route, 401, { error: 'unauthorized' });
    if (pathname === '/api/me') return respond(route, 200, { id: 'fixture', username: 'Nicoli' });
    if (pathname === '/api/logout') { tokenValid = false; return respond(route, 200, { status: 'logged_out' }); }
    if (pathname === '/api/bi/snapshot') return respond(route, 200, snapshot);
    if (pathname === '/api/budget') { budgetReads++; return respond(route, 200, { session_ceiling_usd: 10, runpod_source: 'RunPod GraphQL myself.clientBalance', runpod_status: 'not_configured', runpod_balance_usd: null, runpod_spend_per_hour_usd: null, status_checked_at: '2026-10-16T00:00:00Z', checked_at: null }); }
    if (pathname === '/api/models') return respond(route, 200, { 'qwen-base': { available: modelsOnline }, 'qwen-fin': { available: modelsOnline }, 'qwen-offline': { available: false } });
    if (pathname === '/api/prompts') { if (route.request().method() === 'GET') return respond(route, 200, prompts); const r = revision(prompts, body, 'system_prompt'); return respond(route, r.status, r.body); }
    if (pathname === '/api/criteria') { if (route.request().method() === 'GET') return respond(route, 200, criteria); const r = revision(criteria, body, 'config'); return respond(route, r.status, r.body); }
    if (pathname === '/api/runs') { if (route.request().method() === 'GET') return respond(route, 200, [...runs].reverse()); runAttempts++; assert(budgetReads >= runAttempts + 1, 'budget must refresh before every run'); if (body.question.includes('limite')) return respond(route, 429, { error: 'global inference busy' }); return respond(route, 201, makeRun(body)); }
    if (pathname.endsWith('/feedback')) return respond(route, 201, { status: 'attached' });
    if (pathname.startsWith('/api/runs/')) return respond(route, 200, runs.find(run => run.id === pathname.split('/')[3]));
    return respond(route, 404, { error: 'not_found' });
  });
  try {
    await page.goto(origin);
    assert.equal(await page.getByRole('navigation').count(), 0, 'login must be the first screen');
    assert.equal(await page.getByText('Receita das vendas').count(), 0, 'BI must not render before login');
    await page.locator('#password').fill('fixture-only'); await page.locator('#login').click();
    await page.getByRole('navigation', { name: 'Seções do painel' }).waitFor();
    assert.equal(await page.locator('nav button').count(), 5);
    await page.locator('#content .card').first().waitFor();
    const ref = await browser.newPage({ viewport: { width: 1280, height: 850 }, acceptDownloads: true });
    await ref.setContent(reference); await ref.locator('#content .card').first().waitFor();
    await page.screenshot({ path: path.join(output, 'overview-new.png'), fullPage: true });
    await ref.screenshot({ path: path.join(output, 'overview-reference.png'), fullPage: true });
    for (const [tab, label] of [['overview', 'Visão integrada'], ['financial', 'Financeiro'], ['industrial', 'Industrial'], ['sources', 'Dados e método']]) {
      if (tab !== 'overview') { await page.getByRole('button', { name: label, exact: false }).click(); await ref.locator(`nav button[data-tab="${tab}"]`).click(); }
      const cards = await page.locator('#content .kpi-value').allTextContents();
      const refCards = await ref.locator('#content .kpi-value').allTextContents();
      if (tab === 'sources') { assert.equal(cards.length, refCards.length); assert.equal(cards[0], refCards[0]); assert.equal(cards[1], refCards[1]); assert.equal(cards[2], refCards[2]); assert(cards[3].includes('Local v1')); }
      else assert.deepEqual(cards, refCards, `${tab} KPI parity`);
      const rows = await page.locator('#content tbody tr').allInnerTexts();
      const refRows = await ref.locator('#content tbody tr').allInnerTexts();
      assert.deepEqual(rows, refRows, `${tab} table parity`);
      const chartPaths = await page.locator('#content svg path').evaluateAll(paths => paths.map(path => path.getAttribute('d')));
      const refChartPaths = await ref.locator('#content svg path').evaluateAll(paths => paths.map(path => path.getAttribute('d')));
      assert.deepEqual(chartPaths, refChartPaths, `${tab} chart geometry parity`);
    }
    assert(await page.getByText('Este retrato offline não consulta o DW').count());
    await page.locator('#start').selectOption('2020'); await page.locator('#end').selectOption('2020'); await page.locator('#grain').selectOption('month');
    await ref.locator('#start').selectOption('2020'); await ref.locator('#end').selectOption('2020'); await ref.locator('#grain').selectOption('month');
    assert.deepEqual(await page.locator('#content tbody tr').allInnerTexts(), await ref.locator('#content tbody tr').allInnerTexts(), 'filtered table parity');
    const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#download').click()]);
    const [refDownload] = await Promise.all([ref.waitForEvent('download'), ref.locator('#download').click()]);
    assert.equal(fs.readFileSync(await download.path()).toString('hex'), fs.readFileSync(await refDownload.path()).toString('hex'), 'CSV bytes must match reference');
    await page.screenshot({ path: path.join(output, 'desktop-bi.png'), fullPage: true });
    await page.getByRole('button', { name: 'Bancada de testes' }).click();
    await page.getByText('Fonte: RunPod GraphQL myself.clientBalance', { exact: false }).waitFor();
    await page.locator('#prompt').fill('Prompt versão 1'); await page.locator('#save').click(); await page.getByText('Revisão 1 salva.').waitFor();
    await page.locator('#required-caveats').fill('limite'); await page.locator('#save-criteria').click(); await page.getByText('Critérios revisão 1 salvos.').waitFor();
    await page.locator('#question').fill('Pergunta A'); await page.locator('#run').click(); await page.getByText('Respondido, sem validação científica.').waitFor();
    await page.locator('#prompt').fill('Prompt versão 2'); await page.locator('#save').click(); await page.getByText('Revisão 2 salva.').waitFor();
    await page.locator('#required-caveats').fill('limite\nassociação'); await page.locator('#save-criteria').click(); await page.getByText('Critérios revisão 2 salvos.').waitFor();
    await page.locator('#model').selectOption('qwen-fin'); await page.locator('#question').fill('Pergunta B'); await page.locator('#run').click(); await page.getByText('Resposta qwen-fin', { exact: false }).waitFor();
    await page.locator('#compare-runs').selectOption(runs.slice(0, 2).map(run => run.id)); await page.locator('#compare').click(); await page.getByText('Insumos diferentes', { exact: false }).waitFor();
    assert((await page.locator('#comparison').innerText()).includes('Consulta fixa do backend'));
    await page.locator('#runs').selectOption(runs[0].id); await page.locator('#feedback').fill('Comentário fixture'); await page.locator('#save-feedback').click(); await page.getByText('Feedback anexado', { exact: false }).waitFor();
    await page.locator('#prompt').fill('Rascunho preservado'); await page.locator('#revision').fill('0'); await page.locator('#save').click(); await page.locator('#prompt-conflict').getByText('Conflito: revisão atual 2', { exact: false }).waitFor(); assert.equal(await page.locator('#prompt').inputValue(), 'Rascunho preservado');
    await page.locator('#question').fill('limite'); await page.locator('#run').click(); await page.getByText('Limite de concorrência', { exact: false }).waitFor();
    await page.locator('#question').fill('falha de consulta'); await page.locator('#run').click(); await page.locator('#result').getByText('QueryUnavailable').waitFor();
    modelsOnline = false; await page.locator('#refresh-models').click(); await page.getByText('Nenhum modelo disponível', { exact: false }).waitFor();
    await page.setViewportSize({ width: 360, height: 740 });
    for (const label of ['Visão integrada', 'Financeiro', 'Industrial', 'Dados e método', 'Bancada de testes']) {
      await page.getByRole('button', { name: label, exact: false }).click();
      const width = await page.evaluate(() => document.documentElement.scrollWidth);
      assert(width <= 360, `${label} overflows mobile width: ${width}`);
    }
    await page.screenshot({ path: path.join(output, 'mobile-bench.png'), fullPage: true });
    await page.getByRole('button', { name: 'Sair' }).click(); await page.locator('#login').waitFor();
    assert.equal(await page.getByRole('navigation').count(), 0);
    assert.equal(errors.length, 0, errors.join('; '));
    console.log(`SPEC-008 browser parity and flows passed. Evidence: ${output}`);
    await ref.close();
  } finally { await browser.close(); }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
