from django.db import models


class CompanyInfo(models.Model):
    id = models.AutoField(primary_key=True)
    job_title = models.CharField(max_length=255, null=True, blank=True, verbose_name='职位名称')
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='地址')
    salary_range = models.CharField(max_length=255, null=True, blank=True, verbose_name='薪资范围')
    company_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='公司名称')
    industry = models.CharField(max_length=255, null=True, blank=True, verbose_name='行业')
    company_scale = models.CharField(max_length=255, null=True, blank=True, verbose_name='公司规模')
    company_type = models.CharField(max_length=255, null=True, blank=True, verbose_name='公司类型')
    job_code = models.CharField(max_length=255, null=True, blank=True, verbose_name='职位代码')
    job_details = models.TextField(null=True, blank=True, verbose_name='职位详情')
    update_date = models.DateTimeField(null=True, blank=True, verbose_name='更新日期')
    company_details = models.TextField(null=True, blank=True, verbose_name='公司详情')
    job_source_url = models.CharField(max_length=500, null=True, blank=True, verbose_name='职位来源URL')
    
    class Meta:
        managed = False
        db_table = 'company_info_backup'
        verbose_name = '公司职位信息'
        verbose_name_plural = '公司职位信息'
    
    def __str__(self):
        return f'{self.company_name} - {self.job_title}'


class Company(models.Model):
    RANKING_CHOICES = [
        ('red', '红榜'),
        ('normal', '普通'),
        ('black', '黑榜'),
    ]
    
    SCALE_CHOICES = [
        ('small', '小型（1-50人）'),
        ('medium', '中型（51-500人）'),
        ('large', '大型（501-2000人）'),
        ('enterprise', '企业级（2000人以上）'),
    ]
    
    NATURE_CHOICES = [
        ('private', '民营企业'),
        ('state', '国有企业'),
        ('foreign', '外资企业'),
        ('joint', '合资企业'),
        ('startup', '创业公司'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='公司名称')
    city = models.CharField(max_length=100, verbose_name='城市')
    scale = models.CharField(max_length=20, choices=SCALE_CHOICES, null=True, blank=True, verbose_name='公司规模')
    nature = models.CharField(max_length=20, choices=NATURE_CHOICES, null=True, blank=True, verbose_name='企业性质')
    ranking = models.CharField(max_length=10, choices=RANKING_CHOICES, default='normal', verbose_name='红黑榜')
    avg_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='平均薪资')
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=1000, blank=True)
    public_profile = models.TextField(blank=True)
    source = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    permission_status = models.CharField(max_length=20, default='pending', choices=[('pending','pending'),('allowed','allowed'),('restricted','restricted')])
    collected_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    dedupe_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    is_demo = models.BooleanField(default=False)
    description = models.TextField(verbose_name='公司描述')
    warning_info = models.TextField(blank=True, verbose_name='警告信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '企业信息'
        verbose_name_plural = '企业信息'
        ordering = ['-ranking', 'name']
    
    def __str__(self):
        return self.name


class Job(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', verbose_name='公司')
    title = models.CharField(max_length=255, verbose_name='职位名称')
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='最低薪资')
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='最高薪资')
    city = models.CharField(max_length=100, blank=True)
    experience = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    skills = models.JSONField(default=list)
    source = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    permission_status = models.CharField(max_length=20, default='pending', choices=[('pending','pending'),('allowed','allowed'),('restricted','restricted')])
    collected_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    dedupe_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    is_demo = models.BooleanField(default=False)
    requirements = models.TextField(verbose_name='职位要求')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '职位信息'
        verbose_name_plural = '职位信息'
    
    def __str__(self):
        return f'{self.company.name} - {self.title}'


class JobFair(models.Model):
    UNIVERSITY_CHOICES = [
        ('hnu', '湖南大学'),
        ('csust', '长沙理工大学'),
        ('hnust', '湖南科技大学'),
        ('hunnu_science', '湖南师范大学'),
        ('csu', '中南大学'),
        ('csuft', '中南林业科技大学'),
        ('hnuc', '湖南城市学院'),
        ('hnctu', '湖南工业大学'),
        ('hunnu', '湖南农业大学'),
        ('hust', '湖南理工学院'),
        ('hnu_medicine', '湖南医药学院'),
        ('hnvtc', '湖南铁道职业技术学院'),
        ('xtu', '湘潭大学'),
        ('usc', '南华大学'),
        ('hutb', '湖南工商大学'),
        ('jsu', '吉首大学'),
        ('hhtc', '怀化学院'),
        ('hnfnu', '湖南第一师范学院'),
        ('hufe', '湖南财政经济学院'),
        ('hnxxy', '湖南信息学院'),
        ('hnyxy', '湖南应用技术学院'),
        ('hnist', '湖南理工学院'),
        ('hynu', '衡阳师范学院'),
        ('huas', '湖南文理学院'),
        ('hnjcxy', '湖南警察学院'),
        ('hngxy', '湖南工学院'),
        ('syxy', '邵阳学院'),
        ('xnu', '湘南学院'),
        ('hnrwkjxy', '湖南人文科技学院'),
        ('hnjtgcxy', '湖南交通工程学院'),
        ('hnrjzy', '湖南软件职业技术大学'),
        ('other', '其他高校'),
    ]
    
    university = models.CharField(max_length=50, choices=UNIVERSITY_CHOICES, verbose_name='高校名称', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name='双选会名称', null=True, blank=True)
    date = models.DateTimeField(verbose_name='举办时间', null=True, blank=True)
    location = models.CharField(max_length=255, verbose_name='举办地点', null=True, blank=True)
    contact_phone = models.CharField(max_length=20, verbose_name='联系电话', null=True, blank=True)
    contact_email = models.EmailField(verbose_name='联系邮箱', null=True, blank=True)
    description = models.TextField(verbose_name='双选会详情', null=True, blank=True)
    registration_link = models.CharField(max_length=500, blank=True, verbose_name='报名链接')
    university_url = models.CharField(max_length=500, blank=True, verbose_name='高校就业网站链接')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '湖南高校双选会'
        verbose_name_plural = '湖南高校双选会'
        ordering = ['-date']
    
    def __str__(self):
        date_str = self.date.strftime("%Y-%m-%d") if self.date else '未设置'
        return f'{self.get_university_display()} - {self.name} ({date_str})'
