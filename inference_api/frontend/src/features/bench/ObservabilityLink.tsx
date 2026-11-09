import { privateTraceUrl, type Observability } from './observabilityPresentation';
import { useState } from 'react';
import { benchService, type ObservabilityCurrent } from './benchService';

export function ObservabilityLink({ value, current, runId }: {
  value?: Observability; current?: ObservabilityCurrent | null; runId?: string;
}) {
  return <ObservabilityDetails key={`${runId}:${current?.revision}:${current?.can_reconcile}`}
    value={value} current={current} runId={runId}/>;
}

function ObservabilityDetails({ value, current, runId }: {
  value?: Observability; current?: ObservabilityCurrent | null; runId?: string;
}) {
  const [updated, setUpdated] = useState(current);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const display = updated || value;
  if (!display || display.state === 'disabled') return null;
  const url = privateTraceUrl(display);
  const labels: Record<string, string> = { pending: 'Envio ao LangSmith pendente',
    submitted: 'Trajetória enviada ao LangSmith', partial: 'Envio parcial ao LangSmith',
    failed: 'Falha no envio ao LangSmith' };
  async function refresh() {
    if (!runId || loading) return;
    setLoading(true); setFailed(false);
    try { setUpdated(await benchService.reconcile(runId)); }
    catch { setFailed(true); }
    finally { setLoading(false); }
  }
  return <div className="bench-observability"><p>{labels[display.state || ''] || 'Estado de observabilidade indisponível'}</p>
    {updated?.remote_verified && <p>Etapas confirmadas no LangSmith.</p>}
    {updated?.last_checked_at && <p>Última conferência: {new Date(updated.last_checked_at).toLocaleString('pt-BR')}</p>}
    {(failed || updated?.last_check_error) && <p role="status">Não foi possível confirmar o monitoramento nesta consulta. O resultado da execução foi preservado.</p>}
    {url && <a href={url} target="_blank" rel="noopener noreferrer">Abrir no LangSmith</a>}
    {updated?.can_reconcile && runId && <button type="button" disabled={loading} onClick={() => void refresh()}>
      {loading ? 'Atualizando monitoramento…' : 'Atualizar monitoramento'}</button>}
    {!updated && <p>Atualização indisponível para este histórico.</p>}</div>;
}
