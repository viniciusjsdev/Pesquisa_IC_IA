"""Protocol checks with invented maps and a deterministic model transport."""
import json
import copy
import os
from contextlib import contextmanager
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from inference_api.agent_harness import HarnessError, Limits, run
from inference_api.agent_harness.engine import INPUT_CONTRACT_SHA256, INPUT_SCHEMAS
from inference_api.agent_harness.synthetic_demo import MAPS, QUESTION, fixture_query
from inference_api.agent_harness import openai_audit, synthetic_demo
from inference_api import groq, jobs, models, service
from inference_api.identity.auth import Principal


class ScriptedModel:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, role, envelope, contract):
        self.calls.append((role, envelope))
        expected_role, value = self.outputs.pop(0)
        if expected_role != role:
            raise AssertionError(f"Expected {expected_role}, got {role}")
        return json.dumps(value), {"provider": "fixture", "model_id": "same-candidate"}


def scripted_outputs():
    need = {"entidade": "linha L1", "medida": "parada e lucro", "periodo": "2020", "grao": "linha/ano e observacao/data"}
    return [
        ("analista_pergunta", {"tratavel": True, "necessidade": need,
                              "dominios": ["dw"], "lacunas": []}),
        ("selecionador_fontes", {"decisao": "consultar", "justificativa": "Paradas primeiro",
                                 "fonte_id": "dw_paradas", "dominio_adicional": None,
                                 "map_refs": ["dw_paradas"]}),
        ("especialista_consulta", {"plano": {"fonte_id": "dw_paradas", "campos": ["linha", "ano", "minutos_parada"],
                                              "filtros": {"ano": 2020}, "limite": 1, "grao": "linha/ano"},
                                  "justificativa": "Agregado", "evidence_refs": []}),
        ("revisor_evidencias", {"decisao": "precisa_aprofundar", "evidencias_utilizadas": ["result_01"],
                                 "justificativa": "Falta lucro", "lacuna": "Falta lucro",
                                 "proximo_dado_necessario": "Lucro de 2020", "dominio_sugerido": "financeiro"}),
        ("selecionador_fontes", {"decisao": "consultar", "justificativa": "Lucro",
                                 "fonte_id": "fin_resultado", "dominio_adicional": None,
                                 "map_refs": ["fin_resultado"]}),
        ("especialista_consulta", {"plano": {"fonte_id": "fin_resultado", "campos": ["data", "lucro_liquido"],
                                              "filtros": {"ano": 2020}, "limite": 1, "grao": "observacao/data"},
                                  "justificativa": "Observacao financeira", "evidence_refs": ["result_01"]}),
        ("revisor_evidencias", {"decisao": "suficiente", "evidencias_utilizadas": ["result_01", "result_02"],
                                 "justificativa": "Ambos observados", "lacuna": None,
                                 "proximo_dado_necessario": None, "dominio_sugerido": None}),
        ("redator_resposta", {"resposta": "45 min e 1200 unidades fictícias; não prova causalidade.",
                              "evidencias_utilizadas": ["result_01", "result_02"], "calculos": [],
                              "ressalvas": ["Sem vínculo causal"]}),
    ]


class HarnessTests(unittest.TestCase):
    def test_uncapped_output_preserves_large_json_and_still_validates_schema(self):
        outputs = scripted_outputs()
        outputs[-1][1]["resposta"] = "evidência " * 2000
        result = run(QUESTION, MAPS, ScriptedModel(outputs), fixture_query,
                     limits=Limits(output_bytes=None))
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["response"]["resposta"], outputs[-1][1]["resposta"])
        self.assertGreater(result["trace"][-1]["output_bytes"], 8192)
        self.assertIsNone(result["limits"]["output_bytes"])
        capped = run(QUESTION, MAPS, ScriptedModel(outputs), fixture_query,
                     limits=Limits(corrections_per_role=0))
        self.assertEqual(capped["final_state"]["error"], "model_output_limit")
        outputs[-1][1]["unexpected_field"] = True
        invalid = run(QUESTION, MAPS, ScriptedModel(outputs), fixture_query,
                      limits=Limits(output_bytes=None, corrections_per_role=0))
        self.assertEqual(invalid["status"], "contract_error")
        self.assertIn("model_output_schema_error", invalid["final_state"]["error"])

    def test_reviewer_receives_current_result_once_and_previous_evidence(self):
        model = ScriptedModel(scripted_outputs())
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        reviews = [envelope["input"] for role, envelope in model.calls
                   if role == "revisor_evidencias"]
        self.assertEqual([item["question"] for item in reviews], [QUESTION, QUESTION])
        self.assertEqual([item["domains_identified"] for item in reviews],
                         [["dw"], ["dw"]])
        self.assertEqual(reviews[0]["query_result"]["result_id"], "result_01")
        self.assertEqual(reviews[0]["evidence_state"], [])
        self.assertEqual(reviews[1]["query_result"]["result_id"], "result_02")
        self.assertEqual([item["result_id"] for item in reviews[1]["evidence_state"]],
                         ["result_01"])

    def test_provider_http_status_is_traced_without_retry(self):
        calls = []
        def fails(role, envelope, contract):
            calls.append(role)
            raise groq.GroqError("provider_request_error", "Groq HTTP 413",
                                 metadata={"http_status": 413})
        result = run(QUESTION, MAPS, fails, fixture_query)
        self.assertEqual(calls, ["analista_pergunta"])
        self.assertEqual(result["trace"][0]["http_status"], 413)

    def test_specialist_receives_only_selected_source_filter_specs(self):
        maps = copy.deepcopy(MAPS)
        maps["dw"]["sources"]["dw_paradas"]["filters"] = [
            "ano:integer", "data:range"]
        model = ScriptedModel(scripted_outputs())
        result = run(QUESTION, maps, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        planner = next(envelope["input"]["source_contract"] for role, envelope in model.calls
                       if role == "especialista_consulta")
        self.assertEqual(planner["source_id"], "dw_paradas")
        self.assertEqual(planner["filters"], ["ano:integer", "data:range"])
        self.assertEqual(planner["fields"], maps["dw"]["sources"]["dw_paradas"]["fields"])
        self.assertNotIn("sources", planner)


    def test_versioned_input_contract_rejects_missing_and_cross_role_fields(self):
        self.assertFalse(INPUT_SCHEMAS["analista_pergunta"].is_valid({"question": QUESTION}))
        self.assertFalse(INPUT_SCHEMAS["analista_pergunta"].is_valid({
            "question": QUESTION, "domain_index": [], "protocol": "synthetic",
            "domain_map": MAPS["industrial"]}))
        result = run(QUESTION, MAPS, ScriptedModel(scripted_outputs()), fixture_query)
        self.assertEqual(result["input_contract_sha256"], INPUT_CONTRACT_SHA256)
        self.assertTrue(all(event["input_contract_sha256"] == INPUT_CONTRACT_SHA256
                            for event in result["trace"]
                            if event["role"] not in {"synthetic_query", "map_projection"}))

    def test_dw_then_industrial_detail_is_selected_by_the_model(self):
        outputs = scripted_outputs()
        first_review = {**outputs[3][1], "lacuna": "Falta a parada individual",
                        "proximo_dado_necessario": "Evento industrial da linha L1",
                        "dominio_sugerido": "industrial"}
        detail_refs = ["ind_parada", "ind_parada.evento_id", "ind_parada.minutos_parada"]
        model = ScriptedModel([
            *outputs[:3], ("revisor_evidencias", first_review),
            ("selecionador_fontes", {"decisao": "consultar", "justificativa": "Detalhar evento",
                                     "fonte_id": "ind_parada", "dominio_adicional": None,
                                     "map_refs": ["ind_parada"]}),
            ("especialista_consulta", {"plano": {"fonte_id": "ind_parada",
                                                     "campos": ["evento_id", "minutos_parada"],
                                                     "filtros": {"evento_id": 7}, "limite": 1,
                                                     "grao": "parada/evento"},
                                      "justificativa": "Evento individual", "evidence_refs": ["result_01"]}),
            outputs[6], outputs[7]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual([item["source_id"] for item in result["evidence"]],
                         ["dw_paradas", "ind_parada"])
        self.assertEqual(result["evidence"][1]["rows"][0]["evento_id"], 7)
        self.assertEqual(model.calls[5][1]["input"]["domain"], "industrial")
        self.assertEqual(model.calls[5][1]["input"]["source_contract"]["source_id"], "ind_parada")

    def test_model_can_start_directly_in_financial_detail(self):
        outputs = scripted_outputs()
        analyst = {**outputs[0][1], "dominios": ["financeiro"]}
        plan = {**outputs[5][1], "evidence_refs": []}
        review = {**outputs[6][1], "evidencias_utilizadas": ["result_01"]}
        answer = {**outputs[7][1], "evidencias_utilizadas": ["result_01"]}
        model = ScriptedModel([("analista_pergunta", analyst), *outputs[4:5],
                               ("especialista_consulta", plan),
                               ("revisor_evidencias", review),
                               ("redator_resposta", answer)])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["queries"], 1)
        self.assertEqual(result["evidence"][0]["source_id"], "fin_resultado")
        self.assertEqual(model.calls[1][1]["input"]["source_index"][0]["domain"], "financeiro")
        self.assertEqual(model.calls[2][1]["input"]["domain"], "financeiro")


    def test_synthetic_fixture_applies_plan_filters(self):
        industrial = {"fonte_id": "dw_paradas", "campos": ["minutos_parada"],
                      "filtros": {"linha": "L1", "ano": 2020}}
        financial = {"fonte_id": "fin_resultado", "campos": ["data", "lucro_liquido"],
                     "filtros": {"data": {"from": "2020-01-01", "to": "2021-01-01"}}}
        self.assertEqual(fixture_query(industrial)["rows"][0]["minutos_parada"], 45)
        self.assertEqual(fixture_query(financial)["rows"][0]["lucro_liquido"], 1200)
        self.assertEqual(fixture_query({**industrial, "filtros": {"ano": 2019}})["coverage"]["state"],
                         "no_observation")
        self.assertEqual(fixture_query({**financial, "filtros": {"data": {"from": "2021-01-01", "to": "2022-01-01"}}})["rows"], [])
        with self.assertRaisesRegex(ValueError, "unsupported_synthetic_filter"):
            fixture_query({**industrial, "filtros": {"sql": "SELECT *"}})

    def test_rejected_queries_consume_global_budget(self):
        outputs = scripted_outputs()
        model = ScriptedModel([*outputs[:2], outputs[2], outputs[2]])
        attempts = []
        def rejected(plan):
            attempts.append(plan)
            raise ValueError("unsupported_synthetic_filter")
        result = run(QUESTION, MAPS, model, rejected, limits=Limits(queries=1))
        self.assertEqual(len(attempts), 1)
        self.assertEqual(result["query_attempts"], 1)
        self.assertEqual(result["queries"], 0)
        self.assertEqual(result["final_state"]["error"], "query_attempt_budget_exhausted")

    def test_rejected_query_filter_returns_to_specialist_once(self):
        outputs = scripted_outputs()
        bad_plan = {**outputs[2][1], "plano": {**outputs[2][1]["plano"],
                                               "filtros": {"sql": "SELECT *"}}}
        model = ScriptedModel([*outputs[:2], ("especialista_consulta", bad_plan), *outputs[2:]])
        result = run(QUESTION, MAPS, model, fixture_query, limits=Limits(queries=3))
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["queries"], 2)
        self.assertEqual(result["query_attempts"], 3)
        rejected = [event for event in result["trace"] if event["role"] == "synthetic_query"
                    and event["status"] == "rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["error"], "unsupported_synthetic_filter")
        planner_inputs = [envelope["input"] for role, envelope in model.calls
                          if role == "especialista_consulta"]
        self.assertEqual(planner_inputs[1]["correction_feedback"]["error_code"],
                         "unsupported_synthetic_filter")

    def test_openai_audit_uses_fresh_context_and_fixed_synthetic_prompt(self):
        conversations = []
        class FakeConversation:
            def __init__(self):
                self.calls = []
                conversations.append(self)
            def chat_turn(self, messages, temperature, max_tokens, *, tools, max_request_bytes=None):
                assert max_request_bytes == Limits().input_bytes
                self.calls.append((messages, temperature, max_tokens, tools))
                return {"content": "{}"}, {"provider": "openai", "model_id": "gpt-6-luna",
                                             "response_id": "resp_fixture"}
        with patch("inference_api.agent_harness.openai_audit.openai_provider.Conversation", FakeConversation), \
             patch("inference_api.agent_harness.openai_audit.openai_provider.configuration",
                   side_effect=AssertionError("unexpected network/config lookup")):
            for role in ("analista_pergunta", "especialista_consulta"):
                from inference_api.agent_harness.engine import CONTRACT
                raw, identity = openai_audit.model_call(role, {"role": role, "input": {"synthetic": True}},
                                                         CONTRACT["roles"][role])
                self.assertEqual(raw, "{}")
                self.assertEqual(identity["model_id"], "gpt-6-luna")
        self.assertEqual(len(conversations), 2)
        self.assertTrue(all(len(item.calls) == 1 for item in conversations))
        for item in conversations:
            messages, temperature, max_tokens, tools = item.calls[0]
            self.assertEqual((temperature, max_tokens, tools), (0, 4096, None))
            self.assertIn(synthetic_demo.PROTOCOL_PROMPT, messages[0]["content"])
            self.assertIn("Schema da entrada em input", messages[0]["content"])
            self.assertEqual(json.loads(messages[1]["content"])["input"], {"synthetic": True})

    def test_model_inputs_are_stable_across_run_ids_for_same_case(self):
        first = run(QUESTION, MAPS, ScriptedModel(scripted_outputs()), fixture_query)
        second = run(QUESTION, MAPS, ScriptedModel(scripted_outputs()), fixture_query)
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(first["case_fingerprint"], second["case_fingerprint"])
        self.assertEqual([event["input"] for event in first["trace"]],
                         [event["input"] for event in second["trace"]])

    def test_groq_harness_transport_sends_qwen_not_general_groq_model(self):
        requested = []
        model_id = "qwen/qwen3.8-27b"
        first = {"model": model_id, "choices": [{"index": 0, "delta": {"content": "{}"},
                                                   "finish_reason": None}]}
        last = {"model": model_id, "choices": [{"index": 0, "delta": {},
                                                  "finish_reason": "stop"}], "usage": {"total_tokens": 5}}

        class Stream:
            headers = {"Content-Type": "text/event-stream"}
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def __iter__(self):
                return iter([b"data: " + json.dumps(item).encode() + b"\n" for item in (first, last)] +
                            [b"data: [DONE]\n"])

        def urlopen(request, timeout):
            requested.append(json.loads(request.data))
            return Stream()

        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-key",
                                  "GROQ_MODEL": "openai/gpt-oss-120b",
                                  "GROQ_HARNESS_MODEL": model_id}), \
             patch("inference_api.model_service.groq.models.urlopen", side_effect=urlopen):
            message, metadata = groq.chat_turn([{"role": "user", "content": "fixture"}],
                                               0, 900, tools=None, harness_model=model_id)
        self.assertEqual(requested[0]["model"], model_id)
        self.assertEqual(message["content"], "{}")
        self.assertEqual(metadata["served_model"], model_id)

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass

    # Legacy creation contract archived; SPEC-014 explicitly rejects these requests.
    pass





    def test_selector_semantic_error_returns_to_same_role_once(self):
        outputs = scripted_outputs()
        invalid = {**outputs[1][1], "dominio_adicional": "financeiro"}
        model = ScriptedModel([*outputs[:1], ("selecionador_fontes", invalid), *outputs[1:]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["model_calls"], 9)
        self.assertEqual(next(e for e in result["trace"] if e["status"] == "rejected")["status"], "rejected")
        self.assertEqual(next(e for e in result["trace"] if e["status"] == "rejected")["error"], "invalid_consult_decision")
        feedback = next(e["input"]["correction_feedback"] for _, e in model.calls if "correction_feedback" in e["input"])
        self.assertIn("dominio_adicional deve ser null", feedback["hint"])



    def test_specialist_map_ids_are_not_evidence_ids(self):
        outputs = scripted_outputs()
        invalid = {**outputs[2][1], "evidence_refs": ["dw_paradas"]}
        model = ScriptedModel([*outputs[:2], ("especialista_consulta", invalid), *outputs[2:]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(next(e for e in result["trace"] if e["status"] == "rejected")["error"], "plan_unknown_evidence_refs")
        self.assertEqual(next(e["input"]["correction_feedback"] for _, e in model.calls if "correction_feedback" in e["input"])["error_code"],
                         "plan_unknown_evidence_refs")

    def test_causal_gap_does_not_skip_measurable_sources(self):
        outputs = scripted_outputs()
        inconsistent = {**outputs[0][1], "tratavel": False,
                        "lacunas": ["causalidade não comprovada"]}
        model = ScriptedModel([("analista_pergunta", inconsistent), *outputs])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["trace"][0]["error"], "analysis_domain_consistency")
        self.assertEqual(result["queries"], 2)

    def test_no_evidence_is_never_answered_status(self):
        need = {"entidade": "nenhuma", "medida": "nenhuma", "periodo": "nenhum", "grao": "nenhum"}
        model = ScriptedModel([
            ("analista_pergunta", {"tratavel": False, "necessidade": need,
                                  "dominios": [], "lacunas": ["sem fonte"]}),
            ("redator_resposta", {"resposta": "Sem evidência.",
                                   "evidencias_utilizadas": [], "calculos": [],
                                   "ressalvas": ["Sem evidência"]})])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["queries"], 0)

    def test_redactor_citations_require_exact_result_ids(self):
        outputs = scripted_outputs()
        invalid = {**outputs[-1][1], "evidencias_utilizadas": ["result_01: 45 minutos"]}
        model = ScriptedModel([*outputs[:-1], ("redator_resposta", invalid), outputs[-1]])
        result = run(QUESTION, MAPS, model, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["trace"][-2]["error"], "answer_unknown_evidence")
        self.assertEqual(result["response"]["evidencias_utilizadas"], ["result_01", "result_02"])

    def test_malformed_json_gets_one_visible_retry(self):
        outputs = scripted_outputs()
        model = ScriptedModel([("analista_pergunta", None), outputs[0], *outputs[1:]])
        def transport(role, envelope, contract):
            if not model.calls:
                model.calls.append((role, envelope))
                model.outputs.pop(0)
                return "not json", {"provider": "fixture", "model_id": "same-candidate"}
            return model(role, envelope, contract)
        result = run(QUESTION, MAPS, transport, fixture_query)
        self.assertEqual(result["status"], "answered_unverified")
        self.assertEqual(result["trace"][0]["status"], "rejected")
        self.assertIn("correction_feedback", model.calls[1][1]["input"])

    def test_real_map_is_rejected(self):
        maps = {"dw": {**MAPS["dw"], "synthetic": False}}
        with self.assertRaisesRegex(HarnessError, "real_or_invalid_domain_map_blocked"):
            run(QUESTION, maps, lambda *args: self.fail("model called"), fixture_query)

    def test_provider_failure_is_traced_and_not_retried(self):
        class ProviderFailure(RuntimeError):
            status = "provider_rate_limited"
            retry_after = "60"
        calls = []
        def transport(role, envelope, contract):
            calls.append(role)
            raise ProviderFailure()
        result = run(QUESTION, MAPS, transport, fixture_query)
        self.assertEqual(calls, ["analista_pergunta"])
        self.assertEqual(result["trace"][0]["status"], "provider_error")
        self.assertEqual(result["trace"][0]["retry_after"], "60")

    def test_candidate_change_stops_before_query(self):
        outputs = ScriptedModel(scripted_outputs()).outputs
        first = True
        def transport(role, envelope, contract):
            nonlocal first
            expected_role, output = outputs.pop(0)
            self.assertEqual(role, expected_role)
            model_id = "model-a" if first else "model-b"
            first = False
            return json.dumps(output), {"provider": "fixture", "model_id": model_id}
        result = run(QUESTION, MAPS, transport, fixture_query)
        self.assertEqual(result["status"], "contract_error")
        self.assertEqual(result["final_state"]["error"], "model_identity_changed")
        self.assertEqual(result["queries"], 0)

    def test_query_failure_is_traced_before_review(self):
        model = ScriptedModel(scripted_outputs())
        def failed_query(plan):
            raise RuntimeError("fixture failure")
        result = run(QUESTION, MAPS, model, failed_query)
        self.assertEqual(result["status"], "contract_error")
        self.assertEqual(result["final_state"]["error"], "synthetic_query_error")
        self.assertEqual(result["trace"][-1]["status"], "rejected")
        self.assertEqual(result["queries"], 0)


if __name__ == "__main__":
    unittest.main()
