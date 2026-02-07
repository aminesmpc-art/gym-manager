"""
Create demo gym with sample data for advertising/demos.
Creates: gym tenant, activity types, plans, members, attendance.
"""
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import schema_context, tenant_context


FIRST_NAMES_M = ['Ahmed', 'Mohamed', 'Youssef', 'Omar', 'Ali', 'Hassan', 'Karim', 'Samir', 'Rachid', 'Nabil',
                 'Khalid', 'Amine', 'Bilal', 'Hamza', 'Zakaria', 'Mehdi', 'Reda', 'Soufiane', 'Ayoub', 'Othmane']
FIRST_NAMES_F = ['Fatima', 'Aicha', 'Khadija', 'Meryem', 'Salma', 'Nadia', 'Laila', 'Sara', 'Yasmine', 'Amina',
                 'Houda', 'Zineb', 'Imane', 'Sanaa', 'Hiba', 'Ghita', 'Souad', 'Nawal', 'Samira', 'Hafsa']
LAST_NAMES = ['Benali', 'El Amrani', 'Bouazza', 'Chakir', 'Dahbi', 'El Fassi', 'Ghali', 'Hajji', 'Idrissi', 'Jabri',
              'Karimi', 'Lahlou', 'Mansouri', 'Naciri', 'Ouazzani', 'Qadiri', 'Rami', 'Salhi', 'Tazi', 'Ziani']


class Command(BaseCommand):
    help = 'Create demo gym with sample data for advertising'

    def add_arguments(self, parser):
        parser.add_argument('--members', type=int, default=100, help='Number of demo members')
        parser.add_argument('--name', type=str, default='FitZone Demo', help='Gym name')

    def handle(self, *args, **options):
        from tenants.models import Gym, Domain
        from gym.models import ActivityType
        from subscriptions.models import MembershipPlan
        from members.models import Member, Subscription
        from attendance.models import Attendance
        
        gym_name = options['name']
        num_members = options['members']
        schema_name = 'demo_gym'
        
        self.stdout.write(f'Creating demo gym: {gym_name}')
        
        # Create or get the demo gym tenant
        with schema_context('public'):
            gym, created = Gym.objects.update_or_create(
                schema_name=schema_name,
                defaults={
                    'name': gym_name,
                    'owner_name': 'Demo Owner',
                    'owner_email': 'demo@fitzone.com',
                    'phone': '+212600000000',
                    'address': '123 Demo Street, Casablanca',
                    'status': 'APPROVED',
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Gym tenant created: {gym_name}'))
            else:
                self.stdout.write(f'Gym tenant already exists, updating...')
            
            # Add domain
            Domain.objects.update_or_create(
                domain=f'{schema_name}.gym-backend-production-1547.up.railway.app',
                defaults={'tenant': gym, 'is_primary': True}
            )
        
        # Create demo data within the tenant schema
        with tenant_context(gym):
            self._create_activity_types(ActivityType)
            self._create_plans(MembershipPlan, ActivityType)
            self._create_members(Member, Subscription, MembershipPlan, ActivityType, num_members)
            self._create_attendance(Attendance, Member)
        
        self.stdout.write(self.style.SUCCESS(f'Demo gym "{gym_name}" created with {num_members} members!'))

    def _create_activity_types(self, ActivityType):
        self.stdout.write('Creating activity types...')
        activities = [
            {'name': 'Fitness', 'description': 'Gym & Weights', 'color': '#FF6B6B'},
            {'name': 'Swimming', 'description': 'Pool access', 'color': '#4ECDC4'},
            {'name': 'Yoga', 'description': 'Yoga classes', 'color': '#9B59B6'},
            {'name': 'Boxing', 'description': 'Boxing training', 'color': '#E74C3C'},
            {'name': 'CrossFit', 'description': 'High intensity', 'color': '#F39C12'},
        ]
        for act in activities:
            ActivityType.objects.update_or_create(name=act['name'], defaults=act)
        self.stdout.write(f'  Created {len(activities)} activity types')

    def _create_plans(self, MembershipPlan, ActivityType):
        self.stdout.write('Creating membership plans...')
        activities = list(ActivityType.objects.all())
        
        plans = [
            {'name': 'Monthly Basic', 'duration_months': 1, 'price': 300},
            {'name': 'Quarterly', 'duration_months': 3, 'price': 800},
            {'name': 'Semi-Annual', 'duration_months': 6, 'price': 1500},
            {'name': 'Annual Premium', 'duration_months': 12, 'price': 2800},
        ]
        
        for activity in activities:
            for plan in plans:
                MembershipPlan.objects.update_or_create(
                    name=f"{plan['name']} - {activity.name}",
                    activity_type=activity,
                    defaults={
                        'duration_months': plan['duration_months'],
                        'price': Decimal(plan['price']),
                        'is_active': True,
                    }
                )
        self.stdout.write(f'  Created {len(plans) * len(activities)} plans')

    def _create_members(self, Member, Subscription, MembershipPlan, ActivityType, num_members):
        self.stdout.write(f'Creating {num_members} demo members...')
        plans = list(MembershipPlan.objects.filter(is_active=True))
        
        for i in range(num_members):
            gender = random.choice(['M', 'F'])
            first_name = random.choice(FIRST_NAMES_M if gender == 'M' else FIRST_NAMES_F)
            last_name = random.choice(LAST_NAMES)
            
            # Random join date in the past year
            days_ago = random.randint(1, 365)
            join_date = timezone.now().date() - timedelta(days=days_ago)
            
            member, created = Member.objects.update_or_create(
                phone=f'+2126{random.randint(10000000, 99999999)}',
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{first_name.lower()}.{last_name.lower().replace(" ", "")}@demo.com',
                    'gender': gender,
                    'date_of_birth': datetime(random.randint(1980, 2005), random.randint(1, 12), random.randint(1, 28)).date(),
                    'address': f'{random.randint(1, 100)} Demo Street',
                    'emergency_contact': f'+2126{random.randint(10000000, 99999999)}',
                    'notes': '',
                }
            )
            
            if created:
                # Create subscription for new members
                plan = random.choice(plans)
                status = random.choices(
                    ['ACTIVE', 'EXPIRED', 'PENDING'],
                    weights=[70, 20, 10]  # 70% active, 20% expired, 10% pending
                )[0]
                
                if status == 'ACTIVE':
                    start_date = timezone.now().date() - timedelta(days=random.randint(1, 30))
                    end_date = start_date + timedelta(days=plan.duration_months * 30)
                elif status == 'EXPIRED':
                    end_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
                    start_date = end_date - timedelta(days=plan.duration_months * 30)
                else:  # PENDING
                    start_date = timezone.now().date()
                    end_date = start_date + timedelta(days=plan.duration_months * 30)
                
                Subscription.objects.create(
                    member=member,
                    plan=plan,
                    start_date=start_date,
                    end_date=end_date,
                    amount_paid=plan.price if status != 'PENDING' else Decimal('0'),
                    status=status,
                )
        
        self.stdout.write(f'  Created {num_members} members with subscriptions')

    def _create_attendance(self, Attendance, Member):
        self.stdout.write('Creating attendance records...')
        members = list(Member.objects.all()[:50])  # Use first 50 members
        
        count = 0
        for member in members:
            # Create 5-15 attendance records per member in the past month
            num_records = random.randint(5, 15)
            for _ in range(num_records):
                days_ago = random.randint(0, 30)
                check_in = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(6, 20),
                    minutes=random.randint(0, 59)
                )
                check_out = check_in + timedelta(hours=random.randint(1, 3))
                
                Attendance.objects.get_or_create(
                    member=member,
                    check_in_time=check_in,
                    defaults={'check_out_time': check_out}
                )
                count += 1
        
        self.stdout.write(f'  Created ~{count} attendance records')
