"""Exploratory orchestration boundaries without a live database or Pod."""
from base64 import b64decode
import json
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inference_api import evidence, models, orchestrator, service
from inference_api.contracts import EvidenceItem, SCHEMA_VERSION


def item(tool, year=2020, count=13):
    spec = evidence.QUERIES[tool]
    return EvidenceItem(SCHEMA_VERSION, f"{tool}:{year}", tool,
                        "db_" + spec["domain"].lower(), spec["table"], spec["fields"],
                        {"year": year}, {"year": year}, "annual aggregate of source records",
                        spec["unit"], "123", count, spec["formula"], spec["statement"],
                        (year, year), "available" if count else "absent", spec["limitation"])


BASE = {"author": "pesquisador", "question": "Qual o valor?", "system_prompt": "Cite [evidence:ID] e limites.",
        "model_alias": "qwen-base", "scope": "financeiro", "year": 2020}


class ContractTests(unittest.TestCase):
    def test_routes_and_legacy_contract(self):
        for scope, tools in orchestrator.TOOLS_BY_SCOPE.items():
            with self.subTest(scope=scope):
                request, plan = orchestrator.plan({**BASE, "scope": scope}, "qwen-base", "Q", 0, 256)
                self.assertEqual(plan.tools, tools)
                self.assertEqual(request.route_origin, "researcher_declared_scope")
        request, plan = orchestrator.plan({**BASE, "scope": None,
                                           "evidence_route": "financeiro_vendas_ano"},
                                          "qwen-base", "Q", 0, 256)
        self.assertEqual(plan.scope, "financeiro")
        self.assertEqual(request.route_origin, "legacy_evidence_route")

    def test_unknown_tool_year_and_parameter_fail_before_query(self):
        with patch("inference_api.evidence.psycopg2.connect") as connect, \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            for change in ({"tools": ["SELECT * FROM public.vendas"]},
                           {"year": 2027}, {"scope": ["integrado"]},
                           {"sql": "SELECT * FROM public.vendas"}):
                with self.subTest(change=change):
                    result = service.execute_run({**BASE, **change})
                    self.assertEqual(result["status"], "route_error")
            connect.assert_not_called()

    def test_data_agents_use_readonly_parameterized_source_query(self):
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def execute(self, statement, params=None): calls.append((statement, params))
            def fetchone(self): return (13, 123)
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def close(self): return None
            def set_session(self, **kwargs): sessions.append(kwargs)
            def cursor(self): return Cursor()
        calls, sessions = [], []
        with patch("inference_api.evidence.db_params", return_value={"host": "127.0.0.1"}), \
             patch("inference_api.evidence.psycopg2.connect", return_value=Connection()) as connect:
            financial = evidence.financial_agent(2020)
            industrial = evidence.industrial_agent(2020)
        self.assertEqual(connect.call_count, 2)
        self.assertEqual(sessions, [{"readonly": True, "autocommit": False}] * 2)
        self.assertEqual(calls[1][1], (2020, 2020))
        self.assertEqual(calls[3][1], (2020, 2020))
        self.assertTrue(all("statement_timeout" in calls[i][0] for i in (0, 2)))
        self.assertNotEqual(financial.source_database, industrial.source_database)

    def test_integrated_bundle_and_llm_payload(self):
        captured = {}
        def infer(alias, prompt, question, bundle, temperature, max_tokens):
            captured.update({"alias": alias, "prompt": prompt, "question": question,
                             "bundle": bundle, "temperature": temperature, "max_tokens": max_tokens})
            return ("Associação anual [evidence:financeiro_vendas_ano:2020] "
                    "[evidence:industrial_operacoes_ano:2020]", {"endpoint": "https://model.example"})
        with patch("inference_api.evidence.financial_agent", return_value=item("financeiro_vendas_ano")), \
             patch("inference_api.evidence.industrial_agent", return_value=item("industrial_operacoes_ano")), \
             patch.dict(evidence.AGENTS, {"financeiro_vendas_ano": lambda y: item("financeiro_vendas_ano", y),
                                          "industrial_operacoes_ano": lambda y: item("industrial_operacoes_ano", y)}), \
             patch("inference_api.response_agent.models.infer", side_effect=infer), \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            result = service.execute_run({**BASE, "scope": "integrado"})
        bundle = result["evidence_bundle"]
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(captured["bundle"], bundle)
        self.assertEqual({x["source_database"] for x in bundle["items"]},
                         {"db_financeiro", "db_industrial"})
        self.assertEqual({x["period"]["year"] for x in bundle["items"]}, {2020})
        self.assertIn("sem demonstrar causalidade", " ".join(bundle["limitations"]))
        self.assertEqual(captured["prompt"], BASE["system_prompt"])
        self.assertEqual(captured["question"], BASE["question"])
        self.assertNotIn("password", json.dumps(captured).lower())
        self.assertNotIn("gold", json.dumps(captured).lower())
        self.assertEqual({x["result"] for x in result["checks"] if x["check"] in
                          ("numerical_truth", "causality")}, {"not_checked"})

    def test_missing_evidence_and_query_error_do_not_call_model(self):
        with patch.dict(evidence.AGENTS, {"financeiro_vendas_ano": lambda y: item("financeiro_vendas_ano", y, 0)}), \
             patch("inference_api.response_agent.models.infer") as infer, \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            result = service.execute_run(BASE)
            self.assertEqual(result["status"], "insufficient_evidence")
            self.assertIsNone(result["model_output"])
            infer.assert_not_called()
        def fail(_): raise evidence.SourceQueryError("financeiro_vendas_ano", TimeoutError())
        with patch.dict(evidence.AGENTS, {"financeiro_vendas_ano": fail}), \
             patch("inference_api.response_agent.models.infer") as infer, \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            result = service.execute_run(BASE)
            self.assertEqual(result["status"], "query_error")
            self.assertEqual(result["error"]["stage"], "query")
            infer.assert_not_called()

    def test_model_error_and_invalid_citation_preserve_output(self):
        with patch.dict(evidence.AGENTS, {"financeiro_vendas_ano": lambda y: item("financeiro_vendas_ano", y)}), \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            with patch("inference_api.response_agent.models.infer", side_effect=RuntimeError("offline")):
                result = service.execute_run(BASE)
                self.assertEqual(result["status"], "model_error")
                self.assertIsNotNone(result["evidence_bundle"])
                self.assertIsNone(result["model_output"])
            with patch("inference_api.response_agent.models.infer",
                       return_value=("texto [evidence:inventado:2020]", {"served_model": "qwen-base"})):
                result = service.execute_run(BASE)
                self.assertEqual(result["status"], "answered_unverified")
                self.assertEqual(result["model_output"]["raw_text"], "texto [evidence:inventado:2020]")
                self.assertEqual(next(x for x in result["checks"] if x["check"] == "cited_evidence_ids")["result"], "failed")

    def test_http_model_request_contains_only_prompt_question_and_bundle(self):
        requests = []
        class Response:
            def __init__(self, body): self.body = body
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return json.dumps(self.body).encode()
        def open_request(request, timeout):
            requests.append(request)
            if request.full_url.endswith("/v1/models"):
                return Response({"data": [{"id": "qwen-base"}]})
            return Response({"choices": [{"message": {"content": "texto"}}],
                             "model": "qwen-base", "usage": {"total_tokens": 3}})
        bundle = asdict(evidence.EvidenceBundle(SCHEMA_VERSION,
                    orchestrator.plan(BASE, "qwen-base", "Q", 0, 256)[1],
                    (item("financeiro_vendas_ano"),), "available", ("limite",)))
        with patch("inference_api.models.vllm_url", return_value="https://model.example"), \
             patch("inference_api.models.urlopen", side_effect=open_request):
            answer, serving = models.infer("qwen-base", "Prompt exato", "Pergunta exata",
                                           bundle, 0, 256)
        sent = json.loads(requests[1].data)
        self.assertEqual(answer, "texto")
        self.assertEqual(serving["raw_response"]["model"], "qwen-base")
        self.assertEqual(sent["messages"][0]["content"], "Prompt exato")
        self.assertEqual(sent["messages"][1]["content"],
                         "Pergunta exata\n\nEvidências JSON:\n" + json.dumps(bundle, ensure_ascii=False))
        self.assertEqual(set(sent), {"model", "messages", "temperature", "max_tokens", "stream"})
        self.assertNotIn("password", json.dumps(sent).lower())
        self.assertNotIn("gold", json.dumps(sent).lower())

    def test_response_and_verification_failures_have_distinct_states(self):
        with patch.dict(evidence.AGENTS, {"financeiro_vendas_ano": lambda y: item("financeiro_vendas_ano", y)}), \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            with patch("inference_api.response_agent.models.infer", return_value=("", {"served_model": "qwen-base"})):
                result = service.execute_run(BASE)
                self.assertEqual(result["status"], "response_error")
                self.assertEqual(result["model_output"]["raw_text"], "")
            with patch("inference_api.response_agent.models.infer", return_value=("texto", {"served_model": "qwen-base"})), \
                 patch("inference_api.service.verifier.check", side_effect=RuntimeError("check failed")):
                result = service.execute_run(BASE)
                self.assertEqual(result["status"], "verification_error")
                self.assertEqual(result["model_output"]["raw_text"], "texto")

    def test_invalid_server_response_is_preserved_as_response_error(self):
        class Response:
            def __init__(self, body): self.body = body
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def read(self): return self.body

        for raw_body, expected_format in (
            (b"not-json", "text"),
            (b'{"model":"qwen-base","choices":[]}', "json"),
        ):
            with self.subTest(raw_body=raw_body):
                def open_request(request, timeout):
                    if request.full_url.endswith("/v1/models"):
                        return Response(b'{"data":[{"id":"qwen-base"}]}')
                    return Response(raw_body)

                with patch.dict(evidence.AGENTS, {"financeiro_vendas_ano":
                                                 lambda y: item("financeiro_vendas_ano", y)}), \
                     patch("inference_api.models.vllm_url", return_value="https://model.example"), \
                     patch("inference_api.models.urlopen", side_effect=open_request), \
                     patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
                    result = service.execute_run(BASE)
                self.assertEqual(result["status"], "response_error")
                self.assertEqual(result["error"]["stage"], "response")
                self.assertIsNotNone(result["evidence_bundle"])
                self.assertIsNone(result["model_output"]["raw_text"])
                serving = result["model_output"]["serving"]
                self.assertEqual(serving["raw_response_format"], expected_format)
                self.assertEqual(b64decode(serving["raw_response_bytes_b64"]), raw_body)
                self.assertEqual(result["model"]["endpoint"], "https://model.example")

    def test_concurrent_aliases_are_isolated(self):
        def infer(alias, *_): return (f"Resposta {alias}", {"served_model": alias})
        with patch.dict(evidence.AGENTS, {"financeiro_vendas_ano": lambda y: item("financeiro_vendas_ano", y)}), \
             patch("inference_api.response_agent.models.infer", side_effect=infer), \
             patch("inference_api.service.storage.create_run", side_effect=lambda a, s: s):
            with ThreadPoolExecutor(max_workers=2) as pool:
                runs = list(pool.map(service.execute_run,
                                     ({**BASE, "model_alias": alias} for alias in
                                      ("ft-finqa-a", "ft-failure-b"))))
        self.assertEqual([x["model"]["alias"] for x in runs], ["ft-finqa-a", "ft-failure-b"])
        self.assertEqual([x["model_output"]["serving"]["served_model"] for x in runs],
                         ["ft-finqa-a", "ft-failure-b"])


if __name__ == "__main__":
    unittest.main()
