"""Authenticated SPEC-013 job path with synthetic model and in-memory storage."""
import json
import os
import sys
import threading
import unittest
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from inference_api import jobs, server, service, storage
from inference_api.agent_harness.synthetic_demo import QUESTION
from inference_api.auth import Principal
from test_agent_harness import ScriptedModel, scripted_outputs


class HarnessHttpTests(unittest.TestCase):
    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass


if __name__ == "__main__":
    unittest.main()
