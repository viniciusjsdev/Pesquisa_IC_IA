import { api } from '../../services/api';

export type Snapshot = { snapshot_at: string; series: Record<string, { mes: string }[]> };

export const biService = {
  snapshot: async (): Promise<Snapshot> => (await api.get<Snapshot>('/bi/snapshot')).data,
};
