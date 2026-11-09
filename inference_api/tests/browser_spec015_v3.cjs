/* Real local HTTP/API/auth/jobs/PostgreSQL, with explicitly synthetic model endpoint. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium } = require('../frontend/node_modules/@playwright/test');
const origin = process.env.SPEC015_TEST_ORIGIN;
const output = process.env.SPEC015_TEST_OUTPUT;
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' });
  const page = await browser.newPage({ viewport: {width:1280,height:900}, acceptDownloads:true });
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  const report={fixture:true, scenarios:[], downloads:[], page_errors:errors};
  try {
    await page.goto(origin);
    await page.locator('#username').selectOption('Vinicius');
    await page.locator('#password').fill('fixture-local-password');
    await page.locator('#login').click();
    await page.getByRole('button',{name:'Bancada de testes'}).click();
    await page.getByRole('radiogroup').waitFor();
    assert.equal(await page.getByRole('radio').count(),2);
    for (const adapter of ['openai_responses','groq_chat','chat_completions']) {
      for (const fixed of [true,false]) {
        await page.getByRole('button',{name:/1 · Preparar execução/}).click();
        await page.getByRole('radio',{name:fixed?/A · Pacote/:/B · Consulta/}).check();
        await page.locator('#model').selectOption('fixture-'+adapter);
        if(fixed) await page.locator('#packet').selectOption(await page.locator('#packet option[value^="v3-invented:"]').getAttribute('value'));
        else await page.locator('#question').fill('Compare as três fontes fictícias; associação não prova causalidade.');
        await page.locator('#run').click();
        await page.getByRole('region',{name:'Resposta final'}).waitFor({timeout:20000});
        await page.getByRole('region',{name:'Resposta final'}).getByText(/^Resposta (inventada|da fixture)/).waitFor();
        assert((await page.locator('.harness-disclaimer').textContent()).includes('Fixture sintética'));
        assert.equal(await page.locator('.harness-event-title').filter({hasText:'Serviço de consultas'}).count(),fixed?0:3);
        const downloadEvent=page.waitForEvent('download');
        await page.getByRole('button',{name:'Exportar JSON original'}).click();
        const download=await downloadEvent; const file=path.join(output,download.suggestedFilename()); await download.saveAs(file);
        const run=JSON.parse(fs.readFileSync(file,'utf8'));
        assert.equal(run.snapshot.scenario,fixed?'fixed_evidence':'data_access');
        assert.equal(run.snapshot.observability.state,'pending');
        assert((await page.locator('.bench-observability').textContent()).includes('LangSmith'));
        report.downloads.push({id:run.id,version:run.snapshot.schema_version});
        if (fixed && adapter==='openai_responses') {
          assert.equal(run.snapshot.scenario_contract_version,2);
          assert.equal(run.snapshot.harness_result.queries,0);
          await page.getByRole('button',{name:'Atualizar monitoramento',exact:true}).click();
          await page.getByRole('status').filter({hasText:'Não foi possível confirmar'}).waitFor();
          await page.getByRole('button',{name:'Atualizar monitoramento',exact:true}).click();
          await page.getByText('Etapas confirmadas no LangSmith.').waitFor();
          await page.getByRole('link',{name:'Abrir no LangSmith'}).waitFor();
          report.reconciliation_pending_then_verified=true;
        }
        report.scenarios.push({adapter,scenario:run.snapshot.scenario,status:run.snapshot.status});
        await page.screenshot({path:path.join(output,`${adapter}-${fixed?'A':'B'}.png`),fullPage:true});
        await page.reload();
        await page.getByRole('button',{name:'Bancada de testes'}).click();
        await page.getByRole('button',{name:/3 · Histórico/}).click();
        await page.locator('#runs-search').fill(run.id);
        await page.locator('.bench-run-item').first().click();
        await page.getByRole('button',{name:'Abrir trajetória e resultado'}).click();
        await page.getByRole('region',{name:'Resposta final'}).waitFor();
      }
    }
    await page.getByRole('button',{name:/1 · Preparar execução/}).click();
    await page.getByRole('radio',{name:/A · Pacote/}).check();
    await page.locator('#model').selectOption('fixture-groq_chat');
    await page.locator('#packet').selectOption(await page.locator('#packet option[value^="v3-absent:"]').getAttribute('value'));
    await page.locator('#run').click();
    await page.getByRole('region',{name:'Resposta final'}).waitFor({timeout:20000});
    report.absent_domain_partial_answer=true;
    await page.getByRole('button',{name:/1 · Preparar execução/}).click();
    await page.getByRole('radio',{name:/B · Consulta/}).check();
    await page.locator('#model').selectOption('fixture-groq_chat');
    await page.locator('#question').fill('erro fixture');
    await page.locator('#run').click();
    await page.locator('.bench-notice').filter({hasText:/contract_error/}).waitFor({timeout:20000});
    await page.getByRole('button',{name:/3 · Histórico/}).click();
    await page.locator('#runs-search').fill('Histórico preservado');
    await page.locator('.bench-run-item').first().click();
    await page.getByRole('button',{name:'Abrir trajetória e resultado'}).click();
    await page.getByRole('button',{name:'Exportar JSON original'}).waitFor();
    const legacyDownload=page.waitForEvent('download'); await page.getByRole('button',{name:'Exportar JSON original'}).click();
    const legacy=await legacyDownload; const legacyFile=path.join(output,'legacy.json'); await legacy.saveAs(legacyFile);
    assert.equal(JSON.parse(fs.readFileSync(legacyFile)).snapshot.schema_version,3);
    report.error_visible=true; report.legacy_export=true; report.refresh_reopen=true;
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify(report,null,2));
    console.log('SPEC-015 browser passed');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
