from .dw_query import DWQuery
from .contributors import Contributors
from .trace import Trace
from .industrial_query import IndustrialQuery
from .financial_query import FinancialQuery

def resolve(source):
    if source['domain'] == 'industrial': return IndustrialQuery()
    if source['domain'] == 'financeiro': return FinancialQuery()
    # Approved map kind, not arbitrary model text, selects the lineage tool.
    kind = source.get('kind', source.get('query_kind', ''))
    if kind == 'contributors' or source['id'].endswith('contributors'): return Contributors()
    if kind == 'trace' or source['id'].endswith('trace'): return Trace()
    return DWQuery()
