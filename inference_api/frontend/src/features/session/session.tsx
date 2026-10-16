import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { errorMessage, onSessionExpired, setSessionToken } from '../../services/api';
import { SessionContext, useSession, type Identity } from './sessionContext';
import { sessionService } from './sessionService';

export function SessionProvider({ children }: { children: ReactNode }) {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const queryClient = useQueryClient();
  useEffect(() => {
    onSessionExpired(() => { setSessionToken(null); queryClient.clear(); setIdentity(null); });
    return () => onSessionExpired(null);
  }, [queryClient]);
  const login = async (username: string, password: string) => {
    setSessionToken(await sessionService.login(username, password));
    try {
      setIdentity(await sessionService.identity());
    } catch (error) {
      setSessionToken(null);
      queryClient.clear();
      throw error;
    }
  };
  const logout = async () => {
    try { await sessionService.logout(); }
    finally { setSessionToken(null); queryClient.clear(); setIdentity(null); }
  };
  return <SessionContext.Provider value={{ identity, login, logout }}>{children}</SessionContext.Provider>;
}

export function LoginPage() {
  const { login } = useSession();
  const [username, setUsername] = useState('Nicoli');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    try { await login(username, password); setPassword(''); }
    catch (error) { setMessage(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <main className="login-screen"><section className="login-card">
    <div className="brandmark">◈</div><p className="eyebrow">PESQUISA IC · ACESSO LOCAL</p>
    <h1>Observatório</h1><p>Entre para consultar o retrato sintético e a Bancada de testes.</p>
    <form onSubmit={submit}>
      <label htmlFor="username">Pesquisador</label><select id="username" value={username} onChange={(e) => setUsername(e.target.value)}><option>Nicoli</option><option>Vinicius</option></select>
      <label htmlFor="password">Senha</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      {message && <p role="alert" className="login-error">{message}</p>}
      <button id="login" type="submit" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
    </form>
  </section></main>;
}
