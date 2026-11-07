/* SPEC-009/010 browser smoke against local built UI; all API routes are mocked. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium } = require('../frontend/node_modules/@playwright/test');
const root = path.resolve(__dirname, '..');
const origin = process.env.SPEC009_TEST_ORIGIN || 'http://127.0.0.1:8891';
const bi = JSON.parse(fs.readFileSync(path.join(root, 'private', 'bi_snapshot.json'), 'utf8'));
const output = path.join(root, '.local', 'spec009-browser');
const packet = { case_id: 'integrated-1', sha256: 'a'.repeat(64), question: 'Pergunta do pacote?', domain: 'integrado', source_snapshot: { source_fingerprint: 'b'.repeat(64) } };
const runs = [{ id: '00000000-0000-0000-0000-000000000001', author: 'Nicoli', created_at: '2026-10-15T00:00:00Z', snapshot: { schema_version: 2, status: 'answered_unverified', question_request: { question: 'Antiga', scope: 'financeiro', year: 2020 }, model: { alias: 'qwen-base' } } }];
let next = 2; let dwAvailable = true; let holdGroqJob = false; let failGroqJob = false; let groqPosts = 0; let openaiPosts = 0;
const jobs = new Map();
const reply = (route, status, body) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
function makeRun(body) {
  const synthetic = body.evidence_mode.startsWith('synthetic_');
  const snapshot = { schema_version: body.provider === 'openai' ? 5 : body.provider === 'groq' ? 4 : 3, provider: body.provider, evidence_source: synthetic ? { kind: 'synthetic_fixture', id: 'synthetic-v1' } : null, evidence_mode: body.evidence_mode, status: 'answered_unverified', data_destination: body.provider === 'openai' ? 'https://api.openai.com/v1/responses' : null, data_class: synthetic ? 'synthetic_fixture' : body.evidence_mode === 'dw_snapshot' ? 'selected_dw_packet' : 'dw_tool_results', evidence_bytes_sent: body.provider === 'openai' ? 123 : null, question_request: { question: synthetic ? 'Qual foi o valor fictício em 2020?' : body.evidence_mode === 'dw_snapshot' ? packet.question : body.question, domain: packet.domain }, prompt: { system_prompt: body.system_prompt, revision: null }, verification_criteria: { config: body.criteria }, model: { alias: body.model_alias, model_id: body.provider === 'openai' ? 'gpt-6-luna' : body.provider === 'groq' ? 'fixture-model' : null, api_surface: body.provider === 'openai' ? 'responses/v1' : null, parameters: { temperature: body.temperature, max_tokens: body.max_tokens }, session_id: synthetic ? null : 'fixture-session', served_model: body.provider === 'openai' ? 'gpt-6-luna' : body.provider === 'groq' ? 'fixture-model' : body.model_alias }, packet: body.evidence_mode === 'dw_snapshot' ? { case_id: packet.case_id, sha256: packet.sha256, file_sha256: 'c'.repeat(64), source_snapshot: packet.source_snapshot, schema_version: 1, query_contract_version: 1, query_code_sha256: 'd'.repeat(64) } : null, dw_source: body.evidence_mode === 'dw_tools' ? { database: 'db_pesquisa_dw', source_fingerprint: 'b'.repeat(64), schema_version: 1, query_contract_version: 1 } : null, evidence_json_sent: body.evidence_mode === 'dw_snapshot' || body.evidence_mode === 'synthetic_snapshot' ? '{"fixture":"exact"}' : null, tool_catalog: body.evidence_mode === 'dw_tools' ? [{ function: { name: 'financial' } }] : synthetic && body.evidence_mode === 'synthetic_tools' ? [{ function: { name: 'synthetic_metric' } }] : null, tool_trace: body.evidence_mode === 'dw_tools' ? [{ order: 1, name: 'financial', validated_arguments: { year: 2020 }, result: { coverage: { state: 'observed', rows: 1 }, rows: [{ observation_id: 1 }] } }] : synthetic && body.evidence_mode === 'synthetic_tools' ? [{ order: 1, name: 'synthetic_metric', validated_arguments: { year: 2020 }, result: { coverage: { state: 'observed' }, rows: [{ value: 42 }] } }] : null, model_turns: [{ order: 1, serving: { provider: body.provider } }], model_output: { raw_text: 'Resposta fixture' }, checks: [{ check: 'numerical_truth', result: 'not_checked', detail: 'No gold set' }], error: null };
  const run = { id: `00000000-0000-0000-0000-${String(next++).padStart(12, '0')}`, author: 'Nicoli', created_at: '2026-10-16T00:00:00Z', snapshot };
  runs.push(run); return run;
}
async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_EXECUTABLE || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 850 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  async function chooseMode(mode, alias) {
    if (mode === 'dw_snapshot') await page.getByRole('radio', { name: /A · Sem tools de navegação/ }).check();
    else if (mode === 'dw_tools') await page.getByRole('radio', { name: /B · Com tools de navegação/ }).check();
    else {
      const diagnostics = page.locator('.bench-diagnostics');
      if (!(await diagnostics.evaluate(element => element.open))) await diagnostics.locator('summary').click();
      await page.locator('#diagnostic-mode').selectOption(mode);
    }
    await page.locator('#model').selectOption(alias);
  }
  await page.route(`${origin}/api/**`, route => {
    const pathname = new URL(route.request().url()).pathname;
    const body = route.request().postDataJSON?.() || {};
    if (pathname === '/api/login') return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'Set-Cookie': 'inference_session=fixture-token; Path=/api; HttpOnly; SameSite=Strict' }, body: JSON.stringify({ username: 'Nicoli' }) });
    if (!route.request().headers().cookie?.includes('inference_session=fixture-token')) return reply(route, 401, { error: 'unauthorized' });
    if (pathname === '/api/me') return reply(route, 200, { id: 'fixture', username: 'Nicoli' });
    if (pathname === '/api/bi/snapshot') return reply(route, 200, bi);
    if (pathname === '/api/budget') return reply(route, 200, { session_ceiling_usd: 10, runpod_status: 'not_configured', runpod_balance_usd: null, runpod_spend_per_hour_usd: null, runpod_source: 'fixture', status_checked_at: '2026-10-16T00:00:00Z', checked_at: null });
    if (pathname === '/api/logout') return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'Set-Cookie': 'inference_session=; Path=/api; HttpOnly; SameSite=Strict; Max-Age=0' }, body: '{"status":"logged_out"}' });
    if (pathname === '/api/models') return reply(route, 200, { 'qwen-base': { available: true, provider: 'runpod' }, groq: { available: true, provider: 'groq', model_id: 'fixture-model' }, openai: { available: true, provider: 'openai', model_id: 'gpt-6-luna', dw_enabled: true } });
    if (pathname === '/api/prompts' || pathname === '/api/criteria') return reply(route, 200, []);
    if (pathname === '/api/bench/evidence-packets') return reply(route, 200, [packet]);
    if (pathname === '/api/bench/dw-tools') return reply(route, 200, dwAvailable ? { available: true, source_fingerprint: 'b'.repeat(64) } : { available: false, reason: 'DW ausente' });
    if (pathname === '/api/runs' && route.request().method() === 'GET') return reply(route, 200, [...runs].reverse());
    if (pathname === '/api/run-jobs' && route.request().method() === 'POST') {
      assert(body.evidence_mode); assert(!('scope' in body)); assert(body.request_key);
      if (body.provider === 'groq') { groqPosts++; assert(!('case_id' in body)); assert(!('question' in body)); assert(!('criteria' in body)); }
      if (body.provider === 'openai') { openaiPosts++; if (body.evidence_mode.startsWith('synthetic_')) assert(!('criteria' in body)); }
      const run = makeRun(body);
      const job = { id: body.request_key, status: body.provider === 'groq' && failGroqJob ? 'failed' : body.provider === 'groq' && holdGroqJob ? 'running' : 'completed', run_id: failGroqJob ? null : run.id, error: failGroqJob ? 'injected_failure' : null };
      jobs.set(body.request_key, job);
      return reply(route, 202, job);
    }
    if (pathname.startsWith('/api/run-jobs/by-key/')) return reply(route, 200, jobs.get(pathname.split('/').at(-1)));
    if (pathname.startsWith('/api/run-jobs/')) { const job = jobs.get(pathname.split('/').at(-1)); return reply(route, 200, holdGroqJob || job.status === 'failed' ? job : { ...job, status: 'completed' }); }
    if (pathname.startsWith('/api/runs/')) return reply(route, 200, runs.find(item => item.id === pathname.split('/')[3]));
    return reply(route, 404, { error: 'not_found' });
  });
  try {
    await page.goto(origin);
    await page.locator('#password').fill('fixture-only');
    await page.locator('#login').click();
    await page.getByRole('button', { name: 'Bancada de testes' }).click();
    await page.getByRole('radiogroup', { name: 'Cenário do teste' }).waitFor();
    assert.equal(await page.getByRole('radio', { checked: true }).count(), 0);
    assert(await page.locator('#run').isDisabled());
    await chooseMode('dw_snapshot', 'qwen-base');
    await page.locator('#packet').selectOption(`${packet.case_id}:${packet.sha256}`);
    assert.equal(await page.locator('#packet-question').inputValue(), packet.question);
    assert(await page.locator('#packet-question').getAttribute('readonly') !== null);
    await page.screenshot({ path: path.join(output, 'setup-a.png'), fullPage: true });
    await page.locator('#run').click();
    await page.locator('#result').getByText('Cenário A · sem tools de navegação').first().waitFor();
    await page.screenshot({ path: path.join(output, 'trajectory-a.png'), fullPage: true });
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('dw_tools', 'qwen-base');
    await page.locator('#question').fill('Pergunta livre');
    await page.screenshot({ path: path.join(output, 'setup-b.png'), fullPage: true });
    await page.locator('#run').click();
    await page.locator('#result').getByText('Cenário B · consulta à DW com tools').first().waitFor();
    await page.screenshot({ path: path.join(output, 'trajectory-b.png'), fullPage: true });
    await page.getByRole('button', { name: /Histórico Execuções salvas/ }).click();
    await page.getByRole('button', { name: /Antiga/ }).click();
    await page.locator('#run-detail').getByText('Antiga', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Abrir trajetória e resultado' }).click();
    await page.getByText('Este snapshot antigo não registra', { exact: false }).waitFor();
    await page.locator('#result summary').first().click();
    await page.locator('#result').getByText('Fluxo anterior: escopo e consultas do backend.').waitFor();
    await page.getByRole('button', { name: /Histórico Execuções salvas/ }).click();
    await page.locator('#compare-runs').selectOption(runs.slice(1).map(item => item.id));
    await page.locator('#compare').click();
    await page.getByText('Cenários com e sem tools exigem pergunta e condições controladas', { exact: false }).waitFor();
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    dwAvailable = false;
    await page.getByText('Verificar DW').click();
    await page.getByText('DW indisponível: DW ausente', { exact: false }).waitFor();
    assert(await page.locator('#run').isDisabled());
    await chooseMode('synthetic_snapshot', 'groq');
    holdGroqJob = true;
    await page.locator('#run').click();
    await page.getByText('A página pode ser atualizada.', { exact: false }).waitFor();
    await page.reload();
    await page.getByText('Conectado como Nicoli', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Bancada de testes' }).click();
    holdGroqJob = false;
    await page.locator('#result').getByText('Diagnóstico sintético').first().waitFor();
    assert.equal(groqPosts, 1, 'refresh must not resubmit');
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('synthetic_tools', 'groq');
    await page.locator('#run').click();
    await page.locator('#result').getByText('Diagnóstico sintético').first().waitFor();
    assert.equal(groqPosts, 2);
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('synthetic_snapshot', 'openai');
    assert(await page.locator('#temperature').isDisabled());
    await page.locator('#run').click();
    await page.locator('#result').getByText('gpt-6-luna').first().waitFor();
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('synthetic_tools', 'openai');
    await page.locator('#run').click();
    await page.locator('#result').getByText('Diagnóstico sintético').first().waitFor();
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('dw_snapshot', 'openai');
    await page.locator('#packet').selectOption(`${packet.case_id}:${packet.sha256}`);
    await page.locator('#run').click();
    await page.locator('#result').getByText('Cenário A · sem tools de navegação').first().waitFor();
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('dw_tools', 'openai');
    await page.locator('#question').fill('Pergunta livre OpenAI');
    dwAvailable = true;
    await page.getByText('Verificar DW').click();
    await page.locator('#run').click();
    await page.locator('#result').getByText('Cenário B · consulta à DW com tools').first().waitFor();
    assert.equal(openaiPosts, 4);
    await page.locator('#result .run-technical > summary').click();
    await page.locator('#result').getByText('API utilizada').waitFor();
    await page.getByRole('button', { name: /Preparar execução/ }).click();
    await chooseMode('synthetic_tools', 'groq');
    failGroqJob = true;
    await page.locator('#run').click();
    await page.getByText('injected_failure', { exact: false }).waitFor();
    assert(await page.locator('#run').isDisabled());
    assert.equal(groqPosts, 3);
    await page.reload();
    await page.getByText('Conectado como Nicoli', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Bancada de testes' }).click();
    assert(await page.locator('#run').isDisabled());
    await page.getByRole('button', { name: /Trajetória da execução/ }).click();
    await page.getByText('Verificar envio anterior').click();
    await page.getByText('permanece failed', { exact: false }).waitFor();
    assert.equal(groqPosts, 3, 'uncertain job must not resubmit');
    const harnessRun = { id: '00000000-0000-0000-0000-000000000099', author: 'Nicoli', created_at: '2026-11-01T15:00:00Z', snapshot: {
      schema_version: 6, evidence_mode: 'agent_harness', status: 'answered_unverified', provider: 'groq',
      question_request: { question: 'Quantas paradas houve no período fictício?' },
      model: { provider: 'groq', model_id: 'modelo-fixture' },
      harness_result: { model_calls: 3, queries: 0, response: { resposta: 'A fixture registra 90 paradas.' }, trace: [
        { event_id: 'call_01', role: 'especialista_indice', round: 1, status: 'validated', input: { input: { domain_index: { domain: 'industrial' } } }, output: { table_ids: ['paradas'] } },
        { event_id: 'map_01', role: 'map_projection', round: 1, status: 'validated', input: { selected_table_ids: ['paradas'] }, output: { source_count: 1 } },
        { event_id: 'call_02', role: 'especialista_dados', round: 1, status: 'validated', input: { input: { domain_detail: { domain: 'industrial' }, selected_table_ids: ['paradas'] } }, output: { map_refs: ['paradas.data'] } },
        { event_id: 'call_03', role: 'redator_resposta', round: 2, status: 'validated', input: { input: { evidence_state: [] } }, output: { resposta: 'A fixture registra 90 paradas.' } },
      ] } } };
    runs.push(harnessRun);
    await page.getByRole('button', { name: /Histórico Execuções salvas/ }).click();
    await page.locator('#refresh-runs').click();
    await page.getByRole('button', { name: /Quantas paradas houve no período fictício/ }).click();
    await page.getByRole('button', { name: 'Abrir trajetória e resultado' }).click();
    await page.getByRole('button', { name: /Especialista dos Dados Industriais · escolhe tabelas/ }).waitFor();
    await page.getByRole('button', { name: /Validação dos IDs e preparo do detalhe/ }).click();
    await page.getByText('IDs de tabelas escolhidos pelo especialista.').waitFor();
    await page.getByText('A fixture registra 90 paradas.', { exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, 'harness-v6.png'), fullPage: true });
    await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 360, height: 740 });
    const width = await page.evaluate(() => document.documentElement.scrollWidth);
    assert(width <= 360, `mobile overflow ${width}`);
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
    await page.getByRole('button', { name: 'Sair' }).click();
    await page.locator('#login').waitFor();
    await page.reload();
    await page.locator('#login').waitFor();
    assert.deepEqual(errors, []);
    console.log(`SPEC-009/010/012 browser modes, refresh, jobs and logout passed: ${output}`);
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
