import { useState } from 'react';
import { BIPage, type BITab } from '../features/bi/BIPage';
import { LoginPage } from '../features/session/session';
import { useSession } from '../features/session/sessionContext';
import { BenchPage } from '../features/bench/BenchPage';

type Tab = BITab | 'bench';
const tabs: { key: Tab; label: string; icon: string }[] = [
  { key: 'overview', label: 'Visão integrada', icon: '▦' },
  { key: 'financial', label: 'Financeiro', icon: '↗' },
  { key: 'industrial', label: 'Industrial', icon: '⚙' },
  { key: 'sources', label: 'Dados e método', icon: '≡' },
  { key: 'bench', label: 'Bancada de testes', icon: '◉' },
];

export function App() {
  const { identity, logout } = useSession();
  const [tab, setTab] = useState<Tab>('overview');
  if (!identity) return <LoginPage />;
  return <div className="observatory"><aside>
    <div className="brand"><span className="brandmark">◈</span> observatório</div>
    <div className="subbrand">FINANCEIRO + INDUSTRIAL</div><div className="nav-label">EXPLORAR A BASE</div>
    <nav aria-label="Seções do painel">{tabs.map(item => <button key={item.key} type="button" className={tab === item.key ? 'active' : ''} aria-current={tab === item.key ? 'page' : undefined} onClick={() => setTab(item.key)}><span className="icon" aria-hidden="true">{item.icon}</span>{item.label}</button>)}</nav>
    <div className="sidebar-bottom"><span className="status-dot"/>Conectado como {identity.username}<br/><button className="logout" onClick={() => void logout()}>Sair</button><br/>Base sintética · versão offline</div>
  </aside>{tab === 'bench' ? <BenchPage/> : <BIPage tab={tab}/>}</div>;
}
