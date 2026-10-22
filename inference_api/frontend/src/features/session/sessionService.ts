import { api } from '../../services/api';
import type { Identity } from './sessionContext';

export const sessionService = {
  login: async (username: string, password: string): Promise<void> => {
    await api.post('/login', { username, password }, { headers: { 'X-Browser-Session': '1' } });
  },
  identity: async (): Promise<Identity> => (await api.get<Identity>('/me')).data,
  logout: async (): Promise<void> => { await api.post('/logout'); },
};
