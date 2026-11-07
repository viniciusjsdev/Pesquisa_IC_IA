import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { errorMessage } from '../../services/api';
import { benchService, comparisonSummary, type Run } from './benchService';
import { RunDetail } from './RunDetail';
import { runDateLabel, runHistoryLabel, runScenarioLabel, runStatusLabel } from './runPresentation';
import './bench.scss';

export function BenchPage() {
  const client = useQueryClient();
  const models = useQuery({ queryKey: ['bench', 'models'], queryFn: benchService.models });
  const runs = useQuery({ queryKey: ['bench', 'runs'], queryFn: benchService.runs });
  const packets = useQuery({ queryKey: ['bench', 'packets'], queryFn: benchService.packets });
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [jobId, setJobId] = useState(() => sessionStorage.getItem('bench-uncertain-job') ? '' : sessionStorage.getItem('bench-active-job') || '');
  const [question, setQuestion] = useState('');
  const [evidenceMode, setEvidenceMode] = useState('');
  const [packetKey, setPacketKey] = useState('');
  const [modelAlias, setModelAlias] = useState('');
  const [temperature, setTemperature] = useState(0);
  const [outputLimit, setOutputLimit] = useState('');
  const [seed, setSeed] = useState('');
  const [reasoning, setReasoning] = useState('medium');
  const scenarios = useQuery({ queryKey: ['bench', 'scenarios'], queryFn: benchService.scenarios });
  const [result, setResult] = useState<Run | null>(null);
  const [selectedRun, setSelectedRun] = useState('');
  const [historySearch, setHistorySearch] = useState('');
  const [historyRun, setHistoryRun] = useState<Run | null>(null);
  const [feedback, setFeedback] = useState('');
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<Run[]>([]);
  const [compareWarning, setCompareWarning] = useState('');
  const [section, setSection] = useState<'setup' | 'rounds' | 'history'>('setup');

  const modelOptions = Object.entries(models.data || {});
  const selectedAlias = modelAlias;
  const profile = models.data?.[selectedAlias];
  const selectedPacket = packets.data?.find(item => `${item.case_id}:${item.sha256}` === packetKey);
  const filteredRuns = (runs.data || []).filter(item => {
    const search = historySearch.trim().toLocaleLowerCase('pt-BR');
    return !search || [item.id, item.snapshot?.question_request?.question, item.snapshot?.model?.alias,
      runScenarioLabel(item.snapshot?.evidence_mode),
      item.snapshot?.model?.model_id, runStatusLabel(item.snapshot?.status)]
      .some(value => String(value || '').toLocaleLowerCase('pt-BR').includes(search));
  });

  useEffect(() => { window.scrollTo({ top: 0, behavior: 'auto' }); }, [section]);

  useEffect(() => {
    if (jobId || sessionStorage.getItem('bench-uncertain-job')) return;
    const key = sessionStorage.getItem('bench-active-request-key');
    if (!key) return;
    void benchService.jobByKey(key).then(job => {
      sessionStorage.setItem('bench-active-job', job.id);
      setJobId(job.id);
    }).catch(error => {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        setMessage('Envio anterior ainda não foi encontrado. Verifique novamente e confira o histórico antes de liberar outro envio.');
      } else setMessage('Envio anterior ainda não pôde ser confirmado. Confira o histórico antes de executar novamente.');
    });
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const job = await benchService.job(jobId);
        if (!active) return;
        if (job.status === 'completed' && job.run_id) {
          const run = await benchService.run(job.run_id);
          if (!active) return;
          setResult(run);
          setHistoryRun(null);
          setSelectedRun('');
          setSection('rounds');
          setMessage(`Execução ${run.id} registrada com estado ${run.snapshot.status}.`);
          sessionStorage.removeItem('bench-active-job');
          sessionStorage.removeItem('bench-active-request-key');
          setJobId(''); setBusy(false);
          await client.invalidateQueries({ queryKey: ['bench', 'runs'] });
          return;
        }
        if (['failed', 'interrupted', 'busy'].includes(job.status)) {
          setMessage(`Job ${job.id} ${job.status}: ${job.error || 'desfecho incerto'}. Consulte o histórico e reconcilie a chave antes de outro POST.`);
          sessionStorage.removeItem('bench-active-job');
          sessionStorage.setItem('bench-uncertain-job', job.id);
          setJobId(''); setBusy(false);
          return;
        }
        setMessage(`Execução ${job.id}: ${job.status === 'running' ? 'modelo em execução' : 'aguardando início'}. A página pode ser atualizada.`);
      } catch (error) {
        if (active) setMessage(`Consulta do andamento falhou: ${errorMessage(error)}. A execução não será reenviada.`);
      }
      if (active) timer = setTimeout(() => void poll(), 2000);
    };
    void poll();
    return () => { active = false; clearTimeout(timer); };
  }, [jobId, client]);

  async function execute() {
    if (jobId || sessionStorage.getItem('bench-active-request-key')) { setMessage('Há um envio anterior pendente de reconciliação.'); return; }
    if (!selectedAlias) { setMessage('Nenhum modelo disponível. Atualize o catálogo antes de executar.'); return; }
    if (!evidenceMode || (evidenceMode === 'fixed_evidence' && !selectedPacket) || (evidenceMode === 'data_access' && !question.trim())) { setMessage('Escolha um modo e preencha seus campos obrigatórios.'); return; }
    setBusy(true); setMessage('Registrando execução…');
    const requestKey = crypto.randomUUID();
    try {
      const generation: Record<string, unknown> = { output_token_limit: outputLimit ? Number(outputLimit) : null };
      if (profile?.capabilities.temperature) generation.temperature = temperature;
      if (profile?.capabilities.seed && seed !== '') generation.seed = Number(seed);
      if (profile?.capabilities.reasoning_effort) generation.reasoning_effort = reasoning;
      const body: Record<string, unknown> = { execution_contract_version: 1, scenario: evidenceMode,
        model_profile_id: selectedAlias, generation,
        question: evidenceMode === 'fixed_evidence' ? selectedPacket?.question : question };
      if (evidenceMode === 'fixed_evidence') body.evidence_packet = { id: selectedPacket?.case_id, sha256: selectedPacket?.sha256 };
      else { body.evidence_packet = null; body.catalog_version = scenarios.data?.catalog_version; }
      sessionStorage.setItem('bench-active-request-key', requestKey);
      const job = await benchService.submit(body, requestKey);
      sessionStorage.setItem('bench-active-job', job.id);
      setJobId(job.id);
      setMessage(`Execução ${job.id} recebida; aguardando resultado.`);
    } catch (error) {
      if (axios.isAxiosError(error) && [400, 401, 403].includes(error.response?.status || 0)) {
        sessionStorage.removeItem('bench-active-request-key');
        setMessage(`Pedido recusado antes da criação do job: ${errorMessage(error)}.`);
        setBusy(false);
        return;
      }
      if (sessionStorage.getItem('bench-active-request-key') === requestKey) {
        try {
          const job = await benchService.jobByKey(requestKey);
          sessionStorage.setItem('bench-active-job', job.id);
          setJobId(job.id);
          setMessage(`Envio confirmado como ${job.id}; aguardando resultado.`);
          return;
        } catch (lookupError) {
          if (axios.isAxiosError(lookupError) && lookupError.response?.status === 404) {
            setMessage(`Envio ainda não encontrado após a falha: ${errorMessage(error)}. Verifique novamente; nenhum novo envio será feito.`);
            setBusy(false);
            return;
          }
        }
        setMessage(`Estado do envio incerto: ${errorMessage(error)}. Consulte o histórico antes de nova execução; nada será reenviado automaticamente.`);
      } else setMessage(`Falha antes do envio: ${errorMessage(error)}. Rascunhos preservados.`);
      setBusy(false);
    }
  }
  async function reconcilePending() {
    const key = sessionStorage.getItem('bench-active-request-key');
    if (!key) return;
    try {
      const job = await benchService.jobByKey(key);
      if (['failed', 'interrupted', 'busy'].includes(job.status)) {
        sessionStorage.setItem('bench-uncertain-job', job.id);
        setMessage(`Job ${job.id} permanece ${job.status}; confira o histórico pelo autor e horário antes de descartar a referência.`);
        await client.invalidateQueries({ queryKey: ['bench', 'runs'] });
        return;
      }
      sessionStorage.removeItem('bench-uncertain-job');
      sessionStorage.setItem('bench-active-job', job.id);
      setJobId(job.id);
      setMessage(`Envio ${job.id} confirmado; consultando resultado.`);
    } catch (error) {
      setMessage(axios.isAxiosError(error) && error.response?.status === 404
        ? 'Envio ainda não encontrado. Confira o histórico antes de descartar a referência.'
        : `Não foi possível consultar o envio: ${errorMessage(error)}.`);
    }
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
    try { const selected = await Promise.all(compareIds.map(id => benchService.run(id))); setComparison(selected); setCompareWarning(comparisonSummary(selected)); }
    catch (error) { setCompareWarning(`Falha na comparação: ${errorMessage(error)}`); }
  }

  const viewedRun = historyRun || result;
  const trajectoryHint = viewedRun?.snapshot?.schema_version === 7
    ? 'Papéis, evidências, consultas e recibos do cenário selecionado.'
    : 'Trajetória histórica no contrato original.';

  return <main className="bench-main"><div className="topline"><span>Pesquisa IC / Inteligência dos dados</span><span className="tag">BANCADA EXPLORATÓRIA</span></div>
    <div className="eyebrow">TESTES DE INFERÊNCIA</div><h1>Bancada de testes.</h1><p className="intro">Escolha o cenário de evidências, acompanhe a sequência registrada e consulte execuções anteriores em áreas separadas. Os checks atuais não medem acurácia nem validam a pesquisa científica.</p>
    <nav className="bench-section-nav" aria-label="Áreas da Bancada">
      <button type="button" className={section === 'setup' ? 'is-active' : ''} aria-current={section === 'setup' ? 'page' : undefined} onClick={() => setSection('setup')}><strong>1 · Preparar execução</strong><span>Cenário, caso e modelo</span></button>
      <button type="button" className={section === 'rounds' ? 'is-active' : ''} aria-current={section === 'rounds' ? 'page' : undefined} onClick={() => setSection('rounds')}><strong>2 · Trajetória da execução</strong><span>Chamadas, ferramentas e resposta</span></button>
      <button type="button" className={section === 'history' ? 'is-active' : ''} aria-current={section === 'history' ? 'page' : undefined} onClick={() => setSection('history')}><strong>3 · Histórico</strong><span>Execuções salvas e comparação</span></button>
    </nav>
    <div className="bench"><div className="bench-notice" role="status">{message || 'Catálogo, revisões e histórico carregados conforme a disponibilidade do banco.'}</div>
      {section === 'setup' && <>
      <section className="bench-panel bench-setup-panel"><h2>1 · Cenário do teste</h2>
        <p>Os dois cenários usam Analista, Selecionador, Especialista, Revisor e Redator, com o mesmo modelo.</p>
        <div className="bench-scenario-grid" role="radiogroup" aria-label="Cenário do teste">
          <label className="bench-scenario"><input type="radio" name="test-scenario" value="fixed" checked={evidenceMode === 'fixed_evidence'} onChange={() => setEvidenceMode('fixed_evidence')}/><span><strong>A · Pacote fixo, sem consulta</strong><small>Agentes analisam evidências preparadas antes do run. Zero leituras dos bancos de pesquisa.</small></span></label>
          <label className="bench-scenario"><input type="radio" name="test-scenario" value="navigation" checked={evidenceMode === 'data_access'} onChange={() => setEvidenceMode('data_access')}/><span><strong>B · Consulta aos dados</strong><small>Agentes escolhem fontes da DW, industrial e financeiro; até três tentativas controladas.</small></span></label>
        </div>
      </section>
      <section className="bench-panel bench-setup-panel"><h2>2 · Caso e pergunta</h2>
        {evidenceMode === 'fixed_evidence' && <><label htmlFor="packet">Pacote de evidências</label><select id="packet" value={packetKey} onChange={e => setPacketKey(e.target.value)}><option value="">Escolha um pacote</option>{packets.data?.map(item => <option key={item.sha256} value={`${item.case_id}:${item.sha256}`}>{item.case_id} · {item.sha256.slice(0, 12)}</option>)}</select><p>{selectedPacket?.question}</p><p className="bench-subtle">Hash: {selectedPacket?.sha256 || 'Selecione um pacote'}. Consultas: 0.</p></>}
        {evidenceMode === 'data_access' && <><label htmlFor="question">Pergunta</label><textarea id="question" value={question} onChange={e => setQuestion(e.target.value)}/><p>Catálogo: {scenarios.data?.catalog_version || 'carregando'}. Fontes aprovadas; sem SQL livre.</p></>}
      </section>
      <section className="bench-panel bench-setup-panel"><h2>3 · Modelo e parâmetros</h2>
        <label htmlFor="model">Perfil do modelo</label><select id="model" value={selectedAlias} onChange={e => setModelAlias(e.target.value)}><option value="">Escolha um modelo</option>{modelOptions.map(([id, item]) => <option key={id} value={id} disabled={!item.configured}>{item.provider_id} · {item.requested_model || id} · {item.configured ? 'configurado' : 'não configurado'}</option>)}</select>
        <button onClick={() => void models.refetch()}>Atualizar modelos</button>
        {profile && <><p>{profile.reason}. Capacidades declaradas pelo servidor.</p>
          {profile.capabilities.temperature && <><label htmlFor="temperature">Temperatura</label><input id="temperature" type="number" min="0" max="2" step="0.1" value={temperature} onChange={e => setTemperature(Number(e.target.value))}/></>}
          {profile.capabilities.reasoning_effort && <><label htmlFor="reasoning">Esforço de raciocínio</label><select id="reasoning" value={reasoning} onChange={e => setReasoning(e.target.value)}><option value="low">Baixo</option><option value="medium">Médio</option><option value="high">Alto</option></select></>}
          {profile.capabilities.seed && <><label htmlFor="seed">Seed opcional</label><input id="seed" type="number" step="1" value={seed} onChange={e => setSeed(e.target.value)}/></>}
          <label htmlFor="output-limit">Limite de saída por chamada</label><input id="output-limit" type="number" min="1" max="8192" value={outputLimit} onChange={e => setOutputLimit(e.target.value)} placeholder={profile.capabilities.omit_output_limit ? 'Sem teto solicitado' : 'Limite obrigatório'}/><p>Sem teto solicitado mantém os limites do modelo e do provedor.</p></>}
      </section>
      <section className="bench-panel bench-setup-panel"><h2>4 · Executar</h2><p>Até 48 chamadas e três rodadas. Respostas permanecem sem pontuação científica. O servidor verifica destino e autorização antes do envio.</p>
        <button id="run" disabled={busy || !!jobId || !profile?.configured || !evidenceMode} onClick={() => void execute()}>Executar cenário</button>
        {sessionStorage.getItem('bench-active-request-key') && <><button onClick={() => void reconcilePending()}>Consultar envio pendente</button><p>Confira o histórico antes de descartar um envio incerto.</p></>}
      </section></>}
      {section === 'rounds' && <section className="bench-panel bench-rounds-panel"><div className="bench-section-heading"><div><h2>Trajetória de uma execução</h2><p>{trajectoryHint}</p></div><div className="bench-heading-actions">{historyRun && result && <button type="button" onClick={() => { setHistoryRun(null); setSelectedRun(''); }}>Ver execução desta sessão</button>}{historyRun && <button type="button" onClick={() => setSection('history')}>Voltar ao histórico</button>}</div></div>
        {!jobId && sessionStorage.getItem('bench-active-request-key') && <p><button onClick={() => void reconcilePending()}>Verificar envio anterior</button> <button onClick={() => { sessionStorage.removeItem('bench-active-request-key'); sessionStorage.removeItem('bench-uncertain-job'); setMessage('Referência descartada após conferência manual do histórico.'); }}>Descartar referência após conferir histórico</button></p>}
        <div id="result">{viewedRun ? <RunDetail run={viewedRun}/> : <div className="bench-empty-state"><strong>{jobId ? 'Execução em andamento' : 'Nenhuma execução selecionada'}</strong><p>{jobId ? 'O resultado aparecerá aqui quando o job terminar. A página pode ser atualizada.' : 'Prepare uma execução ou escolha um registro no histórico para ver suas rodadas.'}</p>{!jobId && <button type="button" onClick={() => setSection('history')}>Abrir histórico</button>}</div>}</div></section>}
      {section === 'history' && <>
      <div className="bench-grid bench-history-grid"><section className="bench-panel"><div className="bench-section-heading"><div><h2>Histórico e feedback</h2><p>Até 100 execuções recentes, da mais nova para a mais antiga. Datas no horário deste dispositivo.</p></div><div className="bench-heading-actions"><button id="refresh-runs" onClick={() => void runs.refetch()}>Atualizar histórico</button></div></div><label htmlFor="runs-search">Buscar por pergunta, modelo, estado ou ID</label><input id="runs-search" type="search" value={historySearch} onChange={e => setHistorySearch(e.target.value)} placeholder="Buscar nas execuções carregadas"/><div className="bench-run-list" aria-label="Execuções anteriores">{filteredRuns.map(item => <button type="button" key={item.id} className={`bench-run-item ${selectedRun === item.id ? 'is-selected' : ''}`} aria-current={selectedRun === item.id ? 'true' : undefined} onClick={() => void loadRun(item.id)}><span className="bench-run-item-meta">{runDateLabel(item.created_at)} · {item.snapshot?.model?.alias || item.snapshot?.model?.model_id || 'Modelo não registrado'}</span><strong>{item.snapshot?.question_request?.question || 'Pergunta não registrada'}</strong><span>{runScenarioLabel(item.snapshot?.evidence_mode)} · {runStatusLabel(item.snapshot?.status)}</span></button>)}{!filteredRuns.length && <p className="harness-empty">{runs.isLoading ? 'Carregando execuções…' : historySearch ? 'Nenhuma execução corresponde à busca.' : 'Nenhuma execução registrada.'}</p>}</div><div id="run-detail">{historyRun && <div className="bench-history-selection"><strong>{runHistoryLabel(historyRun)}</strong><p>{historyRun.snapshot?.question_request?.question || 'Pergunta não registrada.'}</p><button type="button" onClick={() => setSection('rounds')}>Abrir trajetória e resultado</button></div>}</div><label htmlFor="feedback">Comentário humano</label><textarea id="feedback" value={feedback} onChange={e => setFeedback(e.target.value)}/><button id="save-feedback" onClick={() => void saveFeedback()}>Anexar feedback</button></section>
      <section className="bench-panel"><h2>Comparação visual</h2><p>Selecione pelo menos duas execuções. Esta leitura não calcula acurácia.</p><label htmlFor="compare-runs">Execuções</label><select id="compare-runs" multiple size={Math.min(6, Math.max(2, runs.data?.length || 2))} value={compareIds} onChange={e => setCompareIds([...e.target.selectedOptions].map(option => option.value))}>{runs.data?.map(item => <option key={item.id} value={item.id}>{item.id.slice(0, 8)} · {item.snapshot.model?.alias || '?'} · {runStatusLabel(item.snapshot.status)}</option>)}</select><button id="compare" onClick={() => void compare()}>Comparar</button><div id="compare-warning" role="status">{compareWarning}</div></section></div>
      {comparison.length > 0 && <div id="comparison" className="comparison">{comparison.map(item => <article className="bench-comparison-card" key={item.id}><strong>{runHistoryLabel(item)}</strong><p><b>Pergunta:</b> {item.snapshot?.question_request?.question || 'Não registrada'}</p><p><b>Resposta:</b> {item.snapshot?.model_output?.raw_text || 'Sem resposta registrada'}</p><button type="button" onClick={() => { setHistoryRun(item); setSelectedRun(item.id); setSection('rounds'); }}>Abrir trajetória</button></article>)}</div>}
      </>}
    </div>
  </main>;
}
