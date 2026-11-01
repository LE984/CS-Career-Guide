from rest_framework import serializers
from django.db import transaction
from .models import Resume, Education, Experience, Project, Certificate, Award


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'school', 'major', 'period', 'description']
    
    def create(self, validated_data):
        validated_data.pop('sort', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('sort', None)
        return super().update(instance, validated_data)


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'company', 'position', 'period', 'description']
    
    def create(self, validated_data):
        validated_data.pop('sort', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('sort', None)
        return super().update(instance, validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'role', 'period', 'url', 'description']
    
    def create(self, validated_data):
        validated_data.pop('sort', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('sort', None)
        return super().update(instance, validated_data)


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'name', 'issuer', 'period', 'description']
    
    def create(self, validated_data):
        validated_data.pop('sort', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('sort', None)
        return super().update(instance, validated_data)


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = ['id', 'name', 'issuer', 'period', 'description']
    
    def create(self, validated_data):
        validated_data.pop('sort', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('sort', None)
        return super().update(instance, validated_data)


class ResumeSerializer(serializers.ModelSerializer):
    education = EducationSerializer(many=True, required=False)
    experience = ExperienceSerializer(many=True, required=False)
    projects = ProjectSerializer(many=True, required=False)
    certificates = CertificateSerializer(many=True, required=False)
    awards = AwardSerializer(many=True, required=False)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'edit_revision', 'avatar', 'avatar_url', 'name', 'target_position', 'phone', 'email', 'address',
            'self_evaluation', 'skills', 'education', 'experience', 'projects', 'certificates', 'awards',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'avatar_url']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def create(self, validated_data):
        # 移除前端发送的avatar_url字段，因为它是由后端生成的
        validated_data.pop('avatar_url', None)
        
        education_data = validated_data.pop('education', [])
        experience_data = validated_data.pop('experience', [])
        projects_data = validated_data.pop('projects', [])
        certificates_data = validated_data.pop('certificates', [])
        awards_data = validated_data.pop('awards', [])
        
        resume = Resume.objects.create(**validated_data)
        
        for edu in education_data:
            Education.objects.create(resume=resume, **edu)
        
        for exp in experience_data:
            Experience.objects.create(resume=resume, **exp)
        
        for project in projects_data:
            Project.objects.create(resume=resume, **project)
        
        for certificate in certificates_data:
            Certificate.objects.create(resume=resume, **certificate)
        
        for award in awards_data:
            Award.objects.create(resume=resume, **award)
        
        return resume
    
    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Resume.objects.select_for_update().get(pk=instance.pk)
        # 移除前端发送的avatar_url字段，因为它是由后端生成的
        validated_data.pop('avatar_url', None)
        
        education_data = validated_data.pop('education', None)
        experience_data = validated_data.pop('experience', None)
        projects_data = validated_data.pop('projects', None)
        certificates_data = validated_data.pop('certificates', None)
        awards_data = validated_data.pop('awards', None)
        
        # 更新基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新教育背景
        if education_data is not None:
            instance.education.all().delete()
            for edu in education_data:
                Education.objects.create(resume=instance, **edu)
        
        # 更新工作经验
        if experience_data is not None:
            instance.experience.all().delete()
            for exp in experience_data:
                Experience.objects.create(resume=instance, **exp)
        
        # 更新项目经验
        if projects_data is not None:
            instance.projects.all().delete()
            for project in projects_data:
                Project.objects.create(resume=instance, **project)
        
        # 更新证书认证
        if certificates_data is not None:
            instance.certificates.all().delete()
            for certificate in certificates_data:
                Certificate.objects.create(resume=instance, **certificate)
        
        # 更新获奖经历
        if awards_data is not None:
            instance.awards.all().delete()
            for award in awards_data:
                Award.objects.create(resume=instance, **award)
        
        return instance
