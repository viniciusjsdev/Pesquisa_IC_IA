import { useState } from 'react';
import type { Run } from './benchService';
import { runStatusLabel } from './runPresentation';
import { ReadableAnswer } from './ReadableAnswer';

/* Historical snapshots have different shapes; display only fields actually recorded. */
/* eslint-disable @typescript-eslint/no-explicit-any */

type Step = {
  id: string;
  kind: 'evidence' | 'assistant' | 'tool';
  title: string;
  summary: string;
  received: unknown;
  returned: unknown;
  technical: unknown;
  receivedSummary: string;
  returnedSummary: string;
  status: string;
};

function pretty(value: unknown) {
  return value == null ? 'Não registrado neste snapshot.' : typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

function buildSteps(snapshot: Record<string, any>): Step[] {
  const turns: any[] = Array.isArray(snapshot.model_turns) ? snapshot.model_turns : [];
  const tools: any[] = Array.isArray(snapshot.tool_trace) ? snapshot.tool_trace : [];
  const steps: Step[] = [];
  if (snapshot.evidence_mode === 'dw_snapshot' || snapshot.evidence_mode === 'synthetic_snapshot') {
    steps.push({ id: 'evidence', kind: 'evidence', title: 'Evidência fixa entregue',
      summary: snapshot.packet?.case_id ? `Pacote ${snapshot.packet.case_id} · sem consulta durante o run` : 'Fixture fixa · sem consulta durante o run',
      received: snapshot.question_request?.question,
      returned: snapshot.evidence_json_sent,
      technical: snapshot.packet || snapshot.evidence_source,
      receivedSummary: snapshot.question_request?.question || 'Pergunta não registrada.',
      returnedSummary: snapshot.evidence_json_sent ? 'Pacote fixo anexado ao pedido do modelo.' : 'Pacote não registrado neste snapshot.',
      status: snapshot.evidence_json_sent ? 'Registrada' : 'Não registrada' });
  }
  const toolByOrder = new Map<number, any>(tools.map(tool => [Number(tool.order), tool]));
  turns.forEach((turn, index) => {
    const order = Number(turn.order) || index + 1;
    const tool = toolByOrder.get(order);
    const isFinal = !tool && index === turns.length - 1;
    const messages: any[] = Array.isArray(turn.request?.messages) ? turn.request.messages : [];
    const toolResults = messages.filter(message => message.role === 'tool').length;
    const offeredTools = Array.isArray(turn.request?.tools) ? turn.request.tools.length : 0;
    steps.push({ id: `turn-${index}`, kind: 'assistant', title: `Assistente · turno ${order}`,
      summary: turn.error ? 'Falha registrada na chamada do modelo' : tool ? `Solicitou a ferramenta ${tool.name || tool.raw_request?.function?.name || 'sem nome'}` : isFinal && snapshot.model_output?.raw_text ? 'Produziu a resposta final' : 'Chamada do modelo registrada',
      received: turn.request,
      returned: turn.error || (tool ? tool.raw_request : isFinal ? snapshot.model_output?.raw_text : null),
      technical: { order: turn.order, started_at: turn.started_at, finished_at: turn.finished_at, serving: turn.serving },
      receivedSummary: !turn.request ? 'Pedido ao modelo não registrado neste snapshot.' : toolResults
        ? `Pergunta e contexto acumulado, com ${toolResults} resultado(s) de ferramenta.`
        : offeredTools ? `Pergunta e instruções, com ${offeredTools} tool(s) disponíveis para escolha.`
          : 'Pergunta, instruções e evidência fixa quando aplicável.',
      returnedSummary: turn.error ? 'A chamada terminou com falha registrada.' : tool
        ? `Pedido para a ferramenta ${tool.name || tool.raw_request?.function?.name || 'sem nome'}.`
        : isFinal && snapshot.model_output?.raw_text ? 'Resposta final registrada abaixo.' : 'Saída do turno não registrada neste snapshot.',
      status: turn.error ? 'Falhou' : 'Registrado' });
    if (tool) {
      steps.push({ id: `tool-${index}`, kind: 'tool', title: `Ferramenta · ${tool.name || tool.raw_request?.function?.name || 'consulta'}`,
        summary: tool.status === 'returned' ? `${tool.result?.coverage?.rows ?? tool.result?.rows?.length ?? '?'} linha(s) retornada(s)` : `Estado: ${tool.status || 'não registrado'}`,
        received: { request: tool.raw_request, validated_arguments: tool.validated_arguments },
        returned: tool.result || tool.error,
        technical: { order: tool.order, started_at: tool.started_at, finished_at: tool.finished_at, result_bytes: tool.result_bytes },
        receivedSummary: tool.validated_arguments ? `Pedido ${tool.name || 'de consulta'} com argumentos validados: ${JSON.stringify(tool.validated_arguments)}.` : 'Pedido da ferramenta registrado; argumentos validados indisponíveis.',
        returnedSummary: tool.status === 'returned' ? `${tool.result?.coverage?.rows ?? tool.result?.rows?.length ?? '?'} linha(s) retornada(s); cobertura ${tool.result?.coverage?.state || 'não registrada'}.` : `Resultado não disponível; estado ${tool.status || 'não registrado'}.`,
        status: tool.status === 'returned' ? 'Retornou' : tool.status === 'failed' ? 'Falhou' : tool.status || 'Não registrado' });
    }
  });
  tools.filter(tool => !turns.some((turn, index) => (Number(turn.order) || index + 1) === Number(tool.order)))
    .forEach((tool, index) => steps.push({ id: `unmatched-tool-${index}`, kind: 'tool', title: `Ferramenta · ${tool.name || tool.raw_request?.function?.name || 'consulta'}`,
      summary: 'Registro de ferramenta sem turno do modelo correspondente neste snapshot',
      received: { request: tool.raw_request, validated_arguments: tool.validated_arguments }, returned: tool.result || tool.error,
      technical: tool, receivedSummary: 'Pedido de ferramenta registrado sem turno correspondente.',
      returnedSummary: tool.status === 'returned' ? `${tool.result?.coverage?.rows ?? tool.result?.rows?.length ?? '?'} linha(s) retornada(s).` : 'Resultado não registrado.',
      status: tool.status || 'Não registrado' }));
  return steps;
}

export function EvidenceTrajectory({ run }: { run: Run }) {
  const snapshot = run.snapshot || {};
  const mode = snapshot.evidence_mode;
  const isFixed = mode === 'dw_snapshot' || mode === 'synthetic_snapshot';
  const synthetic = mode?.startsWith('synthetic_');
  const steps = buildSteps(snapshot);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<'received' | 'returned' | 'technical'>('received');
  const selected = steps.find(step => step.id === selectedId) || steps[0];
  const question = snapshot.question_request?.question;
  const answer = snapshot.model_output?.raw_text;

  return <div className="evidence-trajectory" aria-label="Trajetória da execução">
    <div className="harness-heading"><div><h4>{synthetic ? 'Diagnóstico sintético' : isFixed ? 'Cenário A · sem tools de navegação' : 'Cenário B · consulta à DW com tools'}</h4><p>{synthetic ? 'Fixture inventada; não é um dos dois cenários científicos.' : isFixed ? 'A evidência foi preparada antes da execução e entregue ao modelo.' : 'O modelo pode escolher consultas controladas; apenas pedidos e resultados registrados aparecem na ordem dos turnos.'}</p></div></div>
    <div className="harness-identity"><strong>Modelo configurado para esta execução</strong><span>{snapshot.model?.provider || snapshot.provider || 'Provedor não registrado'} · {snapshot.model?.model_id || snapshot.model?.alias || 'Modelo não registrado'}</span><p>Os turnos registrados são de um modelo. Este snapshot não identifica agentes internos separados.</p></div>
    <div className="harness-user-message"><span className="harness-kind is-user">Usuário</span><strong>Pergunta inicial</strong><p>{question || 'Pergunta não registrada neste snapshot.'}</p></div>
    <div className="harness-trace-layout">
      <nav className="harness-event-list" aria-label="Etapas registradas">
        <div className="harness-round-group"><h5>Ordem registrada</h5>
          {steps.map(step => <button key={step.id} type="button" className={`harness-event ${selected?.id === step.id ? 'is-selected' : ''}`} aria-current={selected?.id === step.id ? 'step' : undefined} aria-label={`${step.title} · ${step.status}`} onClick={() => { setSelectedId(step.id); setDetailTab('received'); }}>
            <span className="harness-event-title"><span className={`harness-kind is-${step.kind}`}>{step.kind === 'evidence' ? 'Entrada' : step.kind === 'tool' ? 'Ferramenta' : 'Assistente'}</span>{step.title.replace(/^Assistente · |^Ferramenta · /, '')}</span>
            <span className="harness-event-meta">{step.status}</span><span className="harness-event-summary">{step.summary}</span>
          </button>)}
          {!steps.length && <p className="harness-empty">Este snapshot não registra turnos nem ferramentas.</p>}
        </div>
      </nav>
      <div className="harness-event-detail" aria-live="polite">
        {selected ? <><div className="harness-event-detail-head"><div><span className="harness-kicker">Etapa registrada</span><h5>{selected.title}</h5></div><span className="harness-status">{selected.status}</span></div>
          <p className="harness-detail-summary">{selected.summary}</p>
          <div className="harness-detail-tabs" aria-label="Detalhes da etapa">
            {([['received', 'Recebeu'], ['returned', 'Devolveu'], ['technical', 'Rastreabilidade']] as const).map(([key, label]) => <button key={key} type="button" aria-pressed={detailTab === key} onClick={() => setDetailTab(key)}>{label}</button>)}
          </div>
          <div className="harness-detail-body">{detailTab === 'technical' ? <pre>{pretty(selected.technical)}</pre> : <><p className="evidence-detail-readable">{detailTab === 'received' ? selected.receivedSummary : selected.returnedSummary}</p><details><summary>Ver {detailTab === 'received' ? 'entrada' : 'saída'} exata</summary><pre>{pretty(detailTab === 'received' ? selected.received : selected.returned)}</pre></details></>}</div>
        </> : <p className="harness-empty">Selecione uma etapa quando a execução registrar eventos.</p>}
      </div>
    </div>
    <div className="harness-final-answer"><strong>Resposta final · Assistente</strong><ReadableAnswer text={answer || 'Nenhuma resposta final registrada.'}/><small>{runStatusLabel(snapshot.status)} · verificações exploratórias não são avaliação científica</small></div>
  </div>;
}
