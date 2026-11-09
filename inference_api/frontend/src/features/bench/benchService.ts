import { api } from '../../services/api';
// Historical run snapshots have multiple schema versions and are rendered read-only.
/* eslint-disable @typescript-eslint/no-explicit-any */

export type Prompt = { id: string; name: string; revision: number; author: string; system_prompt: string };
export type CriteriaConfig = { schema_version: 1; require_evidence: boolean; require_period: boolean; required_units: string[]; require_cited_ids: boolean; required_caveats: string[] };
export type Criterion = { id: string; name: string; revision: number; author: string; config: CriteriaConfig };
export type ObservabilityCurrent = { schema_version: 1; state: string; remote_verified: boolean;
  can_reconcile: boolean; trace_id: string; submitted_events: number; failed_events: number;
  dropped_events: number; pending_events: number; expected_events: number; observed_remote_events: number | null;
  url: string | null; trusted_origin: string | null; last_checked_at: string | null;
  last_check_error: string | null; revision: number };
export type Run = { id: string; author: string; created_at: string; snapshot: Record<string, any>; observability_current?: ObservabilityCurrent | null };
export type RunJob = { id: string; status: 'accepted' | 'running' | 'completed' | 'failed' | 'interrupted' | 'busy'; run_id: string | null; error: string | null; created_at: string; started_at: string | null; finished_at: string | null };
export type Model = { configured: boolean; availability: string; provider_id: string; requested_model: string; reason: string;
  capabilities: { temperature: boolean; reasoning_effort: boolean; seed: boolean; omit_output_limit: boolean; json_schema: string } };
export type Budget = { session_ceiling_usd: number; runpod_status: string; runpod_balance_usd: number | null; runpod_spend_per_hour_usd: number | null; runpod_source: string; status_checked_at: string; checked_at: string | null };
export type Packet = { case_id: string; sha256: string; question: string; domain: string; source_snapshot: { source_fingerprint: string } };
export type DWStatus = { available: boolean; reason?: string; source_fingerprint?: string };

export const benchService = {
  scenarios: async () => (await api.get<{scenarios: string[]; catalog_version: number}>('/bench/scenarios')).data,
  models: async () => (await api.get<Record<string, Model>>('/models')).data,
  prompts: async () => (await api.get<Prompt[]>('/prompts')).data,
  criteria: async () => (await api.get<Criterion[]>('/criteria')).data,
  runs: async () => (await api.get<Run[]>('/runs')).data,
  run: async (id: string) => (await api.get<Run>(`/runs/${encodeURIComponent(id)}`)).data,
  reconcile: async (id: string) => (await api.post<{observability_current: ObservabilityCurrent}>(`/runs/${encodeURIComponent(id)}/observability/reconcile`)).data.observability_current,
  budget: async () => (await api.get<Budget>('/budget')).data,
  packets: async () => (await api.get<Packet[]>('/bench/evidence-packets')).data,
  dwStatus: async () => (await api.get<DWStatus>('/bench/dw-tools')).data,
  savePrompt: async (name: string, system_prompt: string, expected_revision: number) => (await api.post<Prompt>('/prompts', { name, system_prompt, expected_revision })).data,
  saveCriteria: async (name: string, config: CriteriaConfig, expected_revision: number) => (await api.post<Criterion>('/criteria', { name, config, expected_revision })).data,
  submit: async (body: Record<string, unknown>, requestKey: string) => (await api.post<RunJob>('/run-jobs', { ...body, request_key: requestKey })).data,
  job: async (id: string) => (await api.get<RunJob>(`/run-jobs/${encodeURIComponent(id)}`)).data,
  jobByKey: async (key: string) => (await api.get<RunJob>(`/run-jobs/by-key/${encodeURIComponent(key)}`)).data,
  feedback: async (id: string, text: string) => (await api.post(`/runs/${encodeURIComponent(id)}/feedback`, { text })).data,
};

function canonical(value: any): string {
  if (value === undefined) return 'undefined';
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object') return '{' + Object.keys(value).sort()
    .map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
  return JSON.stringify(value);
}

function conditions(s: Run['snapshot']): Record<string, any> {
  const h = s.harness_result;
  return {
    modo: s.evidence_mode, cenário: s.scenario, 'versão de execução': s.execution_contract_version,
    capacidades: s.model_profile?.capabilities, pergunta: s.question_request?.question,
    pacote: s.packet, 'fonte dos dados': s.evidence_source || s.dw_source,
    prompt: s.prompt, critérios: s.verification_criteria, parâmetros: s.model?.parameters,
    'catálogo de tools': s.tool_catalog,
    'contrato de saída': h?.contract_sha256, 'contrato de entrada': h?.input_contract_sha256,
    mapas: h?.map_sha256, protocolo: h?.protocol, limites: h?.limits,
    'política de dependências': h?.dependency_policy, 'orçamento do payload': h?.request_budget_policy,
    'motor do harness': h?.engine_sha256, 'contratos de execução': s.runtime_contract,
  };
}

function differing(values: Record<string, any>[]): string[] {
  if (values.length < 2) return [];
  return Object.keys(values[0]).filter(key => values.some(item => canonical(item[key]) !== canonical(values[0][key])));
}

const requiredRuntimeFiles = [
  'agent_harness/engine.py', 'agent_harness/typed_detail.py', 'agent_harness/local_queries.py',
  'agent_harness/real_pilot.py', 'agent_harness/openai_pilot.py', 'agent_harness/synthetic_demo.py',
  'agent_harness/catalog_runtime.py', 'openai_provider.py', 'groq.py', 'request_budget.py',
].map(path => 'inference_api/src/inference_api/' + path);

function detailLoadState(s: Run['snapshot']): 'missing' | 'changed' | 'recorded' {
  const loads = s.evidence_source?.detail_loads;
  if (!loads || loads.before?.status !== 'recorded' || loads.after?.status !== 'recorded') return 'missing';
  for (const state of [loads.before, loads.after]) {
    for (const domain of ['industrial', 'financeiro']) {
      const manifest = state.domains?.[domain];
      if (!manifest?.sha256 || !Array.isArray(manifest.files) || !manifest.files.length) return 'missing';
    }
  }
  if (canonical(loads.before) !== canonical(loads.after)) return 'changed';
  const files = Object.values(loads.before.domains).flatMap((domain: any) =>
    domain.files.map((file: any) => ({ ...file, database: domain.database })));
  for (const evidence of s.harness_result?.evidence || []) {
    for (const row of evidence.rows || []) {
      const p = row.provenance;
      if (p?.source_file_sha256) {
        const known = files.find((file: any) => file.database === p.database && file.table === p.table && file.period === p.period_index);
        if (!known) return 'missing';
        if (known.sha256 !== p.source_file_sha256) return 'changed';
      }
    }
  }
  return 'recorded';
}

export function comparisonAssessment(runs: Run[]) {
  const controls = differing(runs.map(run => conditions(run.snapshot)));
  const candidates = differing(runs.map(({ snapshot: s }) => ({
    'modelo/provedor': { provider: s.model?.provider || s.provider, model: s.model?.model_id,
      receipts: [...new Set<string>((s.harness_result?.trace || []).filter((e: any) => e.model?.provenance).map((e: any) => canonical(e.model.provenance)))].sort(), alias: s.model?.alias, base_revision: s.model?.base_revision, adapter_hash: s.model?.adapter_hash,
      adapter_run: s.model?.adapter_run, served_model: s.model?.served_model, api_surface: s.model?.api_surface },
  })));
  const outcomes = differing(runs.map(({ snapshot: s }) => ({
    'trajetória e evidências observadas': { trace: s.harness_result?.trace || s.tool_trace,
      evidence: s.harness_result?.evidence || s.evidence_bundle, response: s.harness_result?.response || s.model_output },
  })));
  const missing = new Set<string>();
  for (const { snapshot: s } of runs) {
    const c = conditions(s);
    for (const key of ['modo', 'pergunta', 'prompt', 'critérios', 'parâmetros']) {
      if (c[key] == null) missing.add(key);
    }
    if (!s.model?.model_id || !(s.model?.provider || s.provider)) missing.add('identidade do modelo');
    if (s.harness_result) {
      for (const key of ['contrato de saída', 'contrato de entrada', 'mapas', 'protocolo', 'limites',
        'política de dependências', 'orçamento do payload', 'motor do harness']) {
        if (c[key] == null || canonical(c[key]) === '{}') missing.add(key);
      }
      if (s.evidence_mode === 'agent_harness_pilot' || s.scenario === 'data_access') {
        for (const key of ['dw_fingerprint', 'catalog_sha256', 'data_contract_sha256', 'physical_inventory_sha256']) {
          if (!s.evidence_source?.[key]) missing.add(key);
        }
        const loadState = detailLoadState(s);
        if (loadState === 'missing') missing.add('manifestos das cargas industrial/financeira');
        if (loadState === 'changed' && !controls.includes('carga de detalhe mudou ou contradiz a proveniência')) controls.push('carga de detalhe mudou ou contradiz a proveniência');
      }
      if (s.evidence_mode === 'agent_harness' && !s.evidence_source?.fixture_sha256) missing.add('hash da fixture');
      if (s.schema_version !== 7 && (!s.runtime_contract?.prompt_builder_sha256 || !s.runtime_contract?.query_executor_sha256)) missing.add('contratos de execução');
      if (s.schema_version === 7 && canonical(s.runtime_contract?.code) !== canonical(s.runtime_contract?.code_after)) {
      if (!controls.includes('código mudou durante o run')) controls.push('código mudou durante o run');
    }
    if (s.schema_version === 7) {
        if (!s.model_profile?.sha256 || !s.model_profile?.capabilities) missing.add('perfil e capacidades');
        if (s.scenario === 'fixed_evidence' && (!s.packet?.sha256 || s.packet.sha256 !== s.evidence_source?.sha256)) missing.add('hash do pacote');
        for (const file of ['agent_harness/scenarios.py', 'model_service/registry.py', 'model_service/service.py', 'model_service/adapters.py']) {
          if (!s.runtime_contract?.code?.files?.['inference_api/src/inference_api/' + file]) missing.add('serviço de modelos e cenários');
        }
      }
      if (s.runtime_contract?.code?.version !== 'runtime_files_v1' ||
        requiredRuntimeFiles.some(path => !s.runtime_contract?.code?.files?.[path])) missing.add('componentes executáveis');
    } else missing.add('metadados completos de comparação do harness');
  }
  return { status: runs.length < 2 || missing.size ? 'indeterminate' : controls.length ? 'different_conditions' : 'compatible_recorded_conditions',
    controls, candidates, outcomes, missing: [...missing].sort() };
}

export function comparisonDifferences(runs: Run[]): string[] {
  const result = comparisonAssessment(runs);
  return [...result.controls, ...result.candidates, ...result.outcomes];
}

export function comparisonSummary(runs: Run[]): string {
  const result = comparisonAssessment(runs);
  const status = result.status === 'indeterminate' ? `Compatibilidade indeterminada; faltam metadados (${result.missing.join(', ')}).`
    : result.status === 'different_conditions' ? 'Condições diferentes: não isola o efeito do modelo.'
      : 'Condições registradas compatíveis para comparação.';
  return [status, result.controls.length ? `Insumos diferentes (${result.controls.join(', ')}).` : '',
    result.candidates.length ? 'Modelo/provedor diferente: variável do candidato identificada separadamente.' : '',
    result.outcomes.length ? 'Trajetórias e resultados diferentes são saídas observadas, não condições fixas.' : '',
    'Comparação exploratória; compatibilidade não comprova validade científica.'].filter(Boolean).join(' ');
}
