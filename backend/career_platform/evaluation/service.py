"""Member application service: business remains explicitly unavailable."""
from ..composition_base import UnavailableService

class EvaluationService(UnavailableService):
    def __init__(self, *, strategies=None, dataset_loader=None):
        super().__init__('evaluation')
        self.strategies = strategies
        self.dataset_loader = dataset_loader
