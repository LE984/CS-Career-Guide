from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        # 返回默认头像
        if request:
            return request.build_absolute_uri('/media/avatars/default/default.jpg')
        return '/media/avatars/default/default.jpg'
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'avatar',
            'name', 'gender',
            'school', 'major', 'grade', 'education',
            'github', 'profile', 'address',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    def validate_gender(self, value):
        # 兼容旧版前端的空字符串，不再把它作为独立性别值存储。
        return None if value == '' else value

    class Meta:
        model = User
        fields = [
            'email', 'avatar', 'name', 'gender',
            'school', 'major', 'grade', 'education',
            'github', 'profile', 'address',
            'skills', 'other_skills', 'self_introduction', 'career_goal'
        ]

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("新密码和确认密码不匹配")
        return data

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("密码和确认密码不匹配")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        # 如果没有提供 email，设置为空字符串
        if not validated_data.get('email'):
            validated_data['email'] = ''
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("用户名或密码错误")
        return user
