"""Real business routers plus inert probes for AI/stream and future endpoints."""

from django.contrib import admin
from django.http import JsonResponse, StreamingHttpResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class DefaultPermissionProbe(APIView):
    def get(self, request):
        return Response({'user': request.user.username})


class ExplicitAnonymousProbe(DefaultPermissionProbe):
    authentication_classes = []
    permission_classes = [AllowAny]


stream_events = []


@csrf_exempt
def stream_probe(request):
    def chunks():
        stream_events.append('started')
        yield f'data: {request.user.username}\n\n'.encode()
        yield b'data: [DONE]\n\n'
    return StreamingHttpResponse(chunks(), content_type='text/event-stream')


def identity_probe(request):
    return JsonResponse({'user': request.user.username, 'auth': request.auth.key})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/company-reviews/', include('company_reviews.urls')),
    path('api/career-paths/', include('career_paths.urls')),
    path('api/career-evaluation/', include('career_evaluation.urls')),
    path('api/resumes/', include('resumes.urls')),
    path('api/ai/llm/chat/', stream_probe),
    path('api/career-report/', identity_probe),
    path('api/default-probe/', DefaultPermissionProbe.as_view()),
    path('api/future-probe/', ExplicitAnonymousProbe.as_view()),
    path('api/identity-probe/', identity_probe),
    path('static/probe.css', lambda request: JsonResponse({'static': True})),
]
