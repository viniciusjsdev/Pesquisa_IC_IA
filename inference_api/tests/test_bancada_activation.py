"""Backend-owned exact receipts may coexist; never infer broader authorization."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from copy import deepcopy
import json
import tempfile
import unittest
from unittest.mock import patch
from inference_api.model_service import registry
from spec014_fixture import profile

class AuthorizationTests(unittest.TestCase):
    def test_legacy_and_bundle_keep_exact_identity_data_scenario_and_limits(self):
        p=profile();limits={'model_calls':48,'query_attempts':3}
        b={'decision':'approved','spec_id':'SPEC-014','profile_sha256':p['sha256'],
           'destination':p['endpoint'],'scenario':'data_access','data_sha256':'catalog','limits':limits}
        a={**b,'scenario':'fixed_evidence','data_sha256':'packet','limits':{**limits,'query_attempts':0}}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'authorization.json'
            with patch.dict('os.environ',{'INFERENCE_SPEC014_AUTHORIZATION':str(path)}):
                for value in (b,{'schema_version':1,'authorizations':[a,b]}):
                    path.write_text(json.dumps(value))
                    self.assertEqual(registry.authorize(p,'data_access','catalog',limits),registry.digest(b))
                self.assertEqual(registry.authorize(p,'fixed_evidence','packet',a['limits']),registry.digest(a))
                for bad_profile,scenario,data,requested in [({**p,'sha256':'other'},'data_access','catalog',limits),
                    (p,'fixed_evidence','catalog',limits),(p,'data_access','other',limits),
                    (p,'data_access','catalog',{**limits,'model_calls':49})]:
                    with self.assertRaisesRegex(ValueError,'transmission_authorization_mismatch'):
                        registry.authorize(bad_profile,scenario,data,requested)
                path.write_text(json.dumps({'schema_version':1,'authorizations':[]}))
                with self.assertRaisesRegex(ValueError,'invalid_transmission_authorization_bundle'):
                    registry.authorize(p,'data_access','catalog',limits)

if __name__=='__main__':unittest.main()
