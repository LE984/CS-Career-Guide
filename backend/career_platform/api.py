from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from . import composition
from .errors import FeatureNotImplemented


class PlatformView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    module = None
    operations = {}
    input_serializers = {}
    model = None

    def handle_exception(self, exc):
        from rest_framework.exceptions import APIException
        # Unexpected provider/adapter exceptions must never expose raw payloads.
        if not isinstance(exc, (APIException,)):
            from django.http import Http404
            from django.core.exceptions import PermissionDenied
            if not isinstance(exc, (Http404, PermissionDenied)):
                return Response({'code':'INTERNAL_ERROR','message':'服务暂时不可用','details':{}},status=500)
        response = super().handle_exception(exc)
        code = ('FEATURE_NOT_IMPLEMENTED' if isinstance(exc, FeatureNotImplemented) else
                {400: 'VALIDATION_ERROR', 401: 'UNAUTHENTICATED', 403: 'FORBIDDEN',
                 404: 'NOT_FOUND', 405: 'METHOD_NOT_ALLOWED', 409: 'CONFLICT'}.get(response.status_code, 'REQUEST_FAILED'))
        details = response.data
        response.data = {'code': code, 'message': '功能待实现' if response.status_code == 501 else str(getattr(exc, 'default_detail', '请求失败')), 'details': details}
        return response

    def dispatch_operation(self, request, pk=None):
        from rest_framework.exceptions import NotFound
        serializer = self.input_serializers[request.method](data=request.query_params if request.method == 'GET' else request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        if pk is not None:
            if self.model is not None and not self.model.objects.filter(pk=pk, user=request.user).exists():
                raise NotFound()
            data['id'] = pk
        result = getattr(composition.services[self.module], self.operations[request.method])(user=request.user, data=data)
        return Response(result)

    def get(self, request, pk=None):
        if 'GET' not in self.operations:
            return self.http_method_not_allowed(request)
        return self.dispatch_operation(request, pk)

    def post(self, request, pk=None):
        if 'POST' not in self.operations:
            return self.http_method_not_allowed(request)
        return self.dispatch_operation(request, pk)
