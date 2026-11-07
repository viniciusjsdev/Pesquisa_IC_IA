import { describe, expect, it } from 'vitest';
import { comparisonAssessment, comparisonSummary, type Run } from './benchService';

const files = Object.fromEntries(['agent_harness/engine.py', 'agent_harness/typed_detail.py',
  'agent_harness/local_queries.py', 'agent_harness/real_pilot.py', 'agent_harness/openai_pilot.py',
  'agent_harness/synthetic_demo.py', 'agent_harness/catalog_runtime.py', 'openai_provider.py',
  'groq.py', 'request_budget.py'].map(path => ['inference_api/src/inference_api/' + path, 'hash']));
const loads = { status: 'recorded', domains: {
  industrial: { database: 'db_industrial', sha256: 'industrial-hash', files: [{ table: 'stops', period: 2, sha256: 'source-hash' }] },
  financeiro: { database: 'db_financeiro', sha256: 'finance-hash', files: [{ table: 'results', period: 2, sha256: 'finance-source' }] },
} };

const run = (): Run => ({ id: 'one', author: 'fixture', created_at: '', snapshot: {
  evidence_mode: 'agent_harness_pilot', question_request: { question: 'Pergunta?' },
  prompt: { system_prompt: 'protocolo' }, verification_criteria: { version: 1 },
  model: { provider: 'fixture', model_id: 'candidate-a', parameters: { temperature: 0 } },
  evidence_source: { dw_fingerprint: 'dw-hash', catalog_sha256: 'catalog-hash',
    data_contract_sha256: 'data-hash', physical_inventory_sha256: 'inventory-hash', detail_loads: { before: structuredClone(loads), after: structuredClone(loads) } },
  runtime_contract: { prompt_builder_sha256: 'prompt-hash', query_executor_sha256: 'query-hash', code: { version: 'runtime_files_v1', files: { ...files } } },
  harness_result: { contract_sha256: 'output-hash', input_contract_sha256: 'input-hash',
    map_sha256: { dw: 'dw-map', industrial: 'industrial-map' }, protocol: 'fixture', limits: { queries: 3 },
    dependency_policy: 'direct-v1', request_budget_policy: 'body-v1', engine_sha256: 'engine-hash', trace: [] },
} });

describe('harness comparison conditions', () => {
  it('compares v7 conditions and deduplicates candidate provenance across calls', () => {
    const first = run();
    const s = first.snapshot;
    s.schema_version = 7; s.scenario = 'fixed_evidence'; s.evidence_mode = 'fixed_evidence';
    s.execution_contract_version = 1;
    s.packet = { sha256: 'packet-hash' }; s.evidence_source = { sha256: 'packet-hash' };
    s.model_profile = { sha256: 'profile-hash', capabilities: { streaming: true } };
    for (const path of ['agent_harness/scenarios.py', 'model_service/registry.py', 'model_service/service.py', 'model_service/adapters.py'])
      s.runtime_contract.code.files['inference_api/src/inference_api/' + path] = 'hash';
    s.runtime_contract.code_after = structuredClone(s.runtime_contract.code);
    s.harness_result.trace = [{ model: { provenance: { base_revision: 'abc', adapter_hash: '123' } } }];
    const second = structuredClone(first);
    second.snapshot.harness_result.trace.push(structuredClone(second.snapshot.harness_result.trace[0]));
    expect(comparisonAssessment([first, second]).candidates).toEqual([]);
    expect(comparisonAssessment([first, second]).status).toBe('compatible_recorded_conditions');
    second.snapshot.model_profile.capabilities.streaming = false;
    expect(comparisonAssessment([first, second]).controls).toContain('capacidades');
    const drift = structuredClone(first);
    drift.snapshot.runtime_contract.code_after.files['changed'] = 'new';
    expect(comparisonAssessment([drift, structuredClone(drift)]).controls).toContain('código mudou durante o run');
    const missing = structuredClone(first); delete missing.snapshot.packet.sha256;
    expect(comparisonAssessment([missing, missing]).status).toBe('indeterminate');
  });
  it('compares every executable component and route-independent source loads', () => {
    for (const file of Object.keys(files)) {
      const other = run(); other.snapshot.runtime_contract.code.files[file] = 'changed';
      expect(comparisonAssessment([run(), other]).status).toBe('different_conditions');
    }
    const other = run();
    for (const state of ['before', 'after']) other.snapshot.evidence_source.detail_loads[state].domains.industrial.sha256 = 'new-load';
    expect(comparisonAssessment([run(), other]).status).toBe('different_conditions');
    const unknown = run(); delete unknown.snapshot.evidence_source.detail_loads;
    expect(comparisonAssessment([unknown, unknown]).status).toBe('indeterminate');
    const changed = run();
    changed.snapshot.harness_result.evidence = [{ rows: [{ provenance: { database: 'db_industrial', table: 'stops', period_index: 2, source_file_sha256: 'different-file' } }] }];
    expect(comparisonAssessment([run(), changed]).status).toBe('different_conditions');
    const validRoute = run();
    validRoute.snapshot.harness_result.evidence = [{ rows: [{ provenance: { database: 'db_industrial', table: 'stops', period_index: 2, source_file_sha256: 'source-hash' } }] }];
    expect(comparisonAssessment([run(), validRoute]).status).toBe('compatible_recorded_conditions');
  });
  it('detects each contract, map, limit, data and policy change', () => {
    for (const key of ['contract_sha256', 'input_contract_sha256', 'map_sha256', 'protocol', 'limits',
      'dependency_policy', 'request_budget_policy', 'engine_sha256']) {
      const other = run(); other.snapshot.harness_result[key] = 'changed';
      expect(comparisonAssessment([run(), other]).status).toBe('different_conditions');
    }
    const other = run(); other.snapshot.evidence_source.data_contract_sha256 = 'changed';
    expect(comparisonSummary([run(), other])).toContain('Condições diferentes');
  });

  it('ignores object key order and separates model identity from observed decisions', () => {
    const other = run();
    other.snapshot.harness_result.map_sha256 = { industrial: 'industrial-map', dw: 'dw-map' };
    other.snapshot.model.model_id = 'candidate-b';
    other.snapshot.harness_result.trace = [{ decision: 'other-route' }];
    const result = comparisonAssessment([run(), other]);
    expect(result.status).toBe('compatible_recorded_conditions');
    expect(result.controls).toEqual([]);
    expect(result.candidates).toEqual(['modelo/provedor']);
    expect(result.outcomes).toHaveLength(1);
  });

  it('does not infer compatibility from equally missing metadata in old snapshots', () => {
    const old = run(); delete old.snapshot.harness_result.input_contract_sha256;
    expect(comparisonAssessment([old, structuredClone(old)]).status).toBe('indeterminate');
    expect(comparisonSummary([old, old])).toContain('faltam metadados');
    const missingData = run(); delete missingData.snapshot.evidence_source.data_contract_sha256;
    expect(comparisonAssessment([missingData, missingData]).status).toBe('indeterminate');
  });
});
