"""Compatibility module alias; implementation lives in data_access.queries."""
import sys
from ..data_access.queries import typed_detail as _implementation
sys.modules[__name__] = _implementation
