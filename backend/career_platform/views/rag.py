from ..api import PlatformView
from .. import serializers as s
from ..models import ResumeAnalysisRun, EvaluationRun, PracticeSession
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import serializers
from rest_framework.response import Response


class DemoQuery(s.StrictSerializer):
    query = serializers.CharField(max_length=500, allow_blank=True, default='')
    role = serializers.CharField(max_length=100)
    topic = serializers.CharField(max_length=100, allow_blank=True, default='')
    difficulty = serializers.ChoiceField(choices=['easy', 'medium', 'hard'], default='easy')
    top_k = serializers.IntegerField(min_value=1, max_value=20, default=5)


class DemoRetrieve(PlatformView):
    """只读演示独立于正式检索，沿用登录鉴权和统一错误格式。"""

    module = 'rag'
    operations = {'POST': 'demo_retrieve'}
    input_serializers = {'POST': DemoQuery}

class Retrieve(PlatformView):
    module = 'rag'
    operations = {'POST': 'retrieve'}
    input_serializers = {'POST': s.RetrieveQuestions}

class Answers(PlatformView):
    module = 'rag'
    operations = {'POST': 'answer'}
    input_serializers = {'POST': s.SubmitAnswer}
    model = PracticeSession


class RetryAnswerFeedback(PlatformView):
    module = 'rag'

    def post(self, request, session_pk=None, pk=None):
        serializer = s.RetryFeedback(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data, session_id=session_pk, id=pk)
        result = self.get_service().retry_feedback(user=request.user, data=data)
        return Response(result)

    @staticmethod
    def get_service():
        from .. import composition
        return composition.services['rag']

