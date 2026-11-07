import type { Run } from './benchService';

const statusLabel: Record<string, string> = {
  answered_unverified: 'Resposta registrada, sem verificação científica',
  contract_error: 'Contrato dos agentes recusado',
  response_error: 'Resposta incompleta ou inválida',
  model_error: 'Falha na consulta ao modelo',
  tool_protocol_error: 'Falha no protocolo da ferramenta',
  dw_unavailable: 'DW indisponível',
  provider_bad_request: 'Pedido recusado pelo provedor (400)',
  provider_tool_error: 'Provedor recusou a chamada de tool (400)',
  provider_auth_error: 'Credencial do provedor recusada (401/403)',
  provider_rate_limited: 'Limite temporário do provedor (429)',
  provider_quota_exhausted: 'Créditos ou limite de gastos/uso esgotados',
  provider_unavailable: 'Provedor indisponível na configuração atual',
  provider_request_error: 'Pedido recusado pelo provedor',
  provider_model_mismatch: 'Modelo respondido difere do solicitado',
  provider_error: 'Falha do provedor (5xx)',
  provider_timeout: 'Tempo de espera do provedor esgotado',
  provider_connection_error: 'Conexão com o provedor falhou',
  stream_incomplete: 'Stream incompleto ou inválido',
  response_incomplete: 'Resposta incompleta do provedor',
  context_limit: 'Resposta truncada pelo limite de contexto',
  tool_error: 'Tool inválida',
  insufficient_evidence: 'Evidência insuficiente',
};

export function runStatusLabel(status: string | undefined) {
  return statusLabel[status || ''] || status || 'Estado não registrado';
}

export function runDateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('pt-BR', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

export function runScenarioLabel(mode: string | undefined) {
  if (mode === 'fixed_evidence') return 'A · pacote fixo';
  if (mode === 'data_access') return 'B · consulta aos dados';
  if (mode === 'dw_snapshot') return 'A · evidência fixa';
  if (mode === 'dw_tools') return 'B · consulta à DW';
  if (mode === 'agent_harness_pilot') return 'Piloto · consulta em camadas';
  if (mode === 'agent_harness' || mode?.startsWith('synthetic_')) return 'Diagnóstico sintético';
  return 'Fluxo anterior';
}

export function runHistoryLabel(run: Run) {
  const s = run.snapshot || {};
  const model = s.model || {};
  const question = String(s.question_request?.question || 'Pergunta não registrada').trim();
  return `${runDateLabel(run.created_at)} · ${runScenarioLabel(s.evidence_mode)} · ${model.alias || model.model_id || '?'} · ${runStatusLabel(s.status)} · ${question.slice(0, 55)}${question.length > 55 ? '…' : ''}`;
}
