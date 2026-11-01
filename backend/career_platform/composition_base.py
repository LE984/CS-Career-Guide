from .errors import FeatureNotImplemented

class UnavailableService:
    def __init__(self, module):
        self.module = module

    def __getattr__(self, operation):
        if operation.startswith('_'):
            raise AttributeError(operation)

        def unavailable(**kwargs):
            raise FeatureNotImplemented(self.module, operation)
        return unavailable

