from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import DatabaseError
from django.db.models import Q
import logging
from .models import CareerCategory, ComputerCareer
from .serializers import CareerCategorySerializer, ComputerCareerSerializer


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CareerCategoryViewSet(viewsets.ModelViewSet):
    queryset = CareerCategory.objects.all()
    serializer_class = CareerCategorySerializer
    
    def get_queryset(self):
        # 按市场需求和排序字段排序
        return CareerCategory.objects.order_by('order', '-market_demand')


class ComputerCareerViewSet(viewsets.ReadOnlyModelViewSet):
    """计算机职业API"""
    queryset = ComputerCareer.objects.all()
    serializer_class = ComputerCareerSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except DatabaseError:
            logging.getLogger(__name__).exception('职位列表数据库查询失败')
            return Response({'code': 'JOBS_UNAVAILABLE', 'message': '职位数据暂时无法读取，请稍后重试。'}, status=503)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选参数
        position_name = self.request.query_params.get('position_name')
        company_name = self.request.query_params.get('company_name')
        address = self.request.query_params.get('address')
        industry = self.request.query_params.get('industry')
        search = self.request.query_params.get('search', '').strip()
        
        # 应用筛选
        if position_name:
            queryset = queryset.filter(position_name__icontains=position_name)
        if company_name:
            queryset = queryset.filter(company_name__icontains=company_name)
        if address:
            queryset = queryset.filter(address__icontains=address)
        if industry:
            queryset = queryset.filter(industry__icontains=industry)

        if search:
            queryset = queryset.filter(
                Q(position_name__icontains=search) | Q(company_name__icontains=search)
                | Q(address__icontains=search) | Q(industry__icontains=search)
                | Q(position_details__icontains=search) | Q(company_details__icontains=search)
            )
        
        # 直接展示记录；固定主键顺序保证分页稳定，不做时效排序或个性化推荐。
        queryset = queryset.order_by('pk')
        
        return queryset
