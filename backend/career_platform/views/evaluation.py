from ..api import PlatformView
from .. import serializers as s
from ..models import ResumeAnalysisRun, EvaluationRun, PracticeSession
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class EvaluationRuns(PlatformView):
    module = 'evaluation'
    operations = {'GET': 'list_runs', 'POST': 'run'}
    input_serializers = {'GET': s.Query, 'POST': s.RunEvaluation}
    permission_classes = [IsAuthenticated, IsAdminUser]

class EvaluationDetail(PlatformView):
    module = 'evaluation'
    operations = {'GET': 'get_run'}
    input_serializers = {'GET': s.Query}
    model = EvaluationRun
    permission_classes = [IsAuthenticated, IsAdminUser]

class EvaluationExport(PlatformView):
    module = 'evaluation'
    operations = {'GET': 'export'}
    input_serializers = {'GET': s.Query}
    model = EvaluationRun
    permission_classes = [IsAuthenticated, IsAdminUser]

