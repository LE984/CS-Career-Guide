"""Member application service: business remains explicitly unavailable."""
from ..composition_base import UnavailableService

class ResumeAnalysisService(UnavailableService):
    def __init__(self, *, model_gateway=None, matcher=None, repository=None):
        super().__init__('resume')
        self.model_gateway = model_gateway
        self.matcher = matcher
        self.repository = repository
