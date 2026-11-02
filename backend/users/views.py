from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from django.contrib.auth import authenticate
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UserProfileUpdateSerializer, ChangePasswordSerializer
)
from .models import User

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                user.refresh_from_db()
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'user': UserSerializer(user).data,
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request):
        """获取当前用户信息"""
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request):
        """更新用户信息"""
        serializer = UserProfileUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            # 刷新用户对象以获取最新数据
            request.user.refresh_from_db()
            return Response(UserSerializer(request.user, context={'request': request}).data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """上传头像"""
        if 'avatar' not in request.FILES:
            return Response({'error': '请选择要上传的头像'}, status=status.HTTP_400_BAD_REQUEST)
        
        avatar = request.FILES['avatar']
        
        # 验证文件类型
        if not avatar.content_type.startswith('image/'):
            return Response({'error': '只支持图片文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            request.user.avatar = avatar
            request.user.save()
            # 刷新用户对象以获取最新数据
            request.user.refresh_from_db()
            return Response(UserSerializer(request.user, context={'request': request}).data)
        except Exception as e:
            return Response({'error': '头像上传失败，请重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # 验证旧密码
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': ['旧密码不正确']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 设置新密码
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({'message': '密码修改成功'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
