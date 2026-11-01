from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Company, CompanyInfo, JobFair
from career_platform.permissions import StaffWritePermission
from .serializers import CompanySerializer, CompanyInfoSerializer, JobFairSerializer


class StandardPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    pagination_class = StandardPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, StaffWritePermission]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选参数
        job_title = self.request.query_params.get('job_title')
        city = self.request.query_params.get('city')
        scale = self.request.query_params.get('scale')
        nature = self.request.query_params.get('nature')
        min_salary = self.request.query_params.get('min_salary')
        max_salary = self.request.query_params.get('max_salary')
        ranking = self.request.query_params.get('ranking')
        
        # 应用筛选
        if job_title:
            # 同时搜索公司名称和职位标题
            queryset = queryset.filter(Q(name__icontains=job_title) | Q(jobs__title__icontains=job_title))
        if city:
            queryset = queryset.filter(city=city)
        if scale:
            queryset = queryset.filter(scale=scale)
        if nature:
            queryset = queryset.filter(nature=nature)
        if min_salary:
            queryset = queryset.filter(avg_salary__gte=min_salary)
        if max_salary:
            queryset = queryset.filter(avg_salary__lte=max_salary)
        if ranking:
            queryset = queryset.filter(ranking=ranking)
        
        # 去重
        queryset = queryset.distinct()
        
        # 排序：红榜优先，然后按名称排序
        queryset = queryset.order_by('-ranking', 'name')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        # 获取所有可能的筛选选项
        cities = Company.objects.values_list('city', flat=True).distinct()
        scales = dict(Company.SCALE_CHOICES)
        natures = dict(Company.NATURE_CHOICES)
        rankings = dict(Company.RANKING_CHOICES)
        
        return Response({
            'cities': list(cities),
            'scales': scales,
            'natures': natures,
            'rankings': rankings
        })
    
    @action(detail=False, methods=['post'])
    def submit(self, request):
        # 处理企业评价提交
        company_name = request.data.get('company_name')
        ranking = request.data.get('ranking')
        reason = request.data.get('reason')
        
        if not company_name or not ranking or not reason:
            return Response({'error': '缺少必要参数'}, status=400)
        
        # 验证 ranking 值
        if ranking not in ['red', 'black']:
            return Response({'error': '无效的榜单类型'}, status=400)
        
        # 查找或创建企业
        try:
            company = Company.objects.get(name=company_name)
        except Company.DoesNotExist:
            # 创建新企业记录（使用默认值）
            company = Company(
                name=company_name,
                city='未知',
                scale='small',
                nature='private',
                ranking=ranking,
                avg_salary=0,
                description='',
                warning_info=reason if ranking == 'black' else ''
            )
        else:
            # 更新现有企业
            company.ranking = ranking
            if ranking == 'black':
                company.warning_info = reason
            else:
                company.warning_info = ''
        
        company.save()
        
        return Response({'success': True, 'message': '企业评价提交成功'})


class CompanyInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """公司职位信息查询API（从company_info表）"""
    queryset = CompanyInfo.objects.all()
    serializer_class = CompanyInfoSerializer
    pagination_class = StandardPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选参数
        job_title = self.request.query_params.get('job_title')
        company_name = self.request.query_params.get('company_name')
        address = self.request.query_params.get('address')
        industry = self.request.query_params.get('industry')
        company_scale = self.request.query_params.get('company_scale')
        company_type = self.request.query_params.get('company_type')
        
        # 应用筛选
        if job_title:
            queryset = queryset.filter(job_title__icontains=job_title)
        if company_name:
            queryset = queryset.filter(company_name__icontains=company_name)
        if address:
            queryset = queryset.filter(address__icontains=address)
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        if company_scale:
            queryset = queryset.filter(company_scale=company_scale)
        if company_type:
            queryset = queryset.filter(company_type__icontains=company_type)
        
        # 按更新日期排序
        queryset = queryset.order_by('-update_date')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """获取筛选选项"""
        from django.db.models import Count
        
        # 获取所有城市（从address字段提取）
        addresses = CompanyInfo.objects.values_list('address', flat=True).distinct()
        cities = set()
        for addr in addresses:
            if addr:
                # 提取城市名（格式如 "北京-朝阳区"）
                city = addr.split('-')[0] if '-' in addr else addr
                cities.add(city)
        
        # 获取所有公司规模
        scales = list(CompanyInfo.objects.values_list('company_scale', flat=True)
                      .exclude(company_scale__isnull=True)
                      .exclude(company_scale='')
                      .distinct())
        
        # 获取所有公司类型
        types = list(CompanyInfo.objects.values_list('company_type', flat=True)
                     .exclude(company_type__isnull=True)
                     .exclude(company_type='')
                     .distinct())
        
        # 获取所有行业
        industries = list(CompanyInfo.objects.values_list('industry', flat=True)
                          .exclude(industry__isnull=True)
                          .exclude(industry='')
                          .distinct())
        
        return Response({
            'cities': sorted(list(cities)),
            'scales': scales,
            'types': types,
            'industries': industries
        })
    
    @action(detail=False, methods=['get'])
    def companies(self, request):
        """获取公司列表（去重后）"""
        from django.db.models import Count
        
        # 筛选参数
        job_title = self.request.query_params.get('job_title')
        address = self.request.query_params.get('address')
        industry = self.request.query_params.get('industry')
        company_scale = self.request.query_params.get('company_scale')
        company_type = self.request.query_params.get('company_type')
        
        # 分页参数
        page = int(self.request.query_params.get('page', 1))
        page_size = int(self.request.query_params.get('page_size', 15))
        start = (page - 1) * page_size
        end = start + page_size
        
        queryset = CompanyInfo.objects.all()
        
        # 应用筛选
        if job_title:
            queryset = queryset.filter(job_title__icontains=job_title)
        if address:
            queryset = queryset.filter(address__icontains=address)
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        if company_scale:
            queryset = queryset.filter(company_scale=company_scale)
        if company_type:
            queryset = queryset.filter(company_type__icontains=company_type)
        
        # 按公司名称分组，获取每个公司的职位数量
        companies = queryset.values('company_name', 'company_scale', 'company_type', 'industry', 'company_details').annotate(
            job_count=Count('id')
        ).order_by('-job_count')[start:end]
        
        result = []
        for company in companies:
            # 获取该公司的职位列表
            jobs = CompanyInfo.objects.filter(
                company_name=company['company_name']
            ).values('job_title', 'salary_range', 'address', 'job_source_url')[:5]
            
            result.append({
                'name': company['company_name'],
                'scale': company['company_scale'],
                'type': company['company_type'],
                'industry': company['industry'],
                'description': company['company_details'][:200] if company['company_details'] else '',
                'job_count': company['job_count'],
                'jobs': list(jobs)
            })
        
        return Response(result)


class JobFairViewSet(viewsets.ModelViewSet):
    """湖南高校双选会API"""
    queryset = JobFair.objects.all()
    serializer_class = JobFairSerializer
    pagination_class = StandardPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选参数
        university = self.request.query_params.get('university')
        
        # 应用筛选
        if university:
            queryset = queryset.filter(university=university)
        
        # 按举办时间排序
        queryset = queryset.order_by('-date')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """获取筛选选项"""
        universities = dict(JobFair.UNIVERSITY_CHOICES)
        
        return Response({
            'universities': universities
        })
