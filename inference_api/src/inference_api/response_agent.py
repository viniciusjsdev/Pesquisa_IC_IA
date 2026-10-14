"""The sole LLM caller. It receives no database handle or evaluation labels."""
from . import models, verifier
from .contracts import ModelOutput, SCHEMA_VERSION


def respond(alias: str, prompt: dict, question: str, bundle: dict,
            temperature: float, max_tokens: int) -> ModelOutput:
    raw_text, serving = models.infer(alias, prompt["system_prompt"], question, bundle,
                                     temperature, max_tokens)
    return ModelOutput(SCHEMA_VERSION, raw_text,
                       verifier.cited_ids(raw_text) if isinstance(raw_text, str) else (),
                       serving)
