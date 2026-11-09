"""Owner-authorized, bounded remote reads. Never sends events or reruns work."""
import time
import json
from urllib.parse import urlsplit
from uuid import UUID
import requests
from queue import Queue, Empty
from threading import Thread
from datetime import datetime, timezone
from . import receipts, config

class NotFound(LookupError): pass
class Forbidden(PermissionError): pass
class ReadFailure(RuntimeError): pass

class ReadSession(requests.Session):
    def __init__(self,endpoint,trace_id,*,transport=None,clock=time.monotonic):
        super().__init__()
        self.endpoint=endpoint.rstrip('/')
        self.trace_id=trace_id
        self.clock=clock
        self.deadline=clock()+10
        self.count=0
        self.failure_code=None
        self.transport=transport
    def request(self,method,url,**kwargs):
        remaining=self.deadline-self.clock()
        if remaining<=0:self.failure_code='remote_timeout'
        elif self.count>=3:self.failure_code='remote_read_limit'
        elif (method.upper(),url.split('?',1)[0]) not in {
            ('GET',self.endpoint+'/runs/'+self.trace_id),('POST',self.endpoint+'/runs/query')}:
            self.failure_code='remote_operation_forbidden'
        if self.failure_code:raise ReadFailure(self.failure_code)
        self.count+=1
        kwargs.update(timeout=min(2,remaining),allow_redirects=False,stream=True)
        # requests' read timeout is an inactivity timeout. Bound the caller even
        # during slow headers; the daemon cannot start another physical request.
        result=Queue(maxsize=1)
        send=self.transport or super().request
        def read():
            response=None
            try:
                response=send(method,url,**kwargs)
                if response.is_redirect:raise ReadFailure('remote_redirect_forbidden')
                content=bytearray()
                # One-byte reads also bound a peer trickling a larger chunk.
                for chunk in response.iter_content(chunk_size=1):
                    if self.clock()>=self.deadline:raise ReadFailure('remote_timeout')
                    content.extend(chunk)
                    if len(content)>1024*1024:raise ReadFailure('remote_response_limit')
                response._content=bytes(content);response._content_consumed=True
                result.put((response,None))
            except Exception as exc:result.put((None,exc))
            finally:
                if response is not None and response.raw is not None:response.close()
        Thread(target=read,daemon=True,name='observability-bounded-read').start()
        try:response,error=result.get(timeout=max(0,self.deadline-self.clock()))
        except Empty:
            self.failure_code='remote_timeout';raise ReadFailure(self.failure_code) from None
        if error:
            self.failure_code=str(error) if isinstance(error,ReadFailure) else 'remote_unavailable'
            raise ReadFailure(self.failure_code) from None
        if self.clock()>=self.deadline:
            self.failure_code='remote_timeout';raise ReadFailure(self.failure_code)
        return response

def read_tree(destination,trace_id):
    from langsmith import Client
    from langsmith.schemas import Run
    from langsmith.utils import LangSmithNotFoundError
    from urllib3.util.retry import Retry
    session=ReadSession(destination.endpoint,trace_id)
    client=Client(api_urls={destination.endpoint:destination.api_key},session=session,
        retry_config=Retry(total=0,connect=0,read=0,redirect=0,status=0),timeout_ms=2000,
        auto_batch_tracing=False,omit_traced_runtime_info=True,info={'version':'bounded-read-only'})
    root=None
    try:
        root=client.read_run(trace_id)
        if root.session_id is None:raise ReadFailure('remote_project_missing')
        # Hosted API accepts at most100 per page. Read at most two pages,
        # retaining the overall128-span/three-request ceiling (root + pages).
        spans=[];cursor=None
        for _ in range(2):
            limit=min(100,128-len(spans))
            if limit<=0:raise ReadFailure('remote_span_limit')
            body={'session':[str(root.session_id)],'trace':trace_id,'limit':limit,
                  'select':['id','trace_id','parent_run_id','name','run_type','start_time','session_id','app_path']}
            if cursor:body['cursor']=cursor
            page=client.request_with_retries('POST','/runs/query',stop_after_attempt=1,
                request_kwargs={'data':json.dumps(body)}).json()
            items=page.get('runs',[])
            if not isinstance(items,list) or len(items)>limit:raise ReadFailure('remote_span_limit')
            spans.extend(Run(**item) for item in items)
            cursor=(page.get('cursors') or {}).get('next')
            if not cursor:return root,spans
        if cursor:raise ReadFailure('remote_read_limit')
        return root,spans
    except LangSmithNotFoundError:raise ReadFailure('root_not_indexed' if root is None else 'remote_unavailable') from None
    except ReadFailure:raise
    except Exception:
        raise ReadFailure(session.failure_code or 'remote_unavailable') from None
    finally:session.close()

def validate_url(url,destination,trace_id):
    import re
    try:
        parsed=urlsplit(url or '')
        origin=config.trusted_web_origin(destination.endpoint)
        if (not origin or parsed.scheme+'://'+parsed.netloc!=origin or parsed.username or parsed.password
            or not re.fullmatch(r'/o/[\w-]+/projects/p/[\w-]+/r/'+re.escape(trace_id),parsed.path)):
            return None
        return url,origin
    except ValueError:return None

def reconcile(run_id,principal,*,storage=None,reader=None):
    from ..persistence import storage as default_storage
    storage=storage or default_storage
    run_id=str(UUID(run_id))
    run=storage.get_run(run_id)
    if not run:raise NotFound('run_not_found')
    if str(run.get('snapshot',{}).get('identity',{}).get('principal_id'))!=str(principal.id):
        raise Forbidden('observability_owner_required')
    record=receipts.get(run_id)
    if record and str(record['principal_id'])!=str(principal.id):raise Forbidden('observability_owner_required')
    if not record:raise NotFound('observability_receipt_unavailable')
    if not record['sealed']:raise ValueError('observability_not_finalized')
    with receipts.claim(run_id):
        # Reload after lock acquisition: counters/revision may have advanced.
        record=receipts.get(run_id)
        storage_failed=False
        def save(**updates):
            nonlocal storage_failed
            try:receipts.checked(run_id,**updates)
            except Exception:storage_failed=True
        def response():
            value=receipts.current(run_id,principal.id)
            if value is not None and not storage_failed:return value
            # Preserve the last authorized receipt if persistence/readback fails;
            # do not return null or claim the new remote result was durable.
            fallback={**record,'last_check_error':'receipt_storage_unavailable',
                      'last_checked_at':datetime.now(timezone.utc)}
            return receipts.public(fallback,principal.id)
        destination=config.for_read(record['destination_id'],record['descriptor'])
        if destination is None:
            save(error='destination_unavailable')
            return response()
        trace_id=str(record['trace_id'])
        try:
            root,spans=(reader or read_tree)(destination,trace_id)
            if len(spans)>128:raise ReadFailure('remote_span_limit')
            expected={e['id']:e['parent_run_id'] for e in record['expected_event_ids']}
            observed={str(s.id):str(s.parent_run_id) if s.parent_run_id else None for s in spans}
            complete=(len(expected)==len(record['expected_event_ids']) and len(observed)==len(spans) and observed==expected
                and str(root.id)==trace_id and str(root.trace_id)==trace_id and root.parent_run_id is None
                and trace_id in observed and all(str(s.trace_id)==trace_id for s in spans))
            if not complete:
                save(error='remote_tree_incomplete',state='partial',observed=len(spans))
            else:
                validated=validate_url(root.url,destination,trace_id)
                if not validated:raise ReadFailure('invalid_remote_url')
                url,origin=validated
                save(state='submitted',observed=len(spans),url=url,origin=origin,verified=True)
        except ReadFailure as exc:
            code=str(exc)
            save(error=code,state='pending' if code=='root_not_indexed' else None)
        except Exception:
            save(error='remote_unavailable')
        return response()
