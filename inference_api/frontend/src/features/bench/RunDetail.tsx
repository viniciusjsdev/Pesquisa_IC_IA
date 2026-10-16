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
  return <article className="run-card">
    <h3>Execução {run.id}</h3><Field label="Autor e data" value={`${run.author} · ${run.created_at}`}/><Field label="Estado" value={s.status}/>
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
