/* Local browser contract check with fake, nonpersistent API data and credentials. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'web', 'index.html'), 'utf8');
const output = path.join(root, '.local', 'spec004-browser-mobile.png');
const desktopOutput = path.join(root, '.local', 'spec004-browser-desktop.png');
const prompts = [], criteria = [], runs = [];
let modelsOnline = true;
let next = 1;
const id = () => String(next++).padStart(8, '0') + '-0000-0000-0000-000000000000';
const response = (route, status, body) => route.fulfill({status, contentType: 'application/json', body: JSON.stringify(body)});

function addRevision(list, payload, configKey) {
  const previous = list.filter(item => item.name === payload.name).at(-1);
  const revision = previous?.revision || 0;
  if (revision !== payload.expected_revision) return {status: 409, body: {error: 'revision conflict', current: previous || null}};
  const item = {id: id(), name: payload.name, revision: revision + 1, author: 'Nicoli',
    created_at: '2026-10-15T12:00:00Z', [configKey]: payload[configKey]};
  list.push(item);
  return {status: 201, body: item};
}

function makeRun(payload) {
  const prompt = prompts.find(item => item.id === payload.prompt_revision_id);
  const criterion = criteria.find(item => item.id === payload.criteria_revision_id);
  const unit = 'BRL';
  const error = payload.question.includes('falha de consulta') ? {stage: 'query', type: 'QueryUnavailable'}
    : payload.question.includes('falha') ? {stage: 'model', type: 'ModelOffline'} : null;
  const item = {id: 'financeiro_vendas_ano:2020', source_database: 'db_financeiro',
    source_table: 'vendas', source_fields: ['valor'], period: {year: payload.year},
    unit, value: '123', record_count: 13, quality: 'available', formula: 'sum(valor)',
    query_template: 'SELECT sum(valor) FROM vendas WHERE ano = %s', query_parameters: [payload.year],
    limitation: 'Soma não é receita contábil.'};
  const snapshot = {schema_version: 2,
    status: error ? (error.stage === 'query' ? 'query_error' : 'model_error') : 'answered_unverified',
    question_request: {question: payload.question, scope: payload.scope, year: payload.year},
    route_plan: {scope: payload.scope, year: payload.year, tools: ['financeiro_vendas_ano'],
      choice_origin: 'researcher_declared_scope'},
    prompt: {revision_id: prompt?.id || null, revision: prompt?.revision || null,
      system_prompt: prompt?.system_prompt || payload.system_prompt},
    verification_criteria: {revision_id: criterion?.id || null, revision: criterion?.revision || null,
      config: criterion?.config || payload.criteria},
    model: {alias: payload.model_alias, base_revision: 'test-revision',
      adapter_hash: payload.model_alias === 'qwen-base' ? null : 'test-hash',
      parameters: {temperature: payload.temperature, max_tokens: payload.max_tokens}},
    evidence_bundle: error?.stage === 'query' ? null : {items: [item], limitations: ['Sem inferência causal.']},
    model_output: error ? null : {raw_text: `Resposta ${payload.model_alias} [evidence:${item.id}]`, cited_evidence_ids: [item.id]},
    checks: error ? [] : [{check: 'criteria_evidence_presence', result: 'passed', detail: 'Evidence present.'}], error};
  const run = {id: id(), created_at: '2026-10-15T12:00:00Z', author: 'Nicoli', snapshot};
  runs.push(run);
  return run;
}

async function main() {
  const browser = await chromium.launch({headless: true});
  const page = await browser.newPage({viewport: {width: 390, height: 844}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('http://127.0.0.1:8765/**', async route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    if (pathname === '/') return route.fulfill({status: 200, contentType: 'text/html', body: html});
    const body = route.request().postDataJSON?.() || {};
    if (pathname === '/api/login') return response(route, 200, {token: 'test-session', username: 'Nicoli'});
    if (pathname === '/api/logout') return response(route, 200, {status: 'logged_out'});
    if (pathname === '/api/budget') return response(route, 200, {session_ceiling_usd: 10, runpod_status: 'not_configured', runpod_source: 'test', checked_at: null});
    if (pathname === '/api/models') return response(route, 200, {'qwen-base': {available: modelsOnline}, 'qwen-fin': {available: modelsOnline}, 'qwen-offline': {available: false}});
    if (pathname === '/api/prompts') {
      if (route.request().method() === 'GET') return response(route, 200, prompts);
      const result = addRevision(prompts, body, 'system_prompt'); return response(route, result.status, result.body);
    }
    if (pathname === '/api/criteria') {
      if (route.request().method() === 'GET') return response(route, 200, criteria);
      const result = addRevision(criteria, body, 'config'); return response(route, result.status, result.body);
    }
    if (pathname === '/api/runs') {
      if (route.request().method() === 'GET') return response(route, 200, [...runs].reverse());
      return response(route, 201, makeRun(body));
    }
    if (pathname.startsWith('/api/runs/')) return response(route, 200, runs.find(run => '/' + run.id === pathname.slice('/api/runs'.length)));
    return response(route, 404, {error: 'not_found'});
  });
  try {
    await page.goto('http://127.0.0.1:8765/');
    await page.locator('#password').fill('test-only');
    await page.locator('#login').click();
    await page.getByText('Conectado como Nicoli.').waitFor();
    await page.locator('#prompt').fill('Prompt versão 1');
    await page.locator('#save').click();
    await page.getByText('Revisão 1 salva.').waitFor();
    await page.locator('#required-caveats').fill('limite');
    await page.locator('#save-criteria').click();
    await page.getByText('Critérios revisão 1 salvos.').waitFor();
    await page.locator('#question').fill('Pergunta A');
    await page.locator('#model').selectOption('qwen-base');
    await page.locator('#run').click();
    await page.locator('#result').getByText('Respondido, sem validação científica.').waitFor();
    await page.locator('#prompt').fill('Prompt versão 2');
    await page.locator('#save').click();
    await page.getByText('Revisão 2 salva.').waitFor();
    await page.locator('#required-caveats').fill('limite\nassociação');
    await page.locator('#save-criteria').click();
    await page.getByText('Critérios revisão 2 salvos.').waitFor();
    await page.locator('#question').fill('Pergunta B');
    await page.locator('#model').selectOption('qwen-fin');
    await page.locator('#run').click();
    await page.locator('#result').getByText('Resposta qwen-fin', {exact: false}).waitFor();
    await page.locator('#compare-runs').selectOption(runs.slice(0, 2).map(run => run.id));
    await page.locator('#compare').click();
    await page.getByText('Insumos diferentes', {exact: false}).waitFor();
    const comparison = await page.locator('#comparison').innerText();
    assert(comparison.includes('Prompt versão 1') && comparison.includes('Prompt versão 2'));
    assert(comparison.includes('Revisão dos critérios') && comparison.includes('Consulta fixa do backend'));
    assert(!/acurácia\s*:\s*\d/i.test(comparison));
    assert(await page.locator('#model option[value="qwen-offline"]').isDisabled());
    await page.locator('#prompt').fill('Rascunho local preservado');
    await page.locator('#revision').fill('0');
    await page.locator('#save').click();
    await page.getByText('Conflito: revisão atual 2.', {exact: false}).waitFor();
    assert.equal(await page.locator('#prompt').inputValue(), 'Rascunho local preservado');
    await page.locator('#required-caveats').fill('Rascunho literal');
    await page.locator('#criteria-revision').fill('0');
    await page.locator('#save-criteria').click();
    await page.locator('#criteria-conflict').getByText('Conflito: revisão atual 2.', {exact: false}).waitFor();
    assert.equal(await page.locator('#required-caveats').inputValue(), 'Rascunho literal');
    await page.locator('#question').fill('falha de modelo');
    await page.locator('#run').click();
    await page.locator('#result').getByText('ModelOffline').waitFor();
    await page.locator('#question').fill('falha de consulta');
    await page.locator('#run').click();
    await page.locator('#result').getByText('QueryUnavailable').waitFor();
    modelsOnline = false;
    await page.locator('#refresh-models').click();
    await page.locator('#question').fill('Rascunho sem modelo');
    await page.locator('#run').click();
    await page.getByText('Nenhum modelo disponível.', {exact: false}).waitFor();
    assert.equal(await page.locator('#question').inputValue(), 'Rascunho sem modelo');
    assert.equal(errors.length, 0, errors.join('; '));
    const dimensions = await page.evaluate(() => ({viewport: innerWidth,
      pageWidth: document.documentElement.scrollWidth}));
    assert.equal(dimensions.pageWidth, dimensions.viewport, 'Mobile layout must not scroll horizontally');
    fs.mkdirSync(path.dirname(output), {recursive: true});
    await page.screenshot({path: output, fullPage: true});
    await page.setViewportSize({width: 1280, height: 900});
    const columns = await page.locator('#comparison > div').evaluateAll(items => items.map(item => item.getBoundingClientRect().x));
    assert(columns.length >= 2 && columns[0] !== columns[1], 'Desktop comparison must show columns side by side');
    await page.screenshot({path: desktopOutput, fullPage: true});
    console.log(`SPEC-004 browser flows passed: 2 revisions, 4 runs, comparison, conflicts, query/model failures, unavailable model, mobile and desktop layouts. Screenshots: ${output}, ${desktopOutput}`);
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
