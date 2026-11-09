"""Authenticated public reconciliation route, local HTTP only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from uuid import uuid4
from inference_api import server
from inference_api.observability import reconciliation,receipts

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        threading.Thread(target=self.http.serve_forever,daemon=True).start()
        self.addCleanup(self.http.server_close);self.addCleanup(self.http.shutdown)
        self.path='/api/runs/'+str(uuid4())+'/observability/reconcile'
        self.principal=SimpleNamespace(id=str(uuid4()),username='Vinicius')
        p=patch.object(server.auth,'authenticate',side_effect=lambda credential:self.principal if credential=='Bearer invented' else None)
        p.start();self.addCleanup(p.stop)
    def request(self,path=None,body=None,authorized=True):
        req=Request(f'http://127.0.0.1:{self.http.server_port}'+(path or self.path),method='POST',
                    data=json.dumps(body).encode() if body is not None else None,
                    headers={'Authorization':'Bearer invented'} if authorized else {})
        try:
            with urlopen(req,timeout=3) as response:return response.status,json.load(response)
        except HTTPError as exc:return exc.code,json.load(exc)
    def test_no_auth_invalid_id_body_and_errors_have_no_remote_dispatch(self):
        with patch.object(reconciliation,'reconcile') as reconcile:
            self.assertEqual(self.request(authorized=False)[0],401)
            self.assertEqual(self.request('/api/runs/bad/observability/reconcile')[0],400)
            self.assertEqual(self.request(body={'endpoint':'https://evil.test'})[0],400)
            reconcile.assert_not_called()
            for error,status in [(reconciliation.NotFound('run_not_found'),404),
                                 (reconciliation.Forbidden('observability_owner_required'),403),
                                 (receipts.ReconciliationBusy('reconciliation_in_progress'),409)]:
                reconcile.side_effect=error
                self.assertEqual(self.request()[0],status)
            reconcile.side_effect=None;reconcile.return_value={'schema_version':1,'state':'pending'}
            status,body=self.request()
            self.assertEqual(status,200);self.assertEqual(body,{'observability_current':reconcile.return_value})
            self.assertEqual(reconcile.call_args.args[1],self.principal)

if __name__=='__main__':unittest.main()
