"""Require a real API token for every business endpoint, including Django views."""

from django.http import HttpResponse, JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ApiTokenRequiredMiddleware:
    # Keep this whitelist exact: a new API is protected unless explicitly added.
    public_paths = frozenset({
        '/api/users/auth/login/',
        '/api/users/auth/register/',
    })

    def __init__(self, get_response):
        self.get_response = get_response
        self.authentication = TokenAuthentication()

    def __call__(self, request):
        path = request.path_info
        if path == '/api' or path.startswith('/api/'):
            # CorsMiddleware handles cross-origin preflight first. Other OPTIONS
            # requests must also terminate here, never execute a business view.
            if request.method == 'OPTIONS':
                return HttpResponse(status=204)
            if path not in self.public_paths:
                try:
                    credentials = self.authentication.authenticate(request)
                except AuthenticationFailed as error:
                    return self.unauthorized(str(error.detail))
                except UnicodeError:
                    return self.unauthorized('Invalid token header.')
                if credentials is None:
                    return self.unauthorized('Authentication credentials were not provided.')
                # Ordinary Django views need the same identity as DRF views.
                request.user, request.auth = credentials
        return self.get_response(request)

    @staticmethod
    def unauthorized(detail):
        response = JsonResponse({'detail': detail}, status=401)
        response['WWW-Authenticate'] = 'Token'
        return response
