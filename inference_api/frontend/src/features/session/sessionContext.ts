import { createContext, useContext } from 'react';

export type Identity = { id: string; username: string };
export type SessionValue = { identity: Identity | null; login: (username: string, password: string) => Promise<void>; logout: () => Promise<void> };
export const SessionContext = createContext<SessionValue | null>(null);

export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error('SessionProvider ausente');
  return value;
}
