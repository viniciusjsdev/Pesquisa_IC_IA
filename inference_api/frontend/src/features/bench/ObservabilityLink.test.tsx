import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ObservabilityLink } from './ObservabilityLink';
import { privateTraceUrl } from './observabilityPresentation';
import { benchService, type ObservabilityCurrent } from './benchService';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const origin = 'https://smith.langchain.com';
const url = origin + '/o/fixture-org/projects/p/fixture-project/r/fixture-run?poll=true';
const current: ObservabilityCurrent = { schema_version: 1, state: 'pending', remote_verified: false,
  can_reconcile: true, trace_id: 'invented', submitted_events: 2, failed_events: 0, dropped_events: 0,
  pending_events: 0, expected_events: 2, observed_remote_events: null, url: null, trusted_origin: null,
  last_checked_at: null, last_check_error: null, revision: 1 };
describe('private LangSmith link', () => {
  it('preserves historical runs without metadata', () => {
    const { container } = render(<ObservabilityLink/>); expect(container.textContent).toBe('');
  });
  it('shows an authenticated private trace and partial state', () => {
    render(<ObservabilityLink value={{ state: 'partial', url, trusted_origin: origin }}/>);
    expect(screen.getByText('Envio parcial ao LangSmith')).toBeTruthy();
    expect(screen.getByRole('link').getAttribute('href')).toBe(url);
  });
  it('rejects model links, public traces, credentials and wrong destinations', () => {
    for (const unsafe of ['javascript:alert(1)', 'https://evil.test/runs/1', origin+'/public/abc/r',
      'https://user:password@smith.langchain.com/o/org/projects/p/project/r/run']) {
      expect(privateTraceUrl({ state: 'submitted', url: unsafe, trusted_origin: origin })).toBeNull();
    }
    expect(privateTraceUrl({ state: 'failed', url, trusted_origin: origin })).toBeNull();
  });
  it('displays export failure independently of the answer', () => {
    render(<ObservabilityLink value={{ state: 'failed' }}/>);
    expect(screen.getByText('Falha no envio ao LangSmith')).toBeTruthy();
    expect(screen.queryByRole('link')).toBeNull();
  });
  it('reads only on click, shows loading and persists a verified private link', async () => {
    let resolve!: (value: ObservabilityCurrent) => void;
    const spy = vi.spyOn(benchService, 'reconcile').mockImplementation(() => new Promise(r => { resolve = r; }));
    const frozen = JSON.stringify(current);
    const view = render(<ObservabilityLink value={{state:'failed'}} current={current} runId="run"/>);
    expect(spy).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Atualizar monitoramento' }));
    expect(screen.getByRole('button').hasAttribute('disabled')).toBe(true);
    resolve({...current, state:'submitted', remote_verified:true, url, trusted_origin:origin,
      last_checked_at:'2026-11-08T12:00:00Z', revision:2});
    await screen.findByText('Etapas confirmadas no LangSmith.');
    expect(screen.getByRole('link').getAttribute('href')).toBe(url);
    expect(screen.getByText(/Última conferência/)).toBeTruthy();
    expect(JSON.stringify(current)).toBe(frozen);
    view.rerender(<ObservabilityLink current={current} runId="run"/>);
    expect(spy).toHaveBeenCalledTimes(1);
  });
  it('preserves the last verified link on offline failure and offers no action to other owners', async () => {
    const spy=vi.spyOn(benchService,'reconcile').mockRejectedValue(new Error('offline'));
    const verified={...current,state:'submitted',remote_verified:true,url,trusted_origin:origin};
    const view=render(<ObservabilityLink current={verified} runId="run"/>);
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => expect(screen.getByRole('status')).toBeTruthy());
    expect(screen.getByRole('link').getAttribute('href')).toBe(url);
    view.rerender(<ObservabilityLink current={{...verified,can_reconcile:false}} runId="run"/>);
    await waitFor(() => expect(screen.queryByRole('button')).toBeNull());
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
