import type { Run } from './benchService';
// Evidence bundles retain historical fields from versioned backend snapshots.
/* eslint-disable @typescript-eslint/no-explicit-any */

function Field({ label, value }: { label: string; value: unknown }) {
  return <div className="bench-field"><strong>{label}</strong><span>{value === null || value === undefined || value === '' ? 'Não registrado' : String(value)}</span></div>;
}

export function RunDetail({ run }: { run: Run }) {
  const s = run.snapshot || {};
  const model = s.model || {};
  const bundle = s.evidence_bundle;
  if (s.schema_version === 3) return <article className="run-card"><h3>Execução {run.id}</h3>
    <Field label="Autor e data" value={`${run.author} · ${run.created_at}`}/><Field label="Estado" value={s.status}/>
    <Field label="Modo de evidência" value={s.evidence_mode === 'dw_snapshot' ? 'Pacote fixo da DW' : 'LLM consulta a DW por tools'}/>
    <p className="bench-notice">Execução exploratória; modos A e B respondem perguntas de avaliação distintas. Checks não são pontuação científica.</p>
    <section><h4>Pergunta e origem</h4><Field label="Pergunta" value={s.question_request?.question}/><Field label="Domínio" value={s.question_request?.domain}/><Field label="Pacote e hash" value={s.packet ? `${s.packet.case_id} · ${s.packet.sha256}` : 'Não se aplica'}/><Field label="Fingerprint da DW" value={s.packet?.source_snapshot?.source_fingerprint || s.dw_source?.source_fingerprint}/><Field label="Versões e hash da consulta" value={s.packet ? `${s.packet.schema_version} · ${s.packet.query_contract_version} · ${s.packet.query_code_sha256}` : `${s.dw_source?.schema_version ?? '?'} · ${s.dw_source?.query_contract_version ?? '?'} · ${s.dw_source?.query_code_sha256 ?? '?'}`}/></section>
    <section><h4>Prompt, critérios e modelo</h4><Field label="Prompt exato" value={s.prompt?.system_prompt}/><Field label="Revisão do prompt" value={s.prompt?.revision ?? 'Rascunho'}/><Field label="Revisão dos critérios" value={s.verification_criteria?.revision ?? 'Rascunho'}/><pre>{JSON.stringify(s.verification_criteria?.config || {}, null, 2)}</pre><Field label="Modelo servido e sessão" value={`${model.alias || '?'} · ${model.served_model || '?'} · ${model.session_id || '?'}`}/><pre>{JSON.stringify({ parameters: model.parameters, base_revision: model.base_revision, adapter_run: model.adapter_run, adapter_hash: model.adapter_hash }, null, 2)}</pre></section>
    <section><h4>Evidência entregue</h4>{s.evidence_mode === 'dw_snapshot' ? <><Field label="SHA-256 dos bytes do arquivo" value={s.packet?.file_sha256}/><pre>{s.evidence_json_sent || 'Pacote não entregue.'}</pre></> : <><details><summary>Catálogo anunciado</summary><pre>{JSON.stringify(s.tool_catalog || [], null, 2)}</pre></details><pre>{JSON.stringify(s.tool_trace || [], null, 2)}</pre></>}</section>
    <section><h4>Resposta, falhas e verificações</h4><Field label="Resposta bruta" value={s.model_output?.raw_text || 'Sem resposta'}/><pre>{JSON.stringify({ error: s.error, checks: s.checks }, null, 2)}</pre><details><summary>Turnos brutos do serving</summary><pre>{JSON.stringify(s.model_turns || [], null, 2)}</pre></details></section>
  </article>;
  return <article className="run-card">
    <h3>Execução {run.id}</h3><Field label="Autor e data" value={`${run.author} · ${run.created_at}`}/><Field label="Estado" value={s.status}/>
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
    <section><h4>Erro</h4><pre>{s.error ? JSON.stringify(s.error, null, 2) : 'Nenhum erro registrado.'}</pre></section>
  </article>;
}
