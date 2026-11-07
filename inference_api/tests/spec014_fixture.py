"""Invented local-only fixture shared by unit and browser integration tests."""
import json
from copy import deepcopy
from inference_api.agent_harness.synthetic_demo import MAPS, fixture_query
from inference_api.model_service.registry import digest

QUESTION = 'Compare as três fontes fictícias; associação não prova causalidade.'


def profile(adapter='groq_chat'):
    p = {'id': 'fixture-' + adapter, 'version': 1, 'provider_id': adapter,
         'adapter_id': adapter, 'requested_model': 'fixture-model',
         'deployment_id': 'local-fake', 'endpoint': 'http://127.0.0.1:1/fake',
         'configured': True, 'availability': 'unknown', 'key_env': None,
         'capabilities': {'temperature': True, 'seed': False, 'reasoning_effort': False,
                          'omit_output_limit': True, 'json_schema': 'prompt_validated', 'streaming': True},
         'require_serving_identity': False, 'fixture': True}
    p['sha256'] = digest(p)
    return p


def packet():
    body = {'case_id': 'fixture', 'question': QUESTION,
            'evidence_items': [{'grain': 'fixture/year', 'rows': [{'value': 42}],
                'coverage': {'rows': 1, 'state': 'observed'}, 'units': {'value': 'fixture'}}]}
    return {'body': body, 'sha256': digest(body)}


def answer(envelope):
    role, i, r = envelope['role'], envelope['input'], envelope['round']
    fixed = envelope['scenario'] == 'fixed_evidence'
    if role == 'analista_pergunta':
        return {'tratavel': True, 'necessidade': dict(entidade='fixture', medida='total', periodo='2020', grao='fixture'),
                'dominios': ['dw'] if fixed else ['dw', 'industrial', 'financeiro'], 'lacunas': []}
    if role == 'selecionador_fontes':
        sid = i['available_source_ids'][0] if fixed else ['dw_paradas', 'ind_parada', 'fin_resultado'][min(r-1, 2)]
        return {'selection_kind': 'packet_source' if fixed else 'query_source', 'decisao': 'consultar',
                'justificativa': 'Fonte fixture', 'fonte_id': sid, 'dominio_adicional': None, 'map_refs': [sid]}
    if role == 'especialista_consulta':
        if fixed:
            return {'action': 'analyze_packet', 'evidence_refs': i['available_evidence_ids'],
                    'findings': ['A fixture informa 42.'], 'gaps': []}
        source = i['source_contract']
        return {'action': 'query_source', 'plano': {'fonte_id': source['id'], 'campos': source['fields'],
            'grao': source['grain'], 'limite': 20, 'filtros': {}}, 'justificativa': 'Leitura fixture',
            'evidence_refs': i['available_evidence_ids']}
    if role == 'revisor_evidencias':
        more = not fixed and r < 3
        return {'decisao': 'precisa_aprofundar' if more else 'suficiente',
            'evidencias_utilizadas': i['available_evidence_ids'], 'justificativa': 'Fixture',
            'lacuna': 'Falta outra fonte' if more else None, 'proximo_dado_necessario': 'Detalhe' if more else None,
            'dominio_sugerido': ['industrial', 'financeiro'][r-1] if more else None}
    return {'resposta': 'Resposta da fixture sintética; sem avaliação científica.',
            'evidencias_utilizadas': i['available_evidence_ids'], 'calculos': [],
            'ressalvas': ['Associação não prova causalidade.']}


class Stream:
    headers = {'Content-Type': 'text/event-stream', 'x-request-id': 'fixture-request'}
    def __init__(self, lines): self.lines = lines
    def __iter__(self): return iter(self.lines)
    def __enter__(self): return self
    def __exit__(self, *_): pass


class Transport:
    def __init__(self, mutate=None, fail=None, finish='stop', usage=True):
        self.requests, self.envelopes = [], []
        self.mutate, self.fail, self.finish, self.usage = mutate, fail, finish, usage
    def __call__(self, request, timeout):
        self.requests.append(request)
        body = json.loads(request.data)
        envelope = json.loads((body.get('input') or body['messages'])[-1]['content'])
        self.envelopes.append(envelope)
        if self.fail: raise self.fail
        value = answer(envelope)
        if self.mutate: value = self.mutate(envelope, value)
        raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        if 'input' in body:
            result = {'model': body['model'], 'status': 'completed', 'id': 'fixture',
                'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': raw}]}]}
            if self.usage: result['usage'] = {'input_tokens': 10, 'output_tokens': 20}
            lines = [b'data: ' + json.dumps({'type': 'response.completed', 'response': result}).encode() + b'\n']
        else:
            chunk = {'model': body['model'], 'choices': [{'index': 0, 'delta': {'content': raw}, 'finish_reason': self.finish}]}
            if self.usage: chunk['usage'] = {'prompt_tokens': 10, 'completion_tokens': 20}
            lines = [b'data: ' + json.dumps(chunk).encode() + b'\n', b'data: [DONE]\n']
        return Stream(lines)
