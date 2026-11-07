import type { Run } from './benchService';
import { HarnessRounds } from './HarnessRounds';
import { EvidenceTrajectory } from './EvidenceTrajectory';
import { runDateLabel, runStatusLabel } from './runPresentation';
// Evidence bundles retain historical fields from versioned backend snapshots.
/* eslint-disable @typescript-eslint/no-explicit-any */

function Field({ label, value }: { label: string; value: unknown }) {
  return <div className="bench-field"><strong>{label}</strong><span>{value === null || value === undefined || value === '' ? 'Não registrado' : String(value)}</span></div>;
}

function ReadableAnswer({ value }: { value: string }) {
  return <p className="run-summary-copy">{value.split(/(\*\*[^*]+\*\*)/g).map((part, index) => part.startsWith('**') && part.endsWith('**')
    ? <strong key={index}>{part.slice(2, -2)}</strong> : part)}</p>;
}

const toolStatusLabel: Record<string, string> = { returned: 'concluída', failed: 'falhou', rejected: 'recusada' };
const checkLabel: Record<string, string> = {
  criteria_evidence_presence: 'Presença de evidência',
  criteria_period: 'Período informado',
  numerical_truth: 'Conferência dos números',
  causality: 'Análise de causalidade',
};
const checkResultLabel: Record<string, string> = {
  passed: 'Condição atendida',
  failed: 'Condição não atendida',
  not_checked: 'Não verificada',
  skipped: 'Não executada',
};

function RunSummary({ run }: { run: Run }) {
  const s = run.snapshot || {};
  const model = s.model || {};
  const question = s.question_request?.question;
  const answer = s.model_output?.raw_text;
  const mode = s.evidence_mode === 'dw_snapshot' ? 'Pacote fixo da DW'
    : s.evidence_mode === 'agent_harness' ? 'Agentes em sequência · fixture sintética'
    : s.evidence_mode === 'agent_harness_pilot' ? 'Agentes em sequência · consulta local em camadas'
    : s.evidence_mode === 'dw_tools' ? 'LLM consulta a DW por tools'
      : s.evidence_mode === 'synthetic_snapshot' ? 'Pacote sintético fixo'
        : s.evidence_mode === 'synthetic_tools' ? 'LLM escolhe tool sintética' : 'Fluxo histórico';
  const tools = Array.isArray(s.tool_trace) ? s.tool_trace : [];
  const checks = Array.isArray(s.checks) ? s.checks : [];
  const hostedReceivedDwResult = ['groq', 'openai'].includes(s.provider) && s.status === 'answered_unverified'
    && Array.isArray(s.model_turns) && s.model_turns.some((turn: any) =>
      turn.request?.messages?.some((message: any) => message.role === 'tool'));
  const source = s.evidence_mode === 'dw_tools' && s.dw_source?.database
    ? `${s.dw_source.database}: ${tools.filter((tool: any) => tool.status === 'returned').length} consulta(s) concluída(s)${hostedReceivedDwResult ? `; resultado enviado à ${s.provider === 'openai' ? 'OpenAI' : 'Groq'}` : ''}`
    : s.evidence_mode === 'agent_harness_pilot' ? 'DW e fontes de detalhe aprovadas; consulte o trace para ver quais resultados foram enviados'
    : s.evidence_mode === 'agent_harness' || s.evidence_mode?.startsWith('synthetic_') ? 'Fixture sintética inventada'
      : s.packet?.case_id ? `Pacote ${s.packet.case_id}`
      : s.dw_source?.database ? `Consulta registrada à ${s.dw_source.database}`
        : s.evidence_bundle?.items?.length ? `${s.evidence_bundle.items.length} item(ns) de evidência registrado(s)`
          : 'Origem não resumida neste snapshot';
  return <div className="run-summary">
    <p className="run-summary-meta">{runDateLabel(run.created_at)} <span>· horário deste dispositivo</span> · {run.author}</p>
    <p className={`run-summary-status ${s.status === 'answered_unverified' ? 'is-complete' : 'is-error'}`}><strong>{runStatusLabel(s.status)}</strong></p>
    <div className="run-summary-facts"><span>{s.provider || 'Provedor não registrado'}</span><span>{model.model_id || model.alias || 'Modelo não registrado'}</span><span>{mode}</span></div>
    <h4>Pergunta</h4><p className="run-summary-copy">{question || 'Pergunta não registrada neste snapshot.'}</p>
    <h4>Resposta</h4><ReadableAnswer value={answer || 'Nenhuma resposta foi registrada nesta execução.'}/>
    <h4>Evidência usada</h4><p className="run-summary-copy">{source}</p>
    {s.error?.message && <p className="run-summary-error"><strong>Falha registrada:</strong> {s.error.message}</p>}
    {tools.length > 0 && <p className="run-summary-tools"><strong>Ferramentas chamadas:</strong> {tools.map((tool: any) => `${tool.name || tool.raw_request?.function?.name || 'nome não registrado'} (${toolStatusLabel[tool.status] || tool.status || 'estado não registrado'})`).join(' · ')}</p>}
    {checks.length > 0 && <><h4>Verificações exploratórias</h4><ul className="run-summary-checks">{checks.map((check: any, index: number) => <li key={index}><strong>{checkLabel[check.check] || check.check || 'Verificação sem nome'}:</strong> {checkResultLabel[check.result] || check.result || 'Resultado não registrado'}</li>)}</ul></>}
    <p className="run-summary-caveat">Leitura exploratória. Essas verificações não medem acurácia nem validam a pesquisa científica.</p>
  </div>;
}

function exportRun(run: Run) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(run, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a'); link.href = url; link.download = `run-${run.id}.json`; link.click(); URL.revokeObjectURL(url);
}

export function RunDetail({ run }: { run: Run }) {
  const s = run.snapshot || {};
  const model = s.model || {};
  const bundle = s.evidence_bundle;
  if (s.schema_version === 7 || (s.schema_version === 6 && ['agent_harness', 'agent_harness_pilot'].includes(s.evidence_mode))) return <article className="run-card"><h3>Execução {run.id.slice(0, 8)}</h3><button onClick={() => exportRun(run)}>Exportar JSON original</button><HarnessRounds key={run.id} run={run}/></article>;
  if (s.schema_version === 3 || s.schema_version === 4 || s.schema_version === 5) return <article className="run-card"><h3>Execução {run.id.slice(0, 8)}</h3><button onClick={() => exportRun(run)}>Exportar JSON original</button><EvidenceTrajectory key={run.id} run={run}/><details className="run-technical"><summary>Detalhes técnicos e rastreabilidade</summary><Field label="ID completo" value={run.id}/>
    <Field label="Autor e data" value={`${run.author} · ${run.created_at}`}/><Field label="Estado" value={runStatusLabel(s.status)}/>
    <Field label="Provedor" value={s.provider || 'runpod (snapshot histórico)'}/><Field label="Modelo configurado" value={model.model_id || model.alias}/><Field label="API utilizada" value={model.api_surface}/><Field label="ID da resposta" value={model.response_id}/><Field label="ID da requisição" value={model.request_id}/><Field label="Classe e bytes da evidência nos pedidos tentados" value={s.schema_version === 5 ? `${s.data_class} · ${s.evidence_bytes_sent ?? 'não registrado'} bytes, incluindo reenvios da conversa` : null}/>
    <Field label="Modo de evidência" value={s.evidence_mode === 'dw_snapshot' ? 'Pacote fixo da DW' : s.evidence_mode === 'dw_tools' ? 'LLM consulta a DW por tools' : s.evidence_mode === 'synthetic_snapshot' ? 'Pacote sintético fixo' : 'LLM escolhe tool sintética'}/>
    <p className="bench-notice">Execução exploratória; modos A e B respondem perguntas de avaliação distintas. Checks não são pontuação científica.</p>
    <section><h4>Pergunta e origem</h4><Field label="Pergunta" value={s.question_request?.question}/><Field label="Domínio" value={s.question_request?.domain || (s.evidence_mode?.startsWith('synthetic_') ? 'fixture sintética' : null)}/><Field label="Pacote e hash" value={s.evidence_mode?.startsWith('synthetic_') ? 'synthetic-v1; hash privado não se aplica' : s.packet ? `${s.packet.case_id} · ${s.packet.sha256}` : 'Não se aplica'}/><Field label="Fingerprint da DW" value={s.evidence_mode?.startsWith('synthetic_') ? 'Não se aplica' : s.packet?.source_snapshot?.source_fingerprint || s.dw_source?.source_fingerprint}/><Field label="Versões e hash da consulta" value={s.evidence_mode?.startsWith('synthetic_') ? 'Fixture sintética v1; consulta privada não se aplica' : s.packet ? `${s.packet.schema_version} · ${s.packet.query_contract_version} · ${s.packet.query_code_sha256}` : `${s.dw_source?.schema_version ?? '?'} · ${s.dw_source?.query_contract_version ?? '?'} · ${s.dw_source?.query_code_sha256 ?? '?'}`}/><Field label="Destino configurado para resultados" value={s.data_destination}/></section>
    <section><h4>Prompt, critérios e modelo</h4><Field label="Prompt exato" value={s.prompt?.system_prompt}/><Field label="Revisão do prompt" value={s.prompt?.revision ?? 'Rascunho'}/><Field label="Revisão dos critérios" value={s.verification_criteria?.revision ?? 'Rascunho'}/><pre>{JSON.stringify(s.verification_criteria?.config || {}, null, 2)}</pre><Field label="Modelo servido e sessão" value={`${model.alias || '?'} · ${model.served_model || model.model_id || 'não confirmado'} · ${model.session_id || 'não se aplica'}`}/><pre>{JSON.stringify({ parameters: model.parameters, usage: model.usage, finish_reason: model.finish_reason, base_revision: model.base_revision, adapter_run: model.adapter_run, adapter_hash: model.adapter_hash }, null, 2)}</pre></section>
    <section><h4>Evidência entregue</h4><Field label="Origem" value={s.evidence_source?.kind || s.dw_source?.database || s.packet?.source_snapshot?.kind}/>{['dw_snapshot', 'synthetic_snapshot'].includes(s.evidence_mode) ? <><Field label="SHA-256 dos bytes do arquivo" value={s.packet?.file_sha256}/><pre>{s.evidence_json_sent || 'Pacote não entregue.'}</pre></> : <><details><summary>Catálogo anunciado</summary><pre>{JSON.stringify(s.tool_catalog || [], null, 2)}</pre></details><pre>{JSON.stringify(s.tool_trace || [], null, 2)}</pre></>}</section>
    <section><h4>Resposta, falhas e verificações</h4><Field label="Resposta bruta" value={s.model_output?.raw_text || 'Sem resposta'}/><pre>{JSON.stringify({ error: s.error, checks: s.checks }, null, 2)}</pre><details><summary>Turnos do provedor</summary><pre>{JSON.stringify(s.model_turns || [], null, 2)}</pre></details></section></details>
  </article>;
  return <article className="run-card">
    <h3>Execução {run.id.slice(0, 8)}</h3><button onClick={() => exportRun(run)}>Exportar JSON original</button><RunSummary run={run}/><details className="run-technical"><summary>Detalhes técnicos e rastreabilidade</summary><Field label="ID completo" value={run.id}/><Field label="Autor e data" value={`${run.author} · ${run.created_at}`}/><Field label="Estado" value={s.status}/>
    <p className="bench-notice">Fluxo anterior: escopo e consultas do backend.</p>
    {s.status === 'answered_unverified' && <p className="bench-notice">Respondido, sem validação científica.</p>}
    <section><h4>Pergunta e rota</h4><Field label="Pergunta" value={s.question_request?.question}/><Field label="Escopo e ano" value={`${s.question_request?.scope || '?'} · ${s.question_request?.year ?? '?'}`}/><Field label="Ferramentas e origem da escolha" value={`${(s.route_plan?.tools || []).join(', ') || 'Nenhuma'} · ${s.route_plan?.choice_origin || '?'}`}/></section>
    <section><h4>Prompt e critérios do snapshot</h4><Field label="Prompt exato" value={s.prompt?.system_prompt}/><Field label="Revisão do prompt" value={s.prompt?.revision ?? 'Rascunho'}/><Field label="Revisão dos critérios" value={s.verification_criteria?.revision ?? (s.verification_criteria ? 'Rascunho' : 'Anterior à SPEC-004')}/><pre>{s.verification_criteria ? JSON.stringify(s.verification_criteria.config, null, 2) : 'Critérios não registrados neste snapshot antigo.'}</pre></section>
    <section><h4>Modelo e parâmetros</h4><Field label="Alias e versão" value={`${model.alias || '?'} · base ${model.base_revision || 'não confirmada'} · adapter ${model.adapter_hash || 'não confirmado'}`}/><Field label="Run do adapter e modelo servido" value={`${model.adapter_run || 'não registrado'} · ${model.served_model || 'não registrado'}`}/><pre>{JSON.stringify(model.parameters || {}, null, 2)}</pre></section>
    <section><h4>Consulta, evidência e proveniência</h4>{!bundle?.items?.length && <p>Nenhum item de evidência registrado.</p>}
      {(bundle?.items || []).map((item: Record<string, any>) => <section key={item.id}><h5>Evidência {item.id}</h5><Field label="Origem" value={`${item.source_database}.${item.source_table} · ${(item.source_fields || []).join(', ')}`}/><Field label="Período e unidade" value={`${JSON.stringify(item.period)} · ${item.unit}`}/><Field label="Valor, registros e qualidade" value={`${item.value} · ${item.record_count} registros · ${item.quality}`}/><Field label="Fórmula e ressalva" value={`${item.formula || '?'} · ${item.limitation || '?'}`}/><Field label="Consulta fixa do backend" value={item.query_template}/><Field label="Parâmetros" value={JSON.stringify(item.query_parameters)}/></section>)}
      <Field label="Ressalvas do pacote" value={(bundle?.limitations || []).join(' · ') || 'Não registradas'}/>
    </section>
    <section><h4>Resposta</h4><Field label="Texto bruto" value={s.model_output?.raw_text || 'Sem resposta'}/><Field label="IDs citados" value={(s.model_output?.cited_evidence_ids || []).join(', ') || 'Nenhum'}/>{s.model_output?.serving && <details><summary>Resposta bruta do serving</summary><pre>{JSON.stringify(s.model_output.serving, null, 2)}</pre></details>}</section>
    <section><h4>Checks exploratórios</h4>{!s.checks?.length && <p>Nenhum check registrado.</p>}{(s.checks || []).map((check: Record<string, string>, index: number) => <Field key={index} label={`${check.check}: ${check.result}`} value={check.detail}/>)}</section>
    <section><h4>Erro</h4><pre>{s.error ? JSON.stringify(s.error, null, 2) : 'Nenhum erro registrado.'}</pre></section></details>
  </article>;
}
