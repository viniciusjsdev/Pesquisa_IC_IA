export type Observability = { state?: string; url?: string | null; trusted_origin?: string | null };

export function privateTraceUrl(value?: Observability): string | null {
  if (!value?.url || !['submitted', 'partial'].includes(value.state || '')) return null;
  try {
    const url = new URL(value.url);
    const origins = ['https://smith.langchain.com', 'https://eu.smith.langchain.com'];
    if (!origins.includes(url.origin) || url.origin !== value.trusted_origin
        || url.username || url.password || url.pathname.startsWith('/public/')) return null;
    if (!/^\/o\/[\w-]+\/projects\/p\/[\w-]+\/r\/[\w-]+$/.test(url.pathname)) return null;
    return url.href;
  } catch { return null; }
}

