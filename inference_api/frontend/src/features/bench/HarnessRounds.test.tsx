import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { HarnessRounds } from './HarnessRounds';
import type { Run } from './benchService';

describe('HarnessRounds', () => {
  it('renders the complete saved answer and both writer attempts without changing the snapshot', () => {
    const run: Run = { id: 'repaired', author: 'Pesquisador', created_at: '2026-11-06T16:00:00Z',
      snapshot: { status: 'answered_unverified', harness_result: {
        response: { resposta: 'Total observado: 10.', ressalvas: ['Dados sintéticos; não prova causalidade.'],
          calculos: ['4 + 6 = 10'], evidencias_utilizadas: ['result_01', 'result_02'] },
        evidence: [{ result_id: 'result_01', source_id: 'machine', grain: 'machine_id/year' }],
        trace: [
          { event_id: 'call_08', role: 'redator_resposta', round: 3, attempt: 1,
            status: 'rejected', error: 'answer_unknown_evidence', raw_output: '{"bad":true}', input: { input: {} } },
          { event_id: 'call_09', role: 'redator_resposta', round: 3, attempt: 2,
            status: 'validated', input: { input: {}, source_event_ids: ['tool_01', 'tool_02', 'call_08'] },
            output: { resposta: 'Total observado: 10.' } },
        ],
      } } };
    const before = JSON.stringify(run);
    render(<HarnessRounds run={run}/>);
    const answer = within(screen.getByRole('region', { name: 'Resposta final' }));
    expect(answer.getByText('Dados sintéticos; não prova causalidade.')).toBeInTheDocument();
    expect(answer.getByText('4 + 6 = 10')).toBeInTheDocument();
    expect(answer.getByText(/machine · grão machine_id\/year/)).toBeInTheDocument();
    expect(answer.getByText(/detalhe não registrado/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Assistente · Redator da Resposta · Rejeitada' }));
    fireEvent.click(screen.getByRole('button', { name: 'Saída' }));
    expect(screen.getAllByText(/answer_unknown_evidence/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Assistente · Redator da Resposta · Contrato validado' }));
    expect(screen.getByText('Correção visível · tentativa 2.')).toBeInTheDocument();
    expect(screen.getByText(/tool_01, tool_02, call_08/)).toBeInTheDocument();
    expect(JSON.stringify(run)).toBe(before);
  });

  it('keeps legacy text-only answers readable without inventing metadata', () => {
    render(<HarnessRounds run={{ id: 'old', author: 'Pesquisador', created_at: '',
      snapshot: { model_output: { raw_text: 'Resposta histórica.' }, harness_result: { trace: [] } } }}/>);
    expect(screen.getByText('Resposta histórica.')).toBeInTheDocument();
    expect(screen.queryByText('Ressalvas e limites')).not.toBeInTheDocument();
    expect(screen.queryByText('Evidências utilizadas')).not.toBeInTheDocument();
  });

  it('labels a recorded pilot data query as a backend tool and keeps its evidence state visible', () => {
    const run: Run = {
      id: 'pilot-run', author: 'Pesquisador', created_at: '2026-11-02T16:00:00Z',
      snapshot: { evidence_mode: 'agent_harness_pilot', question_request: { question: 'Pergunta piloto' },
        harness_result: { queries: 1, trace: [
          { event_id: 'tool_01', role: 'data_query', round: 1, status: 'validated',
            input: { fonte_id: 'machine', filtros: { year: 2021, id: 2000002 } },
            output: { result_id: 'result_01', coverage: { state: 'no_observation', rows: 0 }, rows: [] } },
        ] } },
    };
    render(<HarnessRounds run={run}/>);
    expect(screen.getByText(/Dados reais consultados no piloto/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ferramenta · Serviço de consultas/ })).toBeInTheDocument();
    expect(screen.getAllByText(/0 linha\(s\) retornada\(s\)/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Fixture inventada/)).not.toBeInTheDocument();
  });

  it('shows recorded rounds and lets the reader inspect each input, output and error', () => {
    const run: Run = {
      id: 'run-1', author: 'Vinicius', created_at: '2026-11-01T15:00:00Z',
      snapshot: { question_request: { question: 'Pergunta inventada' }, model: { provider: 'groq', model_id: 'modelo-exemplo' }, harness_result: { model_calls: 2, queries: 1, trace: [
        { event_id: 'call_01', role: 'analista_pergunta', round: 0, status: 'validated',
          input: { input: { question: 'Pergunta inventada' }, source_event_ids: [] }, output: { dominios: ['dw'] } },
        { event_id: 'tool_01', role: 'synthetic_query', round: 1, status: 'validated',
          input: { fonte_id: 'fixture_1' }, output: { result_id: 'result_01', rows: [] } },
        { event_id: 'call_02', role: 'revisor_evidencias', round: 1, status: 'rejected',
          input: { input: { available_evidence_ids: ['result_01'] }, source_event_ids: ['call_01', 'tool_01'] },
          raw_output: '{invalid}', error: 'invalid_json' },
      ] } },
    };

    render(<HarnessRounds run={run}/>);
    expect(screen.getByText('Uma IA, vários agentes internos')).toBeInTheDocument();
    expect(screen.getByText('groq · modelo-exemplo · 2 papel(is) registrado(s)')).toBeInTheDocument();
    expect(screen.getByText('Pergunta inicial')).toBeInTheDocument();
    expect(screen.getByText('Entrada da execução · fora do trace de chamadas')).toBeInTheDocument();
    expect(screen.getAllByText('Assistente').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Ferramenta').length).toBeGreaterThan(0);
    expect(screen.getByText('Rodada 0')).toBeInTheDocument();
    expect(screen.getByText('Rodada 0 · 1 etapa(s)')).toBeInTheDocument();
    expect(screen.getByText('Rodada 1')).toBeInTheDocument();
    expect(screen.getByText('Rodada 1 · 2 etapa(s)')).toBeInTheDocument();
    expect(screen.getAllByText(/Pergunta inventada/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: /Ferramenta · Serviço de consultas/ }));
    expect(screen.getByText('Consulta executada pelo backend; não chama outro modelo.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Saída' }));
    expect(screen.getAllByText(/result_01/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: /Revisor das Evidências/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Saída' }));
    expect(screen.getAllByText(/invalid_json/).length).toBeGreaterThan(0);
    expect(within(screen.getByLabelText('Rodadas do Harness')).getByText(/Sem saída validada/)).toBeInTheDocument();
  });

  it('shows the specialist two-call handoff, backend projection and final answer', () => {
    const run: Run = {
      id: 'run-2', author: 'Pesquisadora', created_at: '2026-11-01T16:00:00Z',
      snapshot: { question_request: { question: 'Quantas paradas ocorreram em outubro?' },
        model: { provider: 'groq', model_id: 'qwen-exemplo' },
        status: 'answered_unverified', harness_result: { model_calls: 3, queries: 0,
          response: { resposta: 'Foram 90 paradas na fixture; a origem é result_01.' }, trace: [
            { event_id: 'call_01', role: 'especialista_indice', round: 1, status: 'validated',
              input: { input: { domain_index: { domain: 'industrial', sources: [{ id: 'paradas' }] } } },
              output: { table_ids: ['paradas'], justificativa: 'medida de paradas', lacunas: [] } },
            { event_id: 'map_01', role: 'map_projection', round: 1, status: 'validated',
              input: { domain: 'industrial', selected_table_ids: ['paradas'] },
              output: { source_count: 1, selected_table_ids: ['paradas'] } },
            { event_id: 'call_02', role: 'especialista_dados', round: 1, status: 'validated',
              input: { input: { selected_table_ids: ['paradas'], domain_detail: { domain: 'industrial', sources: { paradas: { fields: ['data'] } } } } },
              output: { map_refs: ['paradas.data'], granularidade: 'evento' } },
            { event_id: 'call_03', role: 'redator_resposta', round: 2, status: 'validated',
              input: { input: { evidence_state: [] } }, output: { resposta: 'Foram 90 paradas na fixture; a origem é result_01.' } },
          ] } },
    };

    render(<HarnessRounds run={run}/>);
    expect(screen.getByText('groq · qwen-exemplo · 2 papel(is) registrado(s)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Especialista dos Dados Industriais · escolhe tabelas/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Validação dos IDs e preparo do detalhe/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Especialista dos Dados Industriais · analisa o detalhe/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Validação dos IDs e preparo do detalhe/ }));
    expect(screen.getByText('Fonte selecionada e mapa versionado; o backend prepara o detalhe.')).toBeInTheDocument();
    expect(screen.getAllByText('1 tabela(s) validada(s); detalhe preparado pelo backend').length).toBeGreaterThan(0);
    expect(screen.getByText('Assistente · Especialista dos Dados Industriais · analisa o detalhe')).toBeInTheDocument();
    expect(screen.getByText('Foram 90 paradas na fixture; a origem é result_01.')).toBeInTheDocument();
  });

  it('shows the domain specialist building and correcting a query in contract 3', () => {
    const run: Run = {
      id: 'contract-3', author: 'Pesquisador', created_at: '2026-11-06T12:00:00Z',
      snapshot: { harness_result: { trace: [
        { event_id: 'call_03', role: 'especialista_consulta', round: 1, status: 'validated',
          input: { input: { domain: 'industrial', source_contract: { source_id: 'paradas' },
            correction_feedback: { rejected_plan: { filtros: { maquina_id: '2' } }, error_code: 'invalid_id_filter' } } },
          output: { plano: { fonte_id: 'paradas', filtros: { maquina_id: 2 } } } },
      ] } },
    };
    render(<HarnessRounds run={run}/>);
    expect(screen.getByRole('button', { name: /Especialista dos Dados Industriais · monta consulta/ })).toBeInTheDocument();
    expect(screen.getByText('Pergunta, contrato completo da fonte, tentativa recusada, erro e saldo atualizado.')).toBeInTheDocument();
    expect(screen.queryByText('Planejador da Consulta')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Entrada' }));
    expect(screen.getAllByText(/invalid_id_filter/).length).toBeGreaterThan(0);
  });
});
