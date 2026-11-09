from .question_analyst import QuestionAnalyst
from .source_selector import SourceSelector
from .consolidated_specialist import ConsolidatedSpecialist
from .industrial_specialist import IndustrialSpecialist
from .financial_specialist import FinancialSpecialist
from .evidence_reviewer import EvidenceReviewer
from .answer_writer import AnswerWriter

AGENTS = {a.role_id: a for a in (QuestionAnalyst(), SourceSelector(), EvidenceReviewer(), AnswerWriter())}
SPECIALISTS = {a.domain: a for a in (ConsolidatedSpecialist(), IndustrialSpecialist(), FinancialSpecialist())}
def resolve(role, domain='dw'):
    return SPECIALISTS[domain] if role == 'especialista_consulta' else AGENTS[role]
