"""The sole production composition root; never import test adapters here."""
from .catalog.service import CatalogService
from .evaluation.service import EvaluationService
from .resume.service import ResumeAnalysisService
from .rag.service import InterviewRagService
from .records.service import PracticeService
from .rag.retrieval import DjangoQuestionRetriever
from .records.repository import DjangoPracticeRepository
from .gateway import JsonModelGateway


def build_services():
    gateway = JsonModelGateway()
    records = PracticeService(repository=DjangoPracticeRepository(), model_gateway=gateway)
    rag = InterviewRagService(
        retriever=DjangoQuestionRetriever(), model_gateway=gateway, records=records,
    )
    return dict(
        catalog=CatalogService(), evaluation=EvaluationService(),
        resume=ResumeAnalysisService(model_gateway=gateway), rag=rag, records=records,
    )

services = build_services()
