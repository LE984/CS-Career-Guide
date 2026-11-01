from django.db import models
from django.conf import settings


def avatar_upload_path(instance, filename):
    return f'avatars/user_{instance.user.id}/{filename}'


class Resume(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resume', verbose_name='用户')
    edit_revision = models.PositiveBigIntegerField(default=0, editable=False)
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True, verbose_name='头像')
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='姓名')
    target_position = models.CharField(max_length=100, null=True, blank=True, verbose_name='意向岗位')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='电话')
    email = models.EmailField(null=True, blank=True, verbose_name='邮箱')
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name='地址')
    self_evaluation = models.TextField(null=True, blank=True, verbose_name='个人自评')
    skills = models.TextField(null=True, blank=True, verbose_name='专业技能')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.edit_revision = models.F('edit_revision') + 1
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'edit_revision'}
        super().save(*args, **kwargs)
        self.refresh_from_db(fields=['edit_revision'])

    class Meta:
        db_table = 'resumes'
        verbose_name = '简历'
        verbose_name_plural = '简历'
    
    def __str__(self):
        return f'{self.user.username}的简历'


class Education(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='education', verbose_name='简历')
    school = models.CharField(max_length=200, verbose_name='学校')
    major = models.CharField(max_length=100, null=True, blank=True, verbose_name='专业')
    period = models.CharField(max_length=50, verbose_name='时间段')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    
    class Meta:
        db_table = 'education'
        verbose_name = '教育背景'
        verbose_name_plural = '教育背景'
    
    def __str__(self):
        return f'{self.school} - {self.major}'


class Experience(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experience', verbose_name='简历')
    company = models.CharField(max_length=200, verbose_name='公司')
    position = models.CharField(max_length=100, verbose_name='职位')
    period = models.CharField(max_length=50, verbose_name='时间段')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    
    class Meta:
        db_table = 'experience'
        verbose_name = '工作经验'
        verbose_name_plural = '工作经验'
    
    def __str__(self):
        return f'{self.company} - {self.position}'


class Project(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects', verbose_name='简历')
    name = models.CharField(max_length=200, verbose_name='项目名称')
    role = models.CharField(max_length=100, verbose_name='担任角色')
    period = models.CharField(max_length=50, verbose_name='时间段')
    url = models.URLField(null=True, blank=True, verbose_name='项目链接')
    description = models.TextField(null=True, blank=True, verbose_name='项目描述')
    
    class Meta:
        db_table = 'projects'
        verbose_name = '项目经验'
        verbose_name_plural = '项目经验'
    
    def __str__(self):
        return self.name


class Certificate(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='certificates', verbose_name='简历')
    name = models.CharField(max_length=200, verbose_name='证书名称')
    issuer = models.CharField(max_length=100, verbose_name='颁发机构')
    period = models.CharField(max_length=50, verbose_name='获得日期')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    
    class Meta:
        db_table = 'certificates'
        verbose_name = '证书认证'
        verbose_name_plural = '证书认证'
    
    def __str__(self):
        return self.name


class Award(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='awards', verbose_name='简历')
    name = models.CharField(max_length=200, verbose_name='奖项名称')
    issuer = models.CharField(max_length=100, verbose_name='颁发机构')
    period = models.CharField(max_length=50, verbose_name='获得日期')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    
    class Meta:
        db_table = 'awards'
        verbose_name = '获奖经历'
        verbose_name_plural = '获奖经历'
    
    def __str__(self):
        return self.name
