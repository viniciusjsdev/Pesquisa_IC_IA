"""No SDK import or active exporter in off mode."""
from contextlib import nullcontext
class Noop:
    enabled = False
    def __init__(self, diagnostic=None): self.diagnostic = diagnostic
    def start(self, *args, **kwargs): return None
    def end(self, *args, **kwargs): pass
    def activate(self, span): return nullcontext()
    def annotate(self, metadata): pass
    def attach_receipt(self,*args,**kwargs): pass
    def bind_run(self,*args,**kwargs): pass
    def finish(self, *args, **kwargs):
        return {'state': 'disabled', **({'diagnostic': self.diagnostic} if self.diagnostic else {})}
    def snapshot(self): return self.finish()
