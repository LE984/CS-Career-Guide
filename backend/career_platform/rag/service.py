"""Member application service: business remains explicitly unavailable."""
from ..composition_base import UnavailableService

class InterviewRagService(UnavailableService):
    def __init__(self, *, retriever=None, model_gateway=None, records=None):
        super().__init__('rag')
        self.retriever = retriever
        self.model_gateway = model_gateway
        self.records = records
