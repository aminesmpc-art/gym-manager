import os
import django
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_management.settings')
django.setup()

from members.models import Member
from subscriptions.models import Payment
from attendance.models import Attendance
from gym.models import ActivityType, MembershipPlan, Gym

User = get_user_model()

# Patch ALLOWED_HOSTS for test
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

def run_test():
    print(">>> Setting up test data...")
    
    # Create Staff User
    if not User.objects.filter(username='staff_test').exists():
        staff = User.objects.create_user(username='staff_test', password='password123', role='STAFF')
    else:
        staff = User.objects.get(username='staff_test')
        
    # Create Gym
    gym, _ = Gym.objects.get_or_create(name="Test Gym")
    
    # Create Activity and Plan
    activity, _ = ActivityType.objects.get_or_create(name="Test Activity")
    plan, _ = MembershipPlan.objects.get_or_create(
        name="Test Plan", 
        activity_type=activity,
        duration_days=30,
        price=1000
    )
    
    # Create Member
    member = Member.objects.create(
        user=User.objects.create_user(username=f'member_test_{timezone.now().timestamp()}', role='MEMBER'),
        first_name="Test",
        last_name="Member",
        activity_type=activity,
        membership_plan=plan,
        subscription_end=timezone.now().date() + timedelta(days=10) # Active
    )
    
    # Create Payment
    Payment.objects.create(
        member=member,
        membership_plan=plan,
        amount=1000,
        payment_date=timezone.now().date(),
        period_start=timezone.now().date(),
        period_end=timezone.now().date() + timedelta(days=30),
        created_by=staff
    )
    
    # Create Attendance
    Attendance.objects.create(
        member=member,
        date=timezone.now().date(),
        recorded_by=staff
    )
    
    print(">>> Testing Dashboard API...")
    client = APIClient()
    
    # 1. Unauthenticated -> 401
    response = client.get('/api/reports/dashboard/')
    print(f"Unauthenticated: {response.status_code} (Expected 401)")
    assert response.status_code == 401
    
    # 2. Authenticated Staff -> 200
    client.force_authenticate(user=staff)
    response = client.get('/api/reports/dashboard/')
    print(f"Authenticated (Staff): {response.status_code} (Expected 200)")
    assert response.status_code == 200
    
    data = response.json()
    print("Response Data:", data)
    
    # Verify Structure
    assert 'overview' in data
    assert 'financials' in data
    assert 'activity_breakdown' in data
    
    # Verify Data
    assert data['overview']['active_members'] >= 1
    assert data['overview']['attendance_today'] >= 1
    assert data['financials']['income_today'] >= 1000
    
    print("\n✅ DASHBOARD API VERIFIED SUCCESS")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        exit(1)
