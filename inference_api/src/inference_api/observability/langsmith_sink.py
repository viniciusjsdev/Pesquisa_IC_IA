"""Explicit SDK emission only; one HTTP attempt and no batching or auto tracing."""
from .config import trusted_web_origin
from urllib.parse import urlsplit
import re

class LangSmithSink:
    def __init__(self, config, client=None):
        self.config = config
        self.urls = {}
        if client is None:
            from langsmith import Client
            from urllib3.util.retry import Retry
            client = Client(api_urls={config.endpoint: config.api_key},
                retry_config=Retry(total=0, connect=0, read=0, redirect=0, status=0),
                timeout_ms=2000, auto_batch_tracing=False, omit_traced_runtime_info=True,
                tracing_sampling_rate=1.0, info={'version': 'local-explicit'})
        self.client = client

    def send(self, event):
        metadata = {**event['metadata'], 'status': event['status']}
        self.client.create_run(name=event['name'], inputs=event['inputs'], run_type=event['run_type'],
            id=event['id'], trace_id=event['trace_id'], parent_run_id=event.get('parent_run_id'),
            start_time=event['start_time'], end_time=event['end_time'], dotted_order=event['dotted_order'],
            outputs=event['outputs'], error=event.get('error'), project_name=self.config.project,
            extra={'metadata': metadata}, usage_metadata=metadata.get('usage_metadata'),
            api_url=self.config.endpoint, api_key=self.config.api_key)
        if event['metadata'].get('local_event_id') == 'root':
            # Resolve the actual private URL; never invent a link or create a public share.
            try:
                url = self.client.read_run(event['id']).url
                parsed = urlsplit(url or '')
                origin = trusted_web_origin(self.config.endpoint)
                if (origin and parsed.scheme+'://'+parsed.netloc == origin
                    and re.fullmatch(r'/o/[\w-]+/projects/p/[\w-]+/r/[\w-]+', parsed.path)):
                    self.urls[event['trace_id']] = url
            except Exception: pass

    def url(self, trace_id):
        return self.urls.get(trace_id)
