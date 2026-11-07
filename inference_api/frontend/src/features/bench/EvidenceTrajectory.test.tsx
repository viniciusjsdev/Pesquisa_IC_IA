import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EvidenceTrajectory } from './EvidenceTrajectory';
import type { Run } from './benchService';

const base = { id: 'run-1', author: 'Pesquisador', created_at: '2026-11-01T12:00:00Z' };

describe('EvidenceTrajectory', () => {
  it('shows the fixed evidence as an input without inventing a tool call', () => {
    const run: Run = { ...base, snapshot: { schema_version: 5, evidence_mode: 'dw_snapshot',
      question_request: { question: 'Pergunta do caso' }, packet: { case_id: 'caso-1' },
      evidence_json_sent: '{"rows":[1]}', model: { model_id: 'modelo-1' },
      model_turns: [{ order: 1, request: { messages: [{ role: 'user', content: 'Pergunta do caso' }] } }],
      model_output: { raw_text: 'Resposta registrada' }, status: 'answered_unverified' } };
    render(<EvidenceTrajectory run={run}/>);
    expect(screen.getByText('Cenário A · sem tools de navegação')).toBeInTheDocument();
    expect(screen.getAllByText('Pergunta do caso').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /Evidência fixa entregue/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Ferramenta/ })).not.toBeInTheDocument();
    expect(screen.getByText('Resposta registrada')).toBeInTheDocument();
  });

  it('shows assistant requests and recorded DW tool results in order', () => {
    const run: Run = { ...base, snapshot: { schema_version: 5, evidence_mode: 'dw_tools',
      question_request: { question: 'Pergunta de navegação' }, model: { model_id: 'modelo-1' },
      model_turns: [
        { order: 1, request: { messages: [{ role: 'user', content: 'Pergunta de navegação' }] } },
        { order: 2, request: { messages: [{ role: 'tool', content: '{"rows":[1]}' }] } },
      ],
      tool_trace: [{ order: 1, name: 'financial', raw_request: { function: { name: 'financial' } },
        validated_arguments: { year: 2021 }, result: { coverage: { rows: 1 }, rows: [{ value: 42 }] }, status: 'returned' }],
      model_output: { raw_text: 'Resposta final' }, status: 'answered_unverified' } };
    render(<EvidenceTrajectory run={run}/>);
    expect(screen.getByText('Cenário B · consulta à DW com tools')).toBeInTheDocument();
    const buttons = screen.getAllByRole('button', { name: /Assistente · turno|Ferramenta · financial/ });
    expect(buttons.map(button => button.getAttribute('aria-label'))).toEqual([
      'Assistente · turno 1 · Registrado', 'Ferramenta · financial · Retornou', 'Assistente · turno 2 · Registrado',
    ]);
    fireEvent.click(screen.getByRole('button', { name: /Ferramenta · financial/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Devolveu' }));
    expect(screen.getByText('1 linha(s) retornada(s); cobertura não registrada.')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Ver saída exata'));
    expect(screen.getByText(/"value": 42/)).toBeInTheDocument();
  });

  it('keeps the full tool catalog behind an expandable technical input', () => {
    const run: Run = { ...base, snapshot: { schema_version: 5, evidence_mode: 'dw_tools',
      question_request: { question: 'Pergunta' }, model: { model_id: 'modelo-1' },
      model_turns: [{ order: 1, request: { messages: [{ role: 'user', content: 'Pergunta' }],
        tools: [{ function: { name: 'financial' } }, { function: { name: 'catalog' } }] } }],
      status: 'insufficient_evidence' } };
    render(<EvidenceTrajectory run={run}/>);
    expect(screen.getByText('Pergunta e instruções, com 2 tool(s) disponíveis para escolha.')).toBeInTheDocument();
    expect(screen.getByText('Ver entrada exata').closest('details')).not.toHaveAttribute('open');
  });
});
