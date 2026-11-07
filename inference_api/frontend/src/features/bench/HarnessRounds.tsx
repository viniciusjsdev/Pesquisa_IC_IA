import { useState } from 'react';
import type { Run } from './benchService';
import { ReadableAnswer } from './ReadableAnswer';

/* Snapshots are immutable, but older and partial v6 traces may omit fields. */
/* eslint-disable @typescript-eslint/no-explicit-any */

const roleNames: Record<string, string> = {
  analista_pergunta: 'Analista da Pergunta',
  selecionador_fontes: 'Selecionador de Fontes',
  planejador_consulta: 'Planejador da Consulta',
  revisor_evidencias: 'Revisor das Evidências',
  redator_resposta: 'Redator da Resposta',
  synthetic_query: 'Consulta à fixture sintética',
  data_query: 'Consulta aos bancos aprovados',
};

function specialistName(domain: string | undefined): string {
  return domain === 'dw' ? 'Especialista dos Dados Consolidados'
    : domain === 'industrial' ? 'Especialista dos Dados Industriais'
      : domain === 'financeiro' ? 'Especialista dos Dados Financeiros'
        : 'Especialista dos Dados';
}

const statusNames: Record<string, string> = {
  validated: 'Contrato validado',
  rejected: 'Rejeitada',
  provider_error: 'Erro do provedor',
  started: 'Iniciada',
};

function roleLabel(event: any): string {
  if (event.role === 'especialista_consulta') return `${specialistName(event.input?.input?.domain)} · ${event.input?.scenario === 'fixed_evidence' ? 'analisa pacote' : 'monta consulta'}`;
  if (event.role === 'especialista_indice') return `${specialistName(event.input?.input?.domain_index?.domain)} · escolhe tabelas`;
  if (event.role === 'especialista_dados') return `${specialistName(event.input?.input?.domain_detail?.domain || event.input?.input?.domain_map?.domain)} · analisa o detalhe`;
  return roleNames[event.role] || event.role || 'Papel não registrado';
}

function eventKind(event: any): 'assistant' | 'tool' {
  return ['synthetic_query', 'data_query', 'map_projection'].includes(event.role) ? 'tool' : 'assistant';
}

function toolLabel(event: any): string {
  return event.role === 'map_projection' ? 'Validação dos IDs e preparo do detalhe' : 'Serviço de consultas';
}

function agentName(event: any): string {
  if (event.role === 'especialista_consulta') return specialistName(event.input?.input?.domain);
  if (['especialista_indice', 'especialista_dados'].includes(event.role)) {
    return specialistName(event.input?.input?.domain_index?.domain || event.input?.input?.domain_detail?.domain || event.input?.input?.domain_map?.domain);
  }
  return roleLabel(event);
}

function eventSummary(event: any): string {
  if (event.status !== 'validated') return event.error ? `Falha registrada: ${event.error}` : 'Sem saída validada';
  const output = event.output || {};
  if (event.role === 'analista_pergunta') return `Domínios propostos: ${(output.dominios || []).join(', ') || 'nenhum'}`;
  if (event.role === 'especialista_indice') return `${output.table_ids?.length ?? 0} tabela(s) escolhida(s): ${(output.table_ids || []).join(', ') || 'nenhuma'}`;
  if (event.role === 'map_projection') return `${output.source_count ?? 0} tabela(s) validada(s); detalhe preparado pelo backend`;
  if (event.role === 'especialista_dados') return `${output.map_refs?.length ?? 0} referência(s) do mapa selecionada(s)`;
  if (event.role === 'selecionador_fontes') return `Decisão: ${output.decisao || 'não registrada'}${output.fonte_id ? ` · fonte ${output.fonte_id}` : ''}`;
  if (event.output?.action === 'analyze_packet') return `Análise do pacote: ${(output.findings || []).join(' · ')}`;
  if (['especialista_consulta', 'planejador_consulta'].includes(event.role)) return `Plano para ${output.plano?.fonte_id || 'fonte não registrada'}`;
  if (event.role === 'synthetic_query' || event.role === 'data_query') return `${output.coverage?.rows ?? output.rows?.length ?? '?'} linha(s) retornada(s) · ${output.result_id || 'sem ID'}`;
  if (event.role === 'revisor_evidencias') return `Decisão: ${output.decisao || 'não registrada'}`;
  if (event.role === 'redator_resposta') return output.resposta ? `Resposta registrada: ${String(output.resposta).slice(0, 110)}${String(output.resposta).length > 110 ? '…' : ''}` : 'Resposta sem texto';
  return 'Saída registrada';
}

function receivedSummary(event: any): string {
  if (event.role === 'analista_pergunta') return 'Pergunta inicial e índice dos domínios habilitados.';
  if (event.role === 'especialista_indice') return `Necessidade da pergunta e índice compacto do domínio ${event.input?.input?.domain_index?.domain || 'não registrado'}.`;
  if (event.role === 'map_projection') return 'Fonte selecionada e mapa versionado; o backend prepara o detalhe.';
  if (event.role === 'especialista_dados') return 'IDs validados e schema detalhado apenas das tabelas selecionadas.';
  if (event.role === 'selecionador_fontes') return event.input?.input?.source_index
    ? 'Pergunta, índice estático de fontes, evidências anteriores, lacuna e orçamento.'
    : 'Necessidade e trechos devolvidos pelos especialistas.';
  if (event.role === 'especialista_consulta' && event.input?.scenario === 'fixed_evidence') return 'Fonte e evidências integrais do pacote imutável, sem consulta.';
  if (event.role === 'especialista_consulta') return (event.input?.input?.correction_feedback || event.input?.input?.feedback)
    ? 'Pergunta, contrato completo da fonte, tentativa recusada, erro e saldo atualizado.'
    : 'Pergunta, contrato completo da fonte com tipos e filtros, evidências anteriores e limites.';
  if (event.role === 'planejador_consulta') return 'Fonte escolhida, trecho do mapa, evidências anteriores e limites.';
  if (event.role === 'synthetic_query' || event.role === 'data_query') return 'Plano tipado aprovado para o serviço de consultas.';
  if (event.role === 'revisor_evidencias') return 'Resultado da consulta, origem e evidências acumuladas.';
  if (event.role === 'redator_resposta') return 'Pergunta, evidências finais e limites registrados.';
  return 'Entrada estruturada registrada no trace.';
}

function returnedSummary(event: any): string {
  if (event.status !== 'validated') return event.error ? `Falha registrada: ${event.error}` : 'Sem saída validada.';
  if (event.role === 'revisor_evidencias' && event.output?.decisao === 'precisa_aprofundar') {
    return `Evidência insuficiente: ${event.output.lacuna || 'lacuna não registrada'}.`;
  }
  if (event.role === 'redator_resposta') return event.output?.resposta || 'Resposta sem texto registrado.';
  return eventSummary(event);
}

function json(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function JsonBlock({ value, empty }: { value: unknown; empty: string }) {
  return value == null ? <p className="harness-empty">{empty}</p> : <pre>{json(value)}</pre>;
}

export function HarnessRounds({ run }: { run: Run }) {
  const harness = run.snapshot?.harness_result;
  const realPilot = run.snapshot?.evidence_mode === 'agent_harness_pilot';
  const trace: any[] = Array.isArray(harness?.trace) ? harness.trace : [];
  const question = run.snapshot?.question_request?.question || trace.find(event => event.role === 'analista_pergunta')?.input?.input?.question;
  const firstModel = trace.find(event => event.model?.model_id)?.model;
  const model = run.snapshot?.model?.model_id || firstModel?.model_id;
  const provider = run.snapshot?.model?.provider || firstModel?.provider || run.snapshot?.provider;
  const agentCount = new Set(trace.filter(event => eventKind(event) === 'assistant').map(event => agentName(event))).size;
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<'input' | 'output' | 'technical'>('input');
  const selected = trace.find(event => event.event_id === selectedId) || trace[0];
  const investigation = trace.filter(event => event.role !== 'redator_resposta');
  const finalEvents = trace.filter(event => event.role === 'redator_resposta');
  const response = harness?.response;
  const caveats: string[] = Array.isArray(response?.ressalvas) ? response.ressalvas : [];
  const calculations: string[] = Array.isArray(response?.calculos) ? response.calculos : [];
  const evidenceRefs: string[] = Array.isArray(response?.evidencias_utilizadas) ? response.evidencias_utilizadas : [];
  const recordedEvidence: any[] = Array.isArray(harness?.evidence) ? harness.evidence : [];
  const rounds = [...new Set(investigation.map(event => Number(event.round) || 0))]
    .map(number => ({ number, events: investigation.filter(event => (Number(event.round) || 0) === number) }));
  const selectedIndex = trace.findIndex(event => event.event_id === selected?.event_id);
  const nextEvent = selectedIndex >= 0 ? trace[selectedIndex + 1] : undefined;

  function selectEvent(id: string) {
    setSelectedId(id);
    setDetailTab('input');
  }

  return <section className="harness-rounds" aria-label="Rodadas do Harness">
    <div className="harness-heading">
      <div><h4>Trajetória da execução</h4><p>Selecione uma etapa para entender a decisão; o JSON exato está nos detalhes da chamada.</p></div>
      <div className="harness-counts"><span>{harness?.model_calls ?? trace.filter(event => eventKind(event) === 'assistant').length} chamadas</span><span>{harness?.queries ?? trace.filter(event => ['synthetic_query', 'data_query'].includes(event.role) && event.status === 'validated').length} consultas</span><span>{rounds.length} rodadas</span></div>
    </div>
    <div className="harness-identity" aria-label="Identidade da execução">
      <strong>Uma IA, vários agentes internos</strong>
      <p>As etapas de Assistente usam o mesmo modelo em papéis diferentes. A Ferramenta é um serviço de consulta do backend, não outro agente.</p>
      <span>{provider && model ? `${provider} · ${model}` : model || 'Modelo não registrado'} · {agentCount} papel(is) registrado(s)</span>
    </div>
    <p className="harness-disclaimer">{run.snapshot?.schema_version === 7 ? (run.snapshot.data_class === 'synthetic_fixture' ? 'Fixture sintética declarada · validação local, sem provedor real.' : run.snapshot.scenario === 'fixed_evidence' ? 'Pacote fixo · sem consulta aos bancos durante o run.' : 'Consulta às fontes aprovadas · resposta sem avaliação científica.') : realPilot ? 'Dados reais consultados no piloto · resposta ainda sem avaliação científica.' : 'Fixture inventada · validação de contrato não é avaliação científica.'} Rodadas e chamadas refletem apenas eventos registrados no snapshot.</p>
    {trace.length === 0 ? <p className="harness-empty">Esta execução não registrou eventos de trajetória.</p> : <>
      <div className="harness-round-overview" aria-label="Visão geral das rodadas">
        {rounds.map(round => <div key={round.number} className="harness-round-overview-item"><strong>Rodada {round.number}</strong><span>{round.events.length} evento(s)</span><span>{round.events.some(event => event.status === 'rejected' || event.status === 'provider_error') ? 'Com falha ou correção' : 'Sem falhas registradas'}</span></div>)}
      </div>
      <div className="harness-trace-layout">
        <nav className="harness-event-list" aria-label="Chamadas por rodada">
          <div className="harness-user-message"><span className="harness-kind is-user">Usuário</span><strong>Pergunta inicial</strong><p>{question || 'Pergunta não registrada.'}</p><small>Entrada da execução · fora do trace de chamadas</small></div>
          {rounds.map(round => <details className="harness-round-group" key={round.number} open>
            <summary>Rodada {round.number} · {round.events.length} etapa(s)</summary>
            {round.events.map((event: any) => <button type="button" key={event.event_id} className={`harness-event ${selected?.event_id === event.event_id ? 'is-selected' : ''}`} aria-label={`${eventKind(event) === 'tool' ? `Ferramenta · ${toolLabel(event)}` : `Assistente · ${roleLabel(event)}`} · ${statusNames[event.status] || event.status || 'sem estado'}`} aria-current={selected?.event_id === event.event_id ? 'step' : undefined} onClick={() => selectEvent(event.event_id)}>
              <span className="harness-event-title"><span className={`harness-kind is-${eventKind(event)}`}>{eventKind(event) === 'tool' ? 'Ferramenta' : 'Assistente'}</span>{eventKind(event) === 'tool' ? toolLabel(event) : roleLabel(event)}</span>
              <span className="harness-event-meta">{event.event_id || 'sem ID'} · {statusNames[event.status] || event.status || 'sem estado'}{event.attempt > 1 ? ` · tentativa ${event.attempt}` : ''}</span>
              <span className="harness-event-summary">{eventSummary(event)}</span>
            </button>)}
          </details>)}
          {finalEvents.map(finalEvent => <button type="button" key={finalEvent.event_id} className={`harness-event harness-final-step ${selected?.event_id === finalEvent.event_id ? 'is-selected' : ''}`} aria-label={`Assistente · ${roleLabel(finalEvent)} · ${statusNames[finalEvent.status] || finalEvent.status}`} onClick={() => selectEvent(finalEvent.event_id)}><span className="harness-event-title"><span className="harness-kind is-assistant">Assistente</span>{roleLabel(finalEvent)}</span><span className="harness-event-meta">{finalEvent.event_id} · {statusNames[finalEvent.status] || finalEvent.status}{finalEvent.attempt > 1 ? ` · tentativa ${finalEvent.attempt}` : ''}</span><span className="harness-event-summary">{eventSummary(finalEvent)}</span></button>)}
        </nav>
        <div className="harness-event-detail" aria-live="polite">
          <h4>Etapa selecionada</h4>
          <div className="harness-event-detail-head"><div><span className="harness-kicker">{selected.event_id} · rodada {selected.round}</span><h5><span className={`harness-kind is-${eventKind(selected)}`}>{eventKind(selected) === 'tool' ? 'Ferramenta' : 'Assistente'}</span>{' '}{eventKind(selected) === 'tool' ? toolLabel(selected) : roleLabel(selected)}</h5><p className="harness-actor-note">{eventKind(selected) === 'tool' ? selected.role === 'map_projection' ? 'Validação e projeção executadas pelo backend; nenhuma consulta ao banco.' : 'Consulta executada pelo backend; não chama outro modelo.' : 'Papel interno da mesma IA desta execução.'}</p></div><span className={`harness-status is-${selected.status || 'unknown'}`}>{statusNames[selected.status] || selected.status || 'Estado não registrado'}</span></div>
          <p className="harness-detail-summary">{eventSummary(selected)}</p>
          <dl className="harness-stage-summary"><dt>Recebeu</dt><dd>{receivedSummary(selected)}</dd><dt>Devolveu</dt><dd>{returnedSummary(selected)}</dd><dt>Próxima ação registrada</dt><dd>{nextEvent ? `${eventKind(nextEvent) === 'tool' ? 'Ferramenta' : 'Assistente'} · ${eventKind(nextEvent) === 'tool' ? toolLabel(nextEvent) : roleLabel(nextEvent)}` : 'Execução encerrada.'}</dd></dl>
          {selected.attempt > 1 && <p>Correção visível · tentativa {selected.attempt}.</p>}
          {(selected.input?.source_event_ids || selected.source_event_ids)?.length > 0 && <p className="harness-sources"><strong>Eventos de origem registrados:</strong> {(selected.input?.source_event_ids || selected.source_event_ids).join(', ')}</p>}
          <div className="harness-detail-tabs" aria-label="Detalhes da chamada">
            {([['input', 'Entrada'], ['output', 'Saída'], ['technical', 'Rastreabilidade']] as const).map(([key, label]) => <button type="button" key={key} aria-pressed={detailTab === key} onClick={() => setDetailTab(key)}>{label}</button>)}
          </div>
          {detailTab === 'input' && <div className="harness-detail-body"><h6>{['synthetic_query', 'data_query'].includes(selected.role) ? 'Plano recebido pelo serviço de consultas' : selected.role === 'map_projection' ? 'IDs recebidos para validação' : 'Contexto recebido por este papel'}</h6><JsonBlock value={eventKind(selected) === 'tool' ? selected.input : selected.input?.input} empty="Entrada não registrada."/><details><summary>Envelope e referências exatas</summary><JsonBlock value={selected.input} empty="Envelope não registrado."/></details></div>}
          {detailTab === 'output' && <div className="harness-detail-body"><h6>Saída {selected.status === 'validated' ? 'validada pelo contrato' : 'registrada'}</h6><JsonBlock value={selected.output} empty="Sem saída validada nesta chamada."/>{selected.error && <p className="harness-error"><strong>Falha:</strong> {selected.error}{selected.retry_after ? ` · tentar após ${selected.retry_after}` : ''}</p>}{selected.raw_output != null && <details><summary>Saída bruta do modelo</summary><JsonBlock value={selected.raw_output} empty="Saída bruta não registrada."/></details>}</div>}
          {detailTab === 'technical' && <div className="harness-detail-body"><h6>Metadados do modelo</h6><JsonBlock value={selected.model} empty="Este evento não é uma chamada de modelo ou não possui metadados."/><details><summary>Evento integral do snapshot</summary><JsonBlock value={selected} empty="Evento indisponível."/></details></div>}
        </div>
      </div>
    </>}
    <section className="harness-final-answer" aria-label="Resposta final"><h4>Resposta final · Assistente / Redator</h4>
      <ReadableAnswer text={response?.resposta || run.snapshot?.model_output?.raw_text || 'Nenhuma resposta final registrada.'}/>
      {caveats.length > 0 && <div><h5>Ressalvas e limites</h5><ul>{caveats.map((text, index) => <li key={index}>{text}</li>)}</ul></div>}
      {calculations.length > 0 && <div><h5>Cálculos registrados</h5><ul>{calculations.map((text, index) => <li key={index}>{text}</li>)}</ul></div>}
      {evidenceRefs.length > 0 && <div><h5>Evidências utilizadas</h5><ul>{evidenceRefs.map(id => {
        const item = recordedEvidence.find(evidence => evidence.result_id === id);
        return <li key={id}><strong>{id}</strong>{item?.source_id ? ` · ${item.source_id}` : ' · detalhe não registrado'}{item?.grain ? ` · grão ${item.grain}` : ''}</li>;
      })}</ul></div>}
      <small>{run.snapshot?.status === 'answered_unverified' ? 'Resposta sem avaliação científica.' : 'Estado final registrado no snapshot.'}</small>
    </section>
    <details className="harness-provenance"><summary>Proveniência do caso e estado final</summary><dl><dt>Fingerprint do caso</dt><dd>{harness?.case_fingerprint || 'Não registrado'}</dd><dt>SHA-256 do contrato</dt><dd>{harness?.contract_sha256 || 'Não registrado'}</dd></dl><h5>Hashes dos mapas</h5><JsonBlock value={harness?.map_sha256} empty="Não registrados."/><h5>Estado final</h5><JsonBlock value={harness?.final_state} empty="Não registrado."/><h5>Evidências consultadas</h5><JsonBlock value={harness?.evidence} empty="Nenhuma evidência registrada."/></details>
  </section>;
}
