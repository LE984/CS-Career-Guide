from ..api import PlatformView
from .. import serializers as s
from ..models import ResumeAnalysisRun, EvaluationRun, PracticeSession
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class PracticeSessions(PlatformView):
    module = 'records'
    operations = {'GET': 'list_sessions', 'POST': 'start'}
    input_serializers = {'GET': s.Query, 'POST': s.StartPractice}

class PracticeDetail(PlatformView):
    module = 'records'
    operations = {'GET': 'get_session'}
    input_serializers = {'GET': s.Query}
    model = PracticeSession

class PracticeFinish(PlatformView):
    module = 'records'
    operations = {'POST': 'finish'}
    input_serializers = {'POST': s.FinishPractice}
    model = PracticeSession

