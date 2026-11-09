"""Bounded process queue, explicit parents and telemetry failures isolated from runs."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from queue import Queue, Full
from threading import Thread, Condition, Lock
import time
from .config import load
from .contracts import VERSION, sdk_id
from .sanitize import project, configured_secrets
from .noop import Noop

ACTIVE = ContextVar('inference_observer_span', default=(None, None))

class Dispatcher:
    def __init__(self, capacity=1000):
        self.queue = Queue(maxsize=capacity)
        Thread(target=self._run, name='inference-telemetry', daemon=True).start()
    def _run(self):
        while True:
            observer, event = self.queue.get()
            try:
                observer.sink.send(event)
                observer.complete(True)
            except Exception: observer.complete(False)
            finally: self.queue.task_done()
    def submit(self, observer, event):
        try: self.queue.put_nowait((observer, event)); return True
        except Full: return False

_dispatcher = None
_lock = Lock()
def dispatcher():
    global _dispatcher
    with _lock:
        if _dispatcher is None: _dispatcher = Dispatcher()
        return _dispatcher

class Observer:
    enabled = True
    def __init__(self, run_id, config, sink, *, dispatch=None):
        self.run_id, self.config, self.sink = run_id, config, sink
        self.dispatch = dispatch or dispatcher()
        self.events, self.ended = {}, set()
        self.condition = Condition()
        self.pending = self.sent = self.failed = self.dropped = 0
        self.secrets = (*configured_secrets(), config.api_key)
        self.receipt_attached=False
        self.receipt_error=None
        self._receipt_lock=Lock()
        self._receipt_updated=0
        self._receipt_running=False
        self._receipt_dirty=False
        self.root = self.start('root', 'Bancada', 'chain')
    def start(self, event_id, name, kind, *, parent=None, inputs=None, metadata=None):
        try:
            if event_id in self.events: return event_id
            parent = parent or (ACTIVE.get()[1] if ACTIVE.get()[0] is self else None)
            parent = parent or ('root' if event_id != 'root' else None)
            now = datetime.now(timezone.utc)
            ident = sdk_id(self.run_id, event_id)
            order = now.strftime('%Y%m%dT%H%M%S%fZ')+ident
            if parent in self.events: order = self.events[parent]['dotted_order']+'.'+order
            inherited = self.events.get(parent, {}).get('metadata', {})
            event = {'id': ident, 'trace_id': sdk_id(self.run_id, 'root'),
                'parent_run_id': sdk_id(self.run_id, parent) if parent else None,
                'dotted_order': order, 'name': name, 'run_type': kind,
                'start_time': now.isoformat(), 'inputs': inputs or {},
                'metadata': {'local_run_id': self.run_id, 'local_event_id': event_id,
                    'instrumentation_version': VERSION, 'content_mode': self.config.content, **(metadata or {})}}
            for key, default in (('round', 0), ('attempt', 1)):
                event['metadata'].setdefault(key, inherited.get(key, default))
            # Sanitize before retaining asynchronous export content.
            with self.condition:
                if 'root' in self.ended:return None
                self.events[event_id] = project(event, self.config.content, self.secrets)
            return event_id
        except Exception:
            self.dropped += 1; return None
    def end(self, event_id, *, outputs=None, status='completed', error=None, metadata=None):
        try:
            if event_id not in self.events or event_id in self.ended: return
            self.ended.add(event_id)
            event = {**self.events[event_id], 'end_time': datetime.now(timezone.utc).isoformat(),
                'outputs': outputs or {}, 'status': status, 'error': error,
                'metadata': {**self.events[event_id]['metadata'], **(metadata or {})}}
            event = project(event, self.config.content, self.secrets)
            if self.config.content == 'metadata':
                event['metadata']['inputs_sha256'] = self.events[event_id]['metadata']['inputs_sha256']
            with self.condition:
                self.pending += 1
                if not self.dispatch.submit(self, event): self.pending -= 1; self.dropped += 1
            self._notify(force=event_id=='root')
        except Exception: self.dropped += 1
    def complete(self, success):
        with self.condition:
            self.pending -= 1
            if success: self.sent += 1
            else: self.failed += 1
            self.condition.notify_all()
        self._notify(force=self.pending==0)
    def attach_receipt(self,principal_id,job_id=None):
        try:
            from . import receipts
            from .config import destination
            ident,descriptor=destination(self.config)
            receipts.create(self.run_id,principal_id,sdk_id(self.run_id,'root'),ident,descriptor,
                            self.config.content,job_id)
            self.receipt_attached=True
            self._notify(force=True)
        except Exception:self.receipt_error='receipt_storage_unavailable'
    def bind_run(self,run_id):
        if not self.receipt_attached:return
        try:
            from . import receipts
            receipts.bind(self.run_id,run_id)
        except Exception:self.receipt_error='receipt_storage_unavailable'
    def _notify(self,force=False):
        if not self.receipt_attached:return
        # Coalesce progress into one bounded writer per observer. Never block
        # inference/final flush on an unavailable application DB.
        with self.condition:
            if not force and time.monotonic()-self._receipt_updated<0.1:return
            self._receipt_dirty=True
            if self._receipt_running:return
            self._receipt_running=True
        def write():
            from . import receipts
            while True:
                with self.condition:
                    self._receipt_dirty=False
                    expected=[{'id':e['id'],'parent_run_id':e['parent_run_id']} for e in self.events.values()]
                    sealed='root' in self.ended
                    counts=self.snapshot()
                try:receipts.progress(self.run_id,expected,sealed,counts)
                except Exception:self.receipt_error='receipt_storage_unavailable'
                with self.condition:
                    self._receipt_updated=time.monotonic()
                    if not self._receipt_dirty:
                        self._receipt_running=False
                        self.condition.notify_all()
                        return
        Thread(target=write,daemon=True,name='observability-receipt').start()
    def annotate(self, metadata):
        try:
            event = self.events['root']
            clean = project({'metadata': metadata}, self.config.content, self.secrets)['metadata']
            event['metadata'].update({k: v for k,v in clean.items() if k not in {'inputs_sha256','outputs_sha256'}})
        except Exception: self.dropped += 1
    @contextmanager
    def activate(self, span):
        token = ACTIVE.set((self, span))
        try: yield
        finally: ACTIVE.reset(token)
    def finish(self, result, timeout=2):
        technical_error=None
        if result['status'] not in {'answered_unverified','insufficient_evidence'}:
            technical_error=(result.get('final_state') or {}).get('error') or 'execution_error'
        self.end('root', outputs={'response': result.get('response'), 'final_state': result.get('final_state')},
            status=result['status'], error=technical_error, metadata={k: result[k] for k in
            ('scenario','contract_sha256','input_contract_sha256','map_sha256','model_calls','queries','query_attempts') if k in result})
        deadline = time.monotonic()+min(max(timeout, 0), 2)
        with self.condition:
            while self.pending and time.monotonic() < deadline:
                self.condition.wait(max(0, deadline-time.monotonic()))
        self._notify(force=True)
        return self.snapshot()
    def snapshot(self):
        """Read current export state without sending, waiting or ending another span."""
        with self.condition:
            state = ('pending' if 'root' not in self.ended or self.pending and not (self.failed or self.dropped) else
                     'partial' if self.sent and (self.failed or self.dropped or self.pending) else
                     'failed' if self.failed or self.dropped else 'submitted')
            metadata = {'state': state, 'submitted_events': self.sent, 'failed_events': self.failed,
                'dropped_events': self.dropped, 'pending_events': self.pending,
                'instrumentation_version': VERSION, 'content_mode': self.config.content}
        if self.sent:
            try:
                url = self.sink.url(sdk_id(self.run_id, 'root'))
                if url:
                    from urllib.parse import urlsplit
                    from .config import trusted_web_origin
                    import re
                    parsed = urlsplit(url)
                    origin = trusted_web_origin(self.config.endpoint)
                    if (origin and parsed.scheme+'://'+parsed.netloc == origin and not parsed.username
                        and re.fullmatch(r'/o/[\w-]+/projects/p/[\w-]+/r/[\w-]+',parsed.path)):
                        metadata.update(url=url, trusted_origin=origin)
            except Exception: pass
        return metadata

def create(run_id):
    try:
        config = load()
        if not config.enabled: return Noop(config.diagnostic)
        from .langsmith_sink import LangSmithSink
        return Observer(run_id, config, LangSmithSink(config))
    except Exception: return Noop('observability_initialization_failed')

def current(): return ACTIVE.get()
