import { api } from '../../services/api';
// Historical run snapshots have multiple schema versions and are rendered read-only.
/* eslint-disable @typescript-eslint/no-explicit-any */

export type Prompt = { id: string; name: string; revision: number; author: string; system_prompt: string };
export type CriteriaConfig = { schema_version: 1; require_evidence: boolean; require_period: boolean; required_units: string[]; require_cited_ids: boolean; required_caveats: string[] };
export type Criterion = { id: string; name: string; revision: number; author: string; config: CriteriaConfig };
export type Run = { id: string; author: string; created_at: string; snapshot: Record<string, any> };
export type Model = { available: boolean; generation_confirmed?: boolean; kind?: string };
export type Budget = { session_ceiling_usd: number; runpod_status: string; runpod_balance_usd: number | null; runpod_spend_per_hour_usd: number | null; runpod_source: string; status_checked_at: string; checked_at: string | null };

export const benchService = {
  models: async () => (await api.get<Record<string, Model>>('/models')).data,
  prompts: async () => (await api.get<Prompt[]>('/prompts')).data,
  criteria: async () => (await api.get<Criterion[]>('/criteria')).data,
  runs: async () => (await api.get<Run[]>('/runs')).data,
  run: async (id: string) => (await api.get<Run>(`/runs/${encodeURIComponent(id)}`)).data,
  budget: async () => (await api.get<Budget>('/budget')).data,
  savePrompt: async (name: string, system_prompt: string, expected_revision: number) => (await api.post<Prompt>('/prompts', { name, system_prompt, expected_revision })).data,
  saveCriteria: async (name: string, config: CriteriaConfig, expected_revision: number) => (await api.post<Criterion>('/criteria', { name, config, expected_revision })).data,
  execute: async (body: Record<string, unknown>) => (await api.post<Run>('/runs', body, { timeout: 120_000 })).data,
  feedback: async (id: string, text: string) => (await api.post(`/runs/${encodeURIComponent(id)}/feedback`, { text })).data,
};

export function comparisonDifferences(runs: Run[]): string[] {
  const signatures = runs.map(({ snapshot: s }) => ({
    pergunta: JSON.stringify(s.question_request?.question),
    período: JSON.stringify({ year: s.question_request?.year, route: s.route_plan }),
    evidência: JSON.stringify(s.evidence_bundle),
    prompt: JSON.stringify(s.prompt),
    critérios: JSON.stringify(s.verification_criteria),
    parâmetros: JSON.stringify(s.model?.parameters),
    'modelo/versão': JSON.stringify({ alias: s.model?.alias, base_revision: s.model?.base_revision, adapter_run: s.model?.adapter_run, adapter_hash: s.model?.adapter_hash, served_model: s.model?.served_model }),
  }));
  if (signatures.length < 2) return [];
  return (Object.keys(signatures[0]) as (keyof typeof signatures[number])[]).filter(key => signatures.some(item => item[key] !== signatures[0][key]));
}
