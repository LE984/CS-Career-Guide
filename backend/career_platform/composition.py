"""The sole production composition root; never import test adapters here."""
from .catalog.service import CatalogService
from .evaluation.service import EvaluationService
from .resume.service import ResumeAnalysisService
from .rag.service import InterviewRagService
from .records.service import PracticeService


def build_services():
    return dict(catalog=CatalogService(), evaluation=EvaluationService(), resume=ResumeAnalysisService(), rag=InterviewRagService(), records=PracticeService())

services = build_services()
