/* SPEC-009 browser smoke against local built UI; all API routes are mocked. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const origin = process.env.SPEC009_TEST_ORIGIN || 'http://127.0.0.1:8891';
const bi = JSON.parse(fs.readFileSync(path.join(root, 'private', 'bi_snapshot.json'), 'utf8'));
const output = path.join(root, '.local', 'spec009-browser');
const packet = { case_id: 'integrated-1', sha256: 'a'.repeat(64), question: 'Pergunta do pacote?', domain: 'integrado', source_snapshot: { source_fingerprint: 'b'.repeat(64) } };
const runs = [{ id: '00000000-0000-0000-0000-000000000001', author: 'Nicoli', created_at: '2026-10-15T00:00:00Z', snapshot: { schema_version: 2, status: 'answered_unverified', question_request: { question: 'Antiga', scope: 'financeiro', year: 2020 }, model: { alias: 'qwen-base' } } }];
let next = 2; let dwAvailable = true;
const reply = (route, status, body) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
function makeRun(body) {
  const snapshot = { schema_version: 3, evidence_mode: body.evidence_mode, status: 'answered_unverified', question_request: { question: body.evidence_mode === 'dw_snapshot' ? packet.question : body.question, domain: packet.domain }, prompt: { system_prompt: body.system_prompt, revision: null }, verification_criteria: { config: body.criteria }, model: { alias: body.model_alias, parameters: { temperature: body.temperature, max_tokens: body.max_tokens }, session_id: 'fixture-session', served_model: body.model_alias }, packet: body.evidence_mode === 'dw_snapshot' ? { case_id: packet.case_id, sha256: packet.sha256, file_sha256: 'c'.repeat(64), source_snapshot: packet.source_snapshot, schema_version: 1, query_contract_version: 1, query_code_sha256: 'd'.repeat(64) } : null, dw_source: body.evidence_mode === 'dw_tools' ? { source_fingerprint: 'b'.repeat(64), schema_version: 1, query_contract_version: 1 } : null, evidence_json_sent: body.evidence_mode === 'dw_snapshot' ? '{"fixture":"exact"}' : null, tool_catalog: body.evidence_mode === 'dw_tools' ? [{ function: { name: 'financial' } }] : null, tool_trace: body.evidence_mode === 'dw_tools' ? [{ order: 1, name: 'financial', validated_arguments: { year: 2020 }, result: { coverage: { state: 'observed', rows: 1 }, rows: [{ observation_id: 1 }] } }] : null, model_turns: [{ order: 1, serving: { session_id: 'fixture-session' } }], model_output: { raw_text: 'Resposta fixture' }, checks: [{ check: 'numerical_truth', result: 'not_checked', detail: 'No gold set' }], error: null };
  const run = { id: `00000000-0000-0000-0000-${String(next++).padStart(12, '0')}`, author: 'Nicoli', created_at: '2026-10-16T00:00:00Z', snapshot };
  runs.push(run); return run;
}
async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 850 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route(`${origin}/api/**`, route => {
    const pathname = new URL(route.request().url()).pathname;
    const body = route.request().postDataJSON?.() || {};
    if (pathname === '/api/login') return reply(route, 200, { token: 'fixture-token', username: 'Nicoli' });
    if (route.request().headers().authorization !== 'Bearer fixture-token') return reply(route, 401, { error: 'unauthorized' });
    if (pathname === '/api/me') return reply(route, 200, { id: 'fixture', username: 'Nicoli' });
    if (pathname === '/api/bi/snapshot') return reply(route, 200, bi);
    if (pathname === '/api/budget') return reply(route, 200, { session_ceiling_usd: 10, runpod_status: 'not_configured', runpod_balance_usd: null, runpod_spend_per_hour_usd: null, runpod_source: 'fixture', status_checked_at: '2026-10-16T00:00:00Z', checked_at: null });
    if (pathname === '/api/models') return reply(route, 200, { 'qwen-base': { available: true } });
    if (pathname === '/api/prompts' || pathname === '/api/criteria') return reply(route, 200, []);
    if (pathname === '/api/bench/evidence-packets') return reply(route, 200, [packet]);
    if (pathname === '/api/bench/dw-tools') return reply(route, 200, dwAvailable ? { available: true, source_fingerprint: 'b'.repeat(64) } : { available: false, reason: 'DW ausente' });
    if (pathname === '/api/runs' && route.request().method() === 'GET') return reply(route, 200, [...runs].reverse());
    if (pathname === '/api/runs' && route.request().method() === 'POST') { assert(body.evidence_mode); assert(!('scope' in body)); return reply(route, 201, makeRun(body)); }
    if (pathname.startsWith('/api/runs/')) return reply(route, 200, runs.find(item => item.id === pathname.split('/')[3]));
    return reply(route, 404, { error: 'not_found' });
  });
  try {
    await page.goto(origin);
    await page.locator('#password').fill('fixture-only');
    await page.locator('#login').click();
    await page.getByRole('button', { name: 'Bancada de testes' }).click();
    await page.locator('#evidence-mode').waitFor();
    assert.equal(await page.locator('#evidence-mode').inputValue(), '');
    assert(await page.locator('#run').isDisabled());
    await page.locator('#evidence-mode').selectOption('dw_snapshot');
    await page.locator('#packet').selectOption(`${packet.case_id}:${packet.sha256}`);
    assert.equal(await page.locator('#packet-question').inputValue(), packet.question);
    assert(await page.locator('#packet-question').getAttribute('readonly') !== null);
    await page.locator('#run').click();
    await page.locator('#result').getByText('Pacote fixo da DW').waitFor();
    await page.locator('#evidence-mode').selectOption('dw_tools');
    await page.locator('#question').fill('Pergunta livre');
    await page.locator('#run').click();
    await page.locator('#result').getByText('LLM consulta a DW por tools').waitFor();
    await page.locator('#runs').selectOption(runs[0].id);
    await page.locator('#run-detail').getByText('Fluxo anterior: escopo e consultas do backend.').waitFor();
    await page.locator('#compare-runs').selectOption(runs.slice(1).map(item => item.id));
    await page.locator('#compare').click();
    await page.getByText('Modos de evidência fixa e pesquisa por tools respondem perguntas de avaliação distintas.', { exact: false }).waitFor();
    dwAvailable = false;
    await page.getByText('Verificar DW').click();
    await page.getByText('Indisponível: DW ausente', { exact: false }).waitFor();
    assert(await page.locator('#run').isDisabled());
    await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 360, height: 740 });
    const width = await page.evaluate(() => document.documentElement.scrollWidth);
    assert(width <= 360, `mobile overflow ${width}`);
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
    assert.deepEqual(errors, []);
    console.log(`SPEC-009 browser modes, history and comparison passed: ${output}`);
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
