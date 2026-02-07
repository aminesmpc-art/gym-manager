import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from members.models import Member
from members.serializers import MemberSerializer
from django.test import RequestFactory

# Mock request from 127.0.0.1
request = RequestFactory().get('/api/members/1/', HTTP_HOST='127.0.0.1:8000')

try:
    m = Member.objects.get(id=1)
    s = MemberSerializer(m, context={'request': request})
    print(f"PHOTO URL (from 127.0.0.1): {s.data.get('photo')}")
except Member.DoesNotExist:
    print("Member 1 not found")

# Mock request from 10.0.2.2
request2 = RequestFactory().get('/api/members/1/', HTTP_HOST='10.0.2.2:8000')
try:
    s2 = MemberSerializer(m, context={'request': request2})
    print(f"PHOTO URL (from 10.0.2.2): {s2.data.get('photo')}")
except:
    pass
