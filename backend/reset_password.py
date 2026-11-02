import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cs_career_guide.settings')

import django
django.setup()

from django.contrib.auth.hashers import make_password
from users.models import User

username = os.getenv('RESET_PASSWORD_USERNAME')
new_password = os.getenv('RESET_PASSWORD_PASSWORD')
if not username or not new_password:
    raise ValueError('Set RESET_PASSWORD_USERNAME and RESET_PASSWORD_PASSWORD')

try:
    user = User.objects.get(username=username)
    user.password = make_password(new_password)
    user.save()
    print(f'Password updated for {username}')
except User.DoesNotExist:
    print(f'❌ 用户 {username} 不存在')