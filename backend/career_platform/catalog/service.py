"""Member application service: business remains explicitly unavailable."""
from ..composition_base import UnavailableService

class CatalogService(UnavailableService):
    def __init__(self, *, source_adapter=None, index_notifier=None):
        super().__init__('catalog')
        self.source_adapter = source_adapter
        self.index_notifier = index_notifier
