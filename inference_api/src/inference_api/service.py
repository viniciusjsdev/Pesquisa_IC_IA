"""One request owns its deterministic route, LLM call and immutable snapshot."""
from dataclasses import asdict

from . import config, evidence, models, orchestrator, response_agent, storage, verifier
from .contracts import ModelOutput, QuestionRequest, RunSnapshot, SCHEMA_VERSION


def _options(payload: dict) -> tuple[float, int]:
    temperature = payload.get("temperature", 0)
    max_tokens = payload.get("max_tokens", 256)
    if type(temperature) not in (float, int) or not 0 <= temperature <= 2:
        raise ValueError("Temperature must be between 0 and 2")
    if type(max_tokens) is not int or not 1 <= max_tokens <= 1024:
        raise ValueError("max_tokens must be between 1 and 1024")
    return temperature, max_tokens


def _prompt(payload: dict) -> dict:
    prompt_id = payload.get("prompt_revision_id")
    draft = payload.get("system_prompt")
    if (prompt_id is None) == (draft is None):
        raise ValueError("Provide exactly one prompt_revision_id or system_prompt")
    if prompt_id is not None:
        prompt = storage.get_prompt(prompt_id)
        if prompt is None:
            raise ValueError("Prompt revision not found")
        return {"schema_version": 1, "revision_id": prompt_id, "revision": prompt["revision"],
                "system_prompt": prompt["system_prompt"]}
    if not isinstance(draft, str) or not draft.strip() or len(draft) > 20000:
        raise ValueError("System prompt is required and limited to 20000 characters")
    return {"schema_version": 1, "revision_id": None, "revision": None, "system_prompt": draft}


def execute_run(payload: dict) -> dict:
    author, question, alias = (payload.get(key) for key in ("author", "question", "model_alias"))
    if not isinstance(author, str) or not author.strip() or len(author) > 100:
        raise ValueError("Author is required")
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise ValueError("Question is required and limited to 4000 characters")
    if not isinstance(alias, str) or alias not in models.MODELS:
        raise ValueError("Unknown model alias")
    temperature, max_tokens = _options(payload)
    prompt = _prompt(payload)
    model = {"alias": alias, "base": models.BASE,
             "battery": models.MODELS[alias]["battery"], "endpoint": config.vllm_url() or None,
             "base_revision": None, "adapter_run": None, "adapter_hash": None,
             "parameters": {"temperature": temperature, "max_tokens": max_tokens}}
    input_year = payload.get("year")
    request = QuestionRequest(question, str(payload.get("scope", payload.get("evidence_route"))),
                              input_year if type(input_year) is int else None,
                              alias, temperature, max_tokens, "unresolved")
    route = bundle = output = None
    checks = ()
    status = "route_error"
    error = None
    try:
        request, route = orchestrator.plan(payload, alias, question, temperature, max_tokens)
    except ValueError as exc:
        error = {"stage": "route", "type": type(exc).__name__, "message": str(exc)}
    else:
        try:
            bundle = evidence.assemble(route)
        except evidence.SourceQueryError as exc:
            status = "query_error"
            error = {"stage": "query", "type": exc.cause_type, "tool": exc.tool}
        except Exception as exc:
            status = "evidence_error"
            error = {"stage": "evidence", "type": type(exc).__name__}
        else:
            if bundle.quality != "available":
                status = "insufficient_evidence"
                error = {"stage": "evidence", "type": "MissingRequiredEvidence"}
            else:
                # The serialized bundle is the same object saved and sent to the model.
                bundle_payload = asdict(bundle)
                try:
                    output = response_agent.respond(alias, prompt, question,
                                                    bundle_payload, temperature, max_tokens)
                except models.ModelResponseError as exc:
                    output = ModelOutput(SCHEMA_VERSION, None, (), exc.serving)
                    model.update({key: exc.serving.get(key) for key in
                                  ("endpoint", "base_revision", "adapter_run", "adapter_hash")})
                    model["served_model"] = exc.serving.get("served_model")
                    status = "response_error"
                    error = {"stage": "response", "type": type(exc).__name__}
                except Exception as exc:
                    status = "model_error"
                    error = {"stage": "model", "type": type(exc).__name__}
                else:
                    model.update({key: output.serving.get(key) for key in
                                  ("endpoint", "base_revision", "adapter_run", "adapter_hash")})
                    model["served_model"] = output.serving.get("served_model")
                    if not isinstance(output.raw_text, str) or not output.raw_text.strip():
                        status = "response_error"
                        error = {"stage": "response", "type": "EmptyModelResponse"}
                    else:
                        try:
                            checks = verifier.check(bundle, output)
                            status = "answered_unverified"
                        except Exception as exc:
                            status = "verification_error"
                            error = {"stage": "verification", "type": type(exc).__name__}
    snapshot = RunSnapshot(SCHEMA_VERSION, request, prompt, model, route, bundle,
                           output, checks, status, error)
    return storage.create_run(author, snapshot.to_dict())
