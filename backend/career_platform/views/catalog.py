from ..api import PlatformView
from .. import serializers as s
from ..models import ResumeAnalysisRun, EvaluationRun, PracticeSession
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class Companies(PlatformView):
    module = 'catalog'
    operations = {'GET': 'companies'}
    input_serializers = {'GET': s.Query}

class Jobs(PlatformView):
    module = 'catalog'
    operations = {'GET': 'jobs'}
    input_serializers = {'GET': s.Query}

class Questions(PlatformView):
    module = 'catalog'
    operations = {'GET': 'questions'}
    input_serializers = {'GET': s.Query}

class Imports(PlatformView):
    module = 'catalog'
    operations = {'POST': 'import_batch'}
    input_serializers = {'POST': s.ImportBatch}
    permission_classes = [IsAuthenticated, IsAdminUser]

