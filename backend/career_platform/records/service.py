"""Member application service: business remains explicitly unavailable."""
from ..composition_base import UnavailableService

class PracticeService(UnavailableService):
    def __init__(self, *, repository=None, model_gateway=None):
        super().__init__('records')
        self.repository = repository
        self.model_gateway = model_gateway
