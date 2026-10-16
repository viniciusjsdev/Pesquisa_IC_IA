import axios, { AxiosError } from 'axios';

let bearer: string | null = null;
let sessionExpired: (() => void) | null = null;

export const api = axios.create({ baseURL: '/api', timeout: 30000 });

api.interceptors.request.use((config) => {
  if (bearer) config.headers.Authorization = `Bearer ${bearer}`;
  return config;
});

api.interceptors.response.use(undefined, (error: AxiosError) => {
  if (error.response?.status === 401 && bearer && !error.config?.url?.endsWith('/login')) {
    bearer = null;
    sessionExpired?.();
  }
  return Promise.reject(error);
});

export function setSessionToken(token: string | null) { bearer = token; }
export function onSessionExpired(callback: (() => void) | null) { sessionExpired = callback; }
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.error;
    if (status === 429) return `Limite de concorrência: ${detail || 'uma inferência por vez'}. Tente novamente manualmente.`;
    if (status === 409) return `Conflito de revisão: ${detail || 'há uma versão mais recente'}. Seu rascunho foi preservado.`;
    if (status === 503) return 'Serviço ou banco indisponível. Confira a preparação local do banco.';
    if (status === 401) return 'Sessão expirada. Entre novamente.';
    return typeof detail === 'string' ? detail : `Falha HTTP ${status || 'de rede'}`;
  }
  return error instanceof Error ? error.message : 'Falha inesperada';
}
