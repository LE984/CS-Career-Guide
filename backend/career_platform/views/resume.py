from ..api import PlatformView
from .. import serializers as s
from ..models import ResumeAnalysisRun, EvaluationRun, PracticeSession
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class ResumeAnalyses(PlatformView):
    module = 'resume'
    operations = {'GET': 'list_runs', 'POST': 'analyze'}
    input_serializers = {'GET': s.Query, 'POST': s.AnalyzeResume}

class ResumeDetail(PlatformView):
    module = 'resume'
    operations = {'GET': 'get_run'}
    input_serializers = {'GET': s.Query}
    model = ResumeAnalysisRun

class ResumeApply(PlatformView):
    module = 'resume'
    operations = {'POST': 'apply'}
    input_serializers = {'POST': s.ApplySuggestions}
    model = ResumeAnalysisRun

