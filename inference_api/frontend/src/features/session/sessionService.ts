import { api } from '../../services/api';
import type { Identity } from './sessionContext';

export const sessionService = {
  login: async (username: string, password: string): Promise<string> =>
    (await api.post<{ token: string }>('/login', { username, password })).data.token,
  identity: async (): Promise<Identity> => (await api.get<Identity>('/me')).data,
  logout: async (): Promise<void> => { await api.post('/logout'); },
};
