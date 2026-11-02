"""建议列表与投稿：独立于模型服务，查询始终分页。"""
import logging

from django.db import DatabaseError
from django.db.models import Q
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SeniorAdvice
from .serializers import SeniorAdviceSerializer

logger = logging.getLogger(__name__)


class AdvicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def senior_advice_list(request):
    try:
        if request.method == 'GET':
            queryset = SeniorAdvice.objects.filter(is_approved=True)
            search = request.query_params.get('search', '').strip()
            if search:
                queryset = queryset.filter(Q(company__icontains=search) | Q(position__icontains=search))
            ordering = request.query_params.get('ordering', 'recent')
            if ordering not in ('recent', 'rating'):
                return Response({'message': '排序方式无效，请选择最新提交或评分最高。'}, status=400)
            queryset = queryset.order_by(*(['-rating', '-created_at', '-pk'] if ordering == 'rating' else ['-created_at', '-pk']))
            paginator = AdvicePagination()
            page = paginator.paginate_queryset(queryset, request)
            return Response({
                'success': True, 'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(), 'previous': paginator.get_previous_link(),
                'results': SeniorAdviceSerializer(page, many=True).data,
            })

        serializer = SeniorAdviceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False, 'message': '请检查标出的表单内容。', 'errors': serializer.errors}, status=400)
        serializer.save(user=request.user, is_approved=False)
        return Response({'success': True, 'message': '建议提交成功，等待审核。', 'data': serializer.data}, status=201)
    except DatabaseError:
        logger.exception('学长学姐建议数据库操作失败')
        action = '读取' if request.method == 'GET' else '保存'
        return Response({'success': False, 'code': 'ADVICE_UNAVAILABLE', 'message': f'建议暂时无法{action}，请稍后重试。'}, status=503)
