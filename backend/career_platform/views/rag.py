from ..api import PlatformView
from .. import serializers as s
from ..models import ResumeAnalysisRun, EvaluationRun, PracticeSession
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class Retrieve(PlatformView):
    module = 'rag'
    operations = {'POST': 'retrieve'}
    input_serializers = {'POST': s.RetrieveQuestions}

class Answers(PlatformView):
    module = 'rag'
    operations = {'POST': 'answer'}
    input_serializers = {'POST': s.SubmitAnswer}
    model = PracticeSession

