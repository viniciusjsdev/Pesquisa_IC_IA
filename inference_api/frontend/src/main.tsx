import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from './features/session/session';
import { App } from './app/App';
import './app/styles.scss';

const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 60_000 } } });
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={client}><SessionProvider><App /></SessionProvider></QueryClientProvider></React.StrictMode>);
