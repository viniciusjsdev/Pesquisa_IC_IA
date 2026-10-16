import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { errorMessage } from '../../services/api';
import { biService } from './biService';
import { csvText, renderBI } from './biRenderer';

export type BITab = 'overview' | 'financial' | 'industrial' | 'sources';

export function BIPage({ tab }: { tab: BITab }) {
  const query = useQuery({ queryKey: ['bi-snapshot'], queryFn: biService.snapshot });
  const years = useMemo(() => query.data ? [...new Set(Object.values(query.data.series).flatMap(rows => rows.map(row => Number(row.mes.slice(0, 4)))))].sort((a, b) => a - b) : [], [query.data]);
  const [start, setStart] = useState<number | null>(null);
  const [end, setEnd] = useState<number | null>(null);
  const [grain, setGrain] = useState<'year' | 'month'>('year');
  const from = start ?? years[0];
  const to = end ?? (years.includes(2025) ? 2025 : years.at(-1));
  const view = query.data && from !== undefined && to !== undefined ? renderBI(query.data, tab, from, to, grain) : null;

  function download() {
    if (!view) return;
    const url = URL.createObjectURL(new Blob([csvText(view.rows)], { type: 'text/csv;charset=utf-8' }));
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = `bi_pesquisa_${from}–${to}_${grain}.csv`;
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <main className="bi-main"><div className="topline"><span>Pesquisa IC <span className="divider">/</span> Inteligência dos dados</span><span className="tag">BASE SINTÉTICA</span></div>
    <div className="eyebrow">{view?.heading[0] || 'OBSERVATÓRIO DA OPERAÇÃO'}</div>
    <h1>{view?.heading[1] || 'Da fábrica ao resultado.'}</h1><p className="intro">{view?.heading[2] || 'Explore a evolução financeira e industrial da empresa.'}</p>
    <div className="toolbar" aria-label="Filtros">
      <div className="field"><label htmlFor="start">Ano inicial</label><select id="start" value={from ?? ''} disabled={!view} onChange={e => { const value = Number(e.target.value); setStart(value); if (to !== undefined && value > to) setEnd(value); }}>{years.map(year => <option key={year}>{year}</option>)}</select></div>
      <div className="field"><label htmlFor="end">Ano final</label><select id="end" value={to ?? ''} disabled={!view} onChange={e => { const value = Number(e.target.value); setEnd(value); if (from !== undefined && value < from) setStart(value); }}>{years.map(year => <option key={year}>{year}</option>)}</select></div>
      <div className="field"><label htmlFor="grain">Agrupar por</label><select id="grain" value={grain} onChange={e => setGrain(e.target.value as 'year' | 'month')}><option value="year">Ano</option><option value="month">Mês</option></select></div>
      <div className="spacer"/><button className="btn" id="download" disabled={!view} onClick={download}>↓ Exportar CSV</button>
    </div>
    {query.isLoading && <div className="loading" role="status">Carregando o retrato protegido…</div>}
    {query.isError && <div className="notice error" role="alert">Não foi possível ler o retrato. {errorMessage(query.error)}</div>}
    {view && <><div className={`notice${view.context.warning ? ' warning' : ''}`}>{view.context.text}</div><div id="content" dangerouslySetInnerHTML={{ __html: view.html }}/></>}
    <div className="footer"><span>Observatório · Dados sintéticos para pesquisa acadêmica<br/>Indicadores descritivos; relações causais não foram avaliadas.</span><span id="updated">{query.data ? `Retrato dos dados: ${new Date(query.data.snapshot_at).toLocaleString('pt-BR')} · versão offline, sem atualização automática` : 'Retrato indisponível'}</span></div>
  </main>;
}
