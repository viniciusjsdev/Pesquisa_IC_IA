"""Receipt persistence uses the application DB, never a research connection."""
from contextlib import closing, contextmanager
import json
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from ..config import app_db_params

class ReconciliationBusy(RuntimeError): pass

def connect():
    params=app_db_params()
    if params.get('dbname')!='db_inference_app' and not params.get('dbname','').startswith('spec015_'):
        # Isolated tests supply the app connection through the same test-owned hook.
        raise ValueError('observability_application_database_required')
    return psycopg2.connect(**{**params,'connect_timeout':1,
        'options':'-c statement_timeout=1000 -c lock_timeout=300'})

def create(harness_id,principal_id,trace_id,destination_id,descriptor,content_mode,job_id=None):
    with closing(connect()) as conn,conn,conn.cursor() as cur:
        cur.execute('INSERT INTO observability_destinations VALUES (%s,%s) ON CONFLICT DO NOTHING',
                    (destination_id,Json(descriptor)))
        cur.execute('''INSERT INTO run_observability
            (harness_run_id,principal_id,trace_id,destination_id,content_mode,job_id)
            VALUES (%s,%s,%s,%s,%s,%s)''',(harness_id,principal_id,trace_id,destination_id,content_mode,job_id))

def bind(harness_id,run_id):
    with closing(connect()) as conn,conn,conn.cursor() as cur:
        cur.execute('UPDATE run_observability SET run_id=%s, revision=revision+1 WHERE harness_run_id=%s AND run_id IS NULL',
                    (run_id,harness_id))

def progress(harness_id,expected,sealed,counts):
    with closing(connect()) as conn,conn,conn.cursor() as cur:
        cur.execute('''UPDATE run_observability SET
            expected_event_ids=CASE WHEN sealed THEN expected_event_ids ELSE %s END,
            sealed=sealed OR %s, submitted_events=GREATEST(submitted_events,%s),
            failed_events=GREATEST(failed_events,%s), dropped_events=GREATEST(dropped_events,%s),
            pending_events=%s, state=CASE WHEN remote_verified THEN state ELSE %s END,
            revision=revision+1 WHERE harness_run_id=%s''',
            (Json(expected),sealed,counts['submitted_events'],counts['failed_events'],counts['dropped_events'],
             counts['pending_events'],counts['state'],harness_id))

def get(run_id):
    with closing(connect()) as conn,conn,conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''SELECT r.*, d.descriptor FROM run_observability r
            JOIN observability_destinations d USING(destination_id) WHERE run_id=%s''',(run_id,))
        row=cur.fetchone()
        return dict(row) if row else None

def public(record,principal_id=None):
    if not record:return None
    return {'schema_version':1,'state':record['state'],'remote_verified':record['remote_verified'],
        'can_reconcile':bool(record['sealed'] and record['run_id'] and str(record['principal_id'])==str(principal_id)),
        'trace_id':str(record['trace_id']),**{key:record[key] for key in
            ('submitted_events','failed_events','dropped_events','pending_events','url','trusted_origin','last_check_error','revision')},
        'expected_events':len(record['expected_event_ids']),'observed_remote_events':record['observed_remote_events'],
        'last_checked_at':record['last_checked_at'].isoformat() if record['last_checked_at'] else None}

def current(run_id,principal_id=None):
    try:return public(get(run_id),principal_id)
    except Exception:return None

@contextmanager
def claim(run_id):
    with closing(connect()) as conn:
        conn.autocommit=True
        with conn.cursor() as cur:
            cur.execute('SELECT pg_try_advisory_lock(hashtextextended(%s,0))',(str(run_id),))
            if not cur.fetchone()[0]:raise ReconciliationBusy('reconciliation_in_progress')
            try:yield
            finally:cur.execute('SELECT pg_advisory_unlock(hashtextextended(%s,0))',(str(run_id),))

def checked(run_id,*,error=None,state=None,observed=None,url=None,origin=None,verified=False):
    with closing(connect()) as conn,conn,conn.cursor() as cur:
        # Export progress and reconciliation update disjoint counters. A failed new
        # check never erases a previous successful remote verification or its URL.
        cur.execute('''UPDATE run_observability SET
            state=CASE WHEN remote_verified AND NOT %s THEN state ELSE COALESCE(%s,state) END,
            remote_verified=remote_verified OR %s,
            observed_remote_events=CASE WHEN remote_verified AND NOT %s THEN observed_remote_events
                ELSE COALESCE(%s,observed_remote_events) END,
            url=COALESCE(%s,url),trusted_origin=COALESCE(%s,trusted_origin),
            last_checked_at=now(),last_check_error=%s,revision=revision+1 WHERE run_id=%s''',
            (verified,state,verified,verified,observed,url,origin,error,run_id))
