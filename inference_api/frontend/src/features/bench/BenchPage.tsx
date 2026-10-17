import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { errorMessage } from '../../services/api';
import { benchService, comparisonDifferences, type CriteriaConfig, type Run } from './benchService';
import { RunDetail } from './RunDetail';
import './bench.scss';

const money = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD' }).format(value);
const splitLines = (value: string) => value.split(/\r?\n/).map(line => line.trim()).filter(Boolean);

export function BenchPage() {
  const client = useQueryClient();
  const models = useQuery({ queryKey: ['bench', 'models'], queryFn: benchService.models });
  const prompts = useQuery({ queryKey: ['bench', 'prompts'], queryFn: benchService.prompts });
  const criteria = useQuery({ queryKey: ['bench', 'criteria'], queryFn: benchService.criteria });
  const runs = useQuery({ queryKey: ['bench', 'runs'], queryFn: benchService.runs });
  const budget = useQuery({ queryKey: ['bench', 'budget'], queryFn: benchService.budget, refetchInterval: 60_000 });
  const packets = useQuery({ queryKey: ['bench', 'packets'], queryFn: benchService.packets });
  const dwStatus = useQuery({ queryKey: ['bench', 'dwStatus'], queryFn: benchService.dwStatus });
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [promptName, setPromptName] = useState('Prompt exploratório');
  const [promptText, setPromptText] = useState('Responda somente com base nas evidências fornecidas. Cite os IDs usados e explicite limites.');
  const [promptRevision, setPromptRevision] = useState(0);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [promptConflict, setPromptConflict] = useState('');
  const [criteriaName, setCriteriaName] = useState('Critérios exploratórios');
  const [criteriaRevision, setCriteriaRevision] = useState(0);
  const [selectedCriteria, setSelectedCriteria] = useState('');
  const [criteriaConflict, setCriteriaConflict] = useState('');
  const [requireEvidence, setRequireEvidence] = useState(true);
  const [requirePeriod, setRequirePeriod] = useState(true);
  const [requireCitedIds, setRequireCitedIds] = useState(true);
  const [units, setUnits] = useState('');
  const [caveats, setCaveats] = useState('');
  const [question, setQuestion] = useState('');
  const [evidenceMode, setEvidenceMode] = useState('');
  const [packetKey, setPacketKey] = useState('');
  const [modelAlias, setModelAlias] = useState('');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(500);
  const [result, setResult] = useState<Run | null>(null);
  const [selectedRun, setSelectedRun] = useState('');
  const [historyRun, setHistoryRun] = useState<Run | null>(null);
  const [feedback, setFeedback] = useState('');
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<Run[]>([]);
  const [compareWarning, setCompareWarning] = useState('');

  const draft: CriteriaConfig = { schema_version: 1, require_evidence: requireEvidence, require_period: requirePeriod, required_units: splitLines(units), require_cited_ids: requireCitedIds, required_caveats: splitLines(caveats) };
  const available = Object.entries(models.data || {}).filter(([, item]) => item.available);
  const selectedAlias = modelAlias && models.data?.[modelAlias]?.available ? modelAlias : available[0]?.[0] || '';
  const budgetInfo = budget.data;
  const selectedPacket = packets.data?.find(item => `${item.case_id}:${item.sha256}` === packetKey);
  const budgetState = budgetInfo?.runpod_status === 'confirmed_read' ? 'leitura confirmada' : budgetInfo?.runpod_status === 'not_configured' ? 'chave de leitura não configurada' : 'falha na leitura';

  function conflict(error: unknown, setter: (message: string) => void, revisionSetter: (revision: number) => void) {
    if (axios.isAxiosError(error) && error.response?.status === 409) {
      const current = error.response.data?.current;
      if (current?.revision) revisionSetter(current.revision);
      setter(`Conflito: revisão atual ${current?.revision ?? 'mais recente'}. Seu rascunho permanece na tela.`);
    } else setter(errorMessage(error));
  }
  async function savePrompt() {
    setPromptConflict(''); setBusy(true);
    try { const item = await benchService.savePrompt(promptName, promptText, promptRevision); setPromptRevision(item.revision); setSelectedPrompt(item.id); await client.invalidateQueries({ queryKey: ['bench', 'prompts'] }); setMessage(`Revisão ${item.revision} salva.`); }
    catch (error) { conflict(error, setPromptConflict, setPromptRevision); }
    finally { setBusy(false); }
  }
  async function saveCriteria() {
    setCriteriaConflict(''); setBusy(true);
    try { const item = await benchService.saveCriteria(criteriaName, draft, criteriaRevision); setCriteriaRevision(item.revision); setSelectedCriteria(item.id); await client.invalidateQueries({ queryKey: ['bench', 'criteria'] }); setMessage(`Critérios revisão ${item.revision} salvos.`); }
    catch (error) { conflict(error, setCriteriaConflict, setCriteriaRevision); }
    finally { setBusy(false); }
  }
  async function execute() {
    if (!selectedAlias) { setMessage('Nenhum modelo disponível. Atualize o catálogo antes de executar.'); return; }
    if (!evidenceMode || (evidenceMode === 'dw_snapshot' && !selectedPacket) || (evidenceMode === 'dw_tools' && !question.trim())) { setMessage('Escolha um modo e preencha seus campos obrigatórios.'); return; }
    setBusy(true); setMessage('Executando…');
    try {
      const refreshed = await budget.refetch();
      if (axios.isAxiosError(refreshed.error) && refreshed.error.response?.status === 401) return;
      const body: Record<string, unknown> = { evidence_mode: evidenceMode, model_alias: selectedAlias, temperature, max_tokens: maxTokens };
      if (evidenceMode === 'dw_snapshot' && selectedPacket) { body.case_id = selectedPacket.case_id; body.packet_sha256 = selectedPacket.sha256; }
      if (evidenceMode === 'dw_tools') body.question = question;
      if (selectedPrompt) body.prompt_revision_id = selectedPrompt; else body.system_prompt = promptText;
      if (selectedCriteria) body.criteria_revision_id = selectedCriteria; else body.criteria = draft;
      const run = await benchService.execute(body);
      setResult(run); setMessage(`Execução ${run.id} registrada com estado ${run.snapshot.status}.`);
      await client.invalidateQueries({ queryKey: ['bench', 'runs'] });
    } catch (error) { setMessage(`Falha ao executar: ${errorMessage(error)} Rascunhos preservados.`); }
    finally { setBusy(false); }
  }
  async function loadRun(id: string) {
    setSelectedRun(id); setHistoryRun(null);
    if (!id) return;
    try { setHistoryRun(await benchService.run(id)); }
    catch (error) { setMessage(errorMessage(error)); }
  }
  async function saveFeedback() {
    if (!selectedRun) { setMessage('Selecione uma execução.'); return; }
    try { await benchService.feedback(selectedRun, feedback); setFeedback(''); setMessage('Feedback anexado sem alterar o snapshot.'); }
    catch (error) { setMessage(errorMessage(error)); }
  }
  async function compare() {
    if (compareIds.length < 2) { setCompareWarning('Selecione pelo menos duas execuções.'); return; }
    try { const selected = await Promise.all(compareIds.map(id => benchService.run(id))); const changed = comparisonDifferences(selected); setComparison(selected); setCompareWarning(`Modos de evidência fixa e pesquisa por tools respondem perguntas de avaliação distintas. ${changed.length ? `Insumos diferentes (${changed.join(', ')}).` : 'Insumos registrados iguais.'} Comparação exploratória; igualdade de insumos não comprova validade científica.`); }
    catch (error) { setCompareWarning(`Falha na comparação: ${errorMessage(error)}`); }
  }

  return <main className="bench-main"><div className="topline"><span>Pesquisa IC / Inteligência dos dados</span><span className="tag">BANCADA EXPLORATÓRIA</span></div>
    <div className="eyebrow">TESTES DE INFERÊNCIA</div><h1>Bancada de testes.</h1><p className="intro">Prompts, critérios, evidências e comparações exploratórias. Os checks não medem acurácia nem validam a pesquisa científica.</p>
    <div className="bench"><div className="bench-notice" role="status">{message || 'Catálogo, revisões e histórico carregados conforme a disponibilidade do banco.'}</div>
      <section className="bench-panel"><h2>Sessão e orçamento</h2><p>Teto manual da sessão: {money(budgetInfo?.session_ceiling_usd ?? 10)}. Saldo real da RunPod: {budgetInfo?.runpod_status === 'confirmed_read' && budgetInfo.runpod_balance_usd !== null ? money(budgetInfo.runpod_balance_usd) : 'indisponível'}. Gasto atual por hora: {budgetInfo?.runpod_status === 'confirmed_read' && budgetInfo.runpod_spend_per_hour_usd !== null ? `${money(budgetInfo.runpod_spend_per_hour_usd)}/hora` : 'não confirmado'}. Fonte: {budgetInfo?.runpod_source ?? 'não informada'}. Estado: {budgetState}. Consulta ao backend: {budgetInfo?.status_checked_at ? new Date(budgetInfo.status_checked_at).toLocaleString('pt-BR') : 'não consultado'}. Consulta à RunPod: {budgetInfo?.checked_at ? new Date(budgetInfo.checked_at).toLocaleString('pt-BR') : 'não consultado'}.</p><button onClick={() => void budget.refetch()}>Atualizar orçamento</button></section>
      <div className="bench-grid"><section className="bench-panel"><h2>Prompt versionado</h2><label htmlFor="saved-prompts">Revisão salva</label><select id="saved-prompts" value={selectedPrompt} onChange={e => { const id = e.target.value; setSelectedPrompt(id); const item = prompts.data?.find(prompt => prompt.id === id); if (item) { setPromptName(item.name); setPromptRevision(item.revision); setPromptText(item.system_prompt); } }}><option value="">Rascunho acima</option>{prompts.data?.map(item => <option key={item.id} value={item.id}>{item.name} · revisão {item.revision} · {item.author}</option>)}</select>
        <label htmlFor="prompt-name">Nome</label><input id="prompt-name" value={promptName} onChange={e => { setPromptName(e.target.value); setSelectedPrompt(''); }}/><label htmlFor="revision">Revisão esperada</label><input id="revision" type="number" min="0" value={promptRevision} onChange={e => setPromptRevision(Number(e.target.value))}/><label htmlFor="prompt">Texto do sistema</label><textarea id="prompt" rows={6} value={promptText} onChange={e => { setPromptText(e.target.value); setSelectedPrompt(''); }}/><button id="save" disabled={busy} onClick={() => void savePrompt()}>Salvar nova revisão</button>{promptConflict && <p id="prompt-conflict" role="alert" className="bench-error">{promptConflict}</p>}</section>
      <section className="bench-panel"><h2>Critérios versionados</h2><label htmlFor="saved-criteria">Revisão salva</label><select id="saved-criteria" value={selectedCriteria} onChange={e => { const id = e.target.value; setSelectedCriteria(id); const item = criteria.data?.find(criterion => criterion.id === id); if (item) { setCriteriaName(item.name); setCriteriaRevision(item.revision); setRequireEvidence(item.config.require_evidence); setRequirePeriod(item.config.require_period); setRequireCitedIds(item.config.require_cited_ids); setUnits(item.config.required_units.join('\n')); setCaveats(item.config.required_caveats.join('\n')); } }}><option value="">Rascunho acima</option>{criteria.data?.map(item => <option key={item.id} value={item.id}>{item.name} · revisão {item.revision} · {item.author}</option>)}</select>
        <label htmlFor="criteria-name">Nome</label><input id="criteria-name" value={criteriaName} onChange={e => { setCriteriaName(e.target.value); setSelectedCriteria(''); }}/><label htmlFor="criteria-revision">Revisão esperada</label><input id="criteria-revision" type="number" min="0" value={criteriaRevision} onChange={e => setCriteriaRevision(Number(e.target.value))}/>
        <label className="check"><input id="require-evidence" type="checkbox" checked={requireEvidence} onChange={e => { setRequireEvidence(e.target.checked); setSelectedCriteria(''); }}/> Exigir evidência</label><label className="check"><input id="require-period" type="checkbox" checked={requirePeriod} onChange={e => { setRequirePeriod(e.target.checked); setSelectedCriteria(''); }}/> Exigir período</label><label className="check"><input id="require-cited-ids" type="checkbox" checked={requireCitedIds} onChange={e => { setRequireCitedIds(e.target.checked); setSelectedCriteria(''); }}/> Exigir IDs citados</label>
        <label htmlFor="required-units">Unidades literais (uma por linha)</label><textarea id="required-units" rows={2} value={units} onChange={e => { setUnits(e.target.value); setSelectedCriteria(''); }}/><label htmlFor="required-caveats">Ressalvas literais (uma por linha)</label><textarea id="required-caveats" rows={2} value={caveats} onChange={e => { setCaveats(e.target.value); setSelectedCriteria(''); }}/><button id="save-criteria" disabled={busy} onClick={() => void saveCriteria()}>Salvar critérios</button>{criteriaConflict && <p id="criteria-conflict" role="alert" className="bench-error">{criteriaConflict}</p>}</section></div>
      <section className="bench-panel"><h2>Executar pergunta</h2><label htmlFor="evidence-mode">Modo de evidência</label><select id="evidence-mode" value={evidenceMode} onChange={e => { setEvidenceMode(e.target.value); setMessage(''); }}><option value="">Escolha um modo</option><option value="dw_snapshot">Pacote fixo da DW</option><option value="dw_tools">LLM consulta a DW por tools</option></select>
        {evidenceMode === 'dw_snapshot' && <div><p>Pacote candidato imutável preparado pela SPEC-007. A pergunta e o domínio vêm do pacote; não há consulta à DW durante esta execução.</p><label htmlFor="packet">Pacote privado</label><select id="packet" value={packetKey} onChange={e => setPacketKey(e.target.value)}><option value="">Escolha um pacote</option>{packets.data?.map(item => <option key={`${item.case_id}:${item.sha256}`} value={`${item.case_id}:${item.sha256}`}>{item.case_id} · {item.sha256.slice(0, 12)} · {item.domain}</option>)}</select><button onClick={() => void packets.refetch()}>Atualizar pacotes</button><label htmlFor="packet-question">Pergunta do pacote</label><textarea id="packet-question" readOnly value={selectedPacket?.question || ''}/>{!packets.data?.length && <p className="bench-notice">Sem pacotes. Prepare candidatos pelo exportador em model_evaluation/README.md e configure o diretório privado do servidor.</p>}</div>}
        {evidenceMode === 'dw_tools' && <div><p>A LLM escolhe entre cinco consultas fixas de leitura da DW. Resultados, chamadas e falhas ficam no histórico. {dwStatus.data?.available ? `DW disponível; fingerprint ${dwStatus.data.source_fingerprint}.` : `Indisponível: ${dwStatus.data?.reason || 'verificação pendente'}.`}</p><button onClick={() => void dwStatus.refetch()}>Verificar DW</button><label htmlFor="question">Pergunta livre</label><textarea id="question" rows={3} value={question} onChange={e => setQuestion(e.target.value)}/></div>}
        <div className="bench-fields"><div><label htmlFor="model">Alias do modelo</label><select id="model" value={selectedAlias} onChange={e => setModelAlias(e.target.value)}>{Object.entries(models.data || {}).map(([alias, item]) => <option key={alias} value={alias} disabled={!item.available}>{alias} · {item.available ? 'disponível' : 'indisponível'}</option>)}</select><button id="refresh-models" onClick={() => void models.refetch()}>Atualizar modelos</button></div><div><label htmlFor="temperature">Temperatura</label><input id="temperature" type="number" min="0" max="2" step="0.1" value={temperature} onChange={e => setTemperature(Number(e.target.value))}/></div><div><label htmlFor="max-tokens">Máximo de tokens</label><input id="max-tokens" type="number" min="1" value={maxTokens} onChange={e => setMaxTokens(Number(e.target.value))}/></div></div><button id="run" disabled={busy || !evidenceMode || !selectedAlias || (evidenceMode === 'dw_snapshot' && !selectedPacket) || (evidenceMode === 'dw_tools' && (!question.trim() || !dwStatus.data?.available))} onClick={() => void execute()}>Executar uma vez</button>{!available.length && <p className="bench-notice">Nenhum modelo disponível; a execução aguarda um endpoint servido.</p>}</section>
      <section className="bench-panel"><h2>Resultado e evidências</h2><div id="result">{result ? <RunDetail run={result}/> : <p>Nenhuma execução nesta sessão.</p>}</div></section>
      <div className="bench-grid"><section className="bench-panel"><h2>Histórico e feedback</h2><button id="refresh-runs" onClick={() => void runs.refetch()}>Atualizar histórico</button><label htmlFor="runs">Execução</label><select id="runs" value={selectedRun} onChange={e => void loadRun(e.target.value)}><option value="">Escolha uma execução</option>{runs.data?.map(item => <option key={item.id} value={item.id}>{item.created_at} · {item.author} · {item.snapshot.evidence_mode || 'fluxo anterior'} · {item.snapshot.model?.alias || '?'} · {item.snapshot.status}</option>)}</select><label htmlFor="feedback">Comentário humano</label><textarea id="feedback" value={feedback} onChange={e => setFeedback(e.target.value)}/><button id="save-feedback" onClick={() => void saveFeedback()}>Anexar feedback</button><div id="run-detail">{historyRun && <RunDetail run={historyRun}/>}</div></section>
      <section className="bench-panel"><h2>Comparação visual</h2><p>Selecione pelo menos duas execuções. Esta leitura não calcula acurácia.</p><label htmlFor="compare-runs">Execuções</label><select id="compare-runs" multiple size={Math.min(6, Math.max(2, runs.data?.length || 2))} value={compareIds} onChange={e => setCompareIds([...e.target.selectedOptions].map(option => option.value))}>{runs.data?.map(item => <option key={item.id} value={item.id}>{item.id.slice(0, 8)} · {item.snapshot.model?.alias || '?'} · {item.snapshot.status}</option>)}</select><button id="compare" onClick={() => void compare()}>Comparar</button><div id="compare-warning" role="status">{compareWarning}</div></section></div>
      {comparison.length > 0 && <div id="comparison" className="comparison">{comparison.map(item => <RunDetail key={item.id} run={item}/>)}</div>}
    </div>
  </main>;
}
