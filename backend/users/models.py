from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    GENDER_CHOICES = [('男', '男'), ('女', '女')]

    # 基本信息
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='名字')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True, verbose_name='性别')
    profile = models.TextField(null=True, blank=True, verbose_name='简介')
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', null=True, blank=True, verbose_name='头像')
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name='地址')
    
    # 教育信息
    school = models.CharField(max_length=100, null=True, blank=True, verbose_name='学校')
    major = models.CharField(max_length=100, null=True, blank=True, verbose_name='专业')
    grade = models.CharField(max_length=50, null=True, blank=True, verbose_name='年级')
    education = models.CharField(max_length=50, null=True, blank=True, verbose_name='学历')
    
    # 自我介绍信息
    skills = models.TextField(null=True, blank=True, verbose_name='技能')
    other_skills = models.TextField(null=True, blank=True, verbose_name='其他技能')
    self_introduction = models.TextField(null=True, blank=True, verbose_name='条件自述')
    career_goal = models.TextField(null=True, blank=True, verbose_name='职业期望')
    
    # 社交链接
    github = models.URLField(null=True, blank=True, verbose_name='GitHub')
    
    class Meta:
        db_table = 'users'
        constraints = [
            models.CheckConstraint(
                check=models.Q(gender__in=['男', '女']) | models.Q(gender__isnull=True),
                name='users_gender_valid_or_null',
            ),
        ]
        verbose_name = '用户'
        verbose_name_plural = '用户'
