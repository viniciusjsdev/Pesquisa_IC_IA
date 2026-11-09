def validation_location(error):
    """JSON pointer from schema-defined names, never untrusted instance keys."""
    path = list(error.absolute_schema_path)
    segments = []
    for index, segment in enumerate(path[:-1]):
        if segment == 'properties' and isinstance(path[index + 1], str):
            segments.append(path[index + 1])
        elif segment == 'items':
            segments.append('*')
    return ''.join('/' + part.replace('~', '~0').replace('/', '~1') for part in segments)

TERMINAL = {'action_forbidden', 'source_forbidden', 'model_identity_changed',
            'missing_model_identity', 'model_output_limit'}
REPAIRABLE_QUERY = {'plan_outside_selected_map', 'invalid_typed_plan',
    'plan_source_or_grain_mismatch', 'fields_outside_catalog', 'row_limit_invalid',
    'filters_outside_catalog', 'invalid_range_filter', 'invalid_id_filter',
    'invalid_lineage_filter', 'invalid_synthetic_filters', 'unsupported_synthetic_filter',
    'invalid_synthetic_date_filter'}
class ProtocolError(ValueError): pass
def require(value, error):
    if not value: raise ProtocolError(error)
