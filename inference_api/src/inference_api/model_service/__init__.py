"""Internal, provider-neutral inference boundary for SPEC-014."""
from .service import ModelService, ModelError
from .registry import profiles, resolve

__all__ = ['ModelService', 'ModelError', 'profiles', 'resolve']
