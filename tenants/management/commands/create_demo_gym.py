"""
Create demo gym with sample data for advertising/demos.
Creates: gym tenant, activity types, plans, members, attendance.
ONLY CREATES DATA IF NONE EXISTS (unless --reset is passed).
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
        parser.add_argument('--members', type=int, default=120, help='Number of demo members')
        parser.add_argument('--name', type=str, default='FitZone Demo', help='Gym name')
        parser.add_argument('--reset', action='store_true', help='Delete existing data and recreate')

    def handle(self, *args, **options):
        from tenants.models import Gym, Domain
        
        gym_name = options['name']
        num_members = options['members']
        schema_name = 'demo_gym'
        reset = options['reset']
        
        self.stdout.write(f'Creating demo gym: {gym_name}')
        
        # Create or get the demo gym tenant
        with schema_context('public'):
            gym, created = Gym.objects.update_or_create(
                schema_name=schema_name,
                defaults={
                    'name': gym_name,
                    'slug': 'demo_gym',
                    'owner_name': 'Demo Owner',
                    'owner_email': 'demo@fitzone.com',
                    'owner_phone': '+212600000000',
                    'status': 'approved',
                    'subscription_plan': 'pro',
                    'subscription_status': 'active',
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Gym tenant created: {gym_name}'))
            else:
                self.stdout.write(f'Gym tenant already exists')
            
            # Add domain
            Domain.objects.update_or_create(
                domain=f'{schema_name}.gym-backend-production-1547.up.railway.app',
                defaults={'tenant': gym, 'is_primary': True}
            )
        
        # Create demo data within the tenant schema
        with tenant_context(gym):
            # Import models within tenant context
            from gym.models import ActivityType, MembershipPlan
            from members.models import Member
            from attendance.models import Attendance
            from users.models import User
            from subscriptions.models import Payment
            
            # Check if members already exist
            existing_count = Member.objects.count()
            if existing_count > 0 and not reset:
                self.stdout.write(self.style.WARNING(
                    f'Demo data already exists ({existing_count} members). Use --reset to recreate.'
                ))
                return
            
            # If reset, delete existing data
            if reset and existing_count > 0:
                self.stdout.write(self.style.WARNING(f'Deleting {existing_count} existing members...'))
                Attendance.objects.all().delete()
                Payment.objects.all().delete()
                Member.objects.all().delete()
                User.objects.filter(role='MEMBER').delete()
                self.stdout.write(self.style.SUCCESS('Existing data deleted'))
            
            # Create admin user for this tenant
            admin, admin_created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@fitzone.com',
                    'first_name': 'Demo',
                    'last_name': 'Admin',
                    'role': 'ADMIN',
                    'is_staff': True,
                    'is_active': True,
                }
            )
            if admin_created:
                admin.set_password('admin123')
                admin.save()
                self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))
            
            self._create_activity_types(ActivityType)
            self._create_plans(MembershipPlan, ActivityType)
            self._create_members(Member, MembershipPlan, ActivityType, User, num_members)
            self._create_attendance(Attendance, Member)
            self._create_payments(Payment, Member)
        
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
            {'name': 'Monthly', 'duration_days': 30, 'price': 300},
            {'name': 'Quarterly', 'duration_days': 90, 'price': 800},
            {'name': 'Semi-Annual', 'duration_days': 180, 'price': 1500},
            {'name': 'Annual', 'duration_days': 365, 'price': 2800},
        ]
        
        for activity in activities:
            for plan in plans:
                MembershipPlan.objects.update_or_create(
                    name=plan['name'],
                    activity_type=activity,
                    defaults={
                        'duration_days': plan['duration_days'],
                        'price': Decimal(plan['price']),
                        'is_active': True,
                    }
                )
        self.stdout.write(f'  Created {len(plans) * len(activities)} plans')

    def _create_members(self, Member, MembershipPlan, ActivityType, User, num_members):
        self.stdout.write(f'Creating {num_members} demo members...')
        plans = list(MembershipPlan.objects.filter(is_active=True))
        
        # Fixed distribution: ~80% active, ~15% expired, ~5% pending
        active_count = int(num_members * 0.80)
        expired_count = int(num_members * 0.15)
        pending_count = num_members - active_count - expired_count
        
        member_distribution = (
            ['active'] * active_count + 
            ['expired'] * expired_count + 
            ['pending'] * pending_count
        )
        random.shuffle(member_distribution)
        
        for i, status_type in enumerate(member_distribution):
            gender = random.choice(['M', 'F'])
            first_name = random.choice(FIRST_NAMES_M if gender == 'M' else FIRST_NAMES_F)
            last_name = random.choice(LAST_NAMES)
            phone = f'+2126{random.randint(10000000, 99999999)}'
            username = f'member_{i+1:03d}'
            email = f'{first_name.lower()}.{last_name.lower().replace(" ", "")}@demo.com'
            
            # Create user first
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'MEMBER',
                    'is_active': True,
                }
            )
            user.set_password('member123')
            user.save()
            
            plan = random.choice(plans)
            
            if status_type == 'active':
                start_date = timezone.now().date() - timedelta(days=random.randint(1, 30))
                end_date = start_date + timedelta(days=plan.duration_days)
                amount_paid = plan.price
            elif status_type == 'expired':
                end_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
                start_date = end_date - timedelta(days=plan.duration_days)
                amount_paid = plan.price
            else:  # pending
                start_date = None
                end_date = None
                amount_paid = Decimal('0')
            
            # Date of birth (all adults)
            birth_year = random.randint(1980, 2005)
            dob = datetime(birth_year, random.randint(1, 12), random.randint(1, 28)).date()
            
            Member.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                gender=gender,
                age_category='ADULT',
                date_of_birth=dob,
                address=f'{random.randint(1, 100)} Demo Street, Casablanca',
                activity_type=plan.activity_type,
                membership_plan=plan,
                subscription_start=start_date,
                subscription_end=end_date,
                amount_paid=amount_paid,
            )
        
        self.stdout.write(f'  Created {num_members} members')

    def _create_attendance(self, Attendance, Member):
        self.stdout.write('Creating attendance records...')
        # Get active members (those with valid subscription)
        today = timezone.now().date()
        active_members = list(Member.objects.filter(subscription_end__gte=today)[:50])
        
        count = 0
        for member in active_members:
            # Create 3-10 attendance records per member over past 30 days
            num_records = random.randint(3, 10)
            for _ in range(num_records):
                days_ago = random.randint(0, 30)
                check_in = timezone.now() - timedelta(
                    days=days_ago,
                    hours=random.randint(6, 20),
                    minutes=random.randint(0, 59)
                )
                check_out = check_in + timedelta(hours=random.randint(1, 2))
                
                Attendance.objects.get_or_create(
                    member=member,
                    check_in_time=check_in,
                    defaults={'check_out_time': check_out}
                )
                count += 1
        
        self.stdout.write(f'  Created {count} attendance records')

    def _create_payments(self, Payment, Member):
        """Create payment records for members with subscriptions."""
        self.stdout.write('Creating payment records...')
        members_with_subscription = Member.objects.filter(
            subscription_start__isnull=False,
            amount_paid__gt=0
        )
        
        count = 0
        for member in members_with_subscription:
            Payment.objects.get_or_create(
                member=member,
                date=member.subscription_start,
                defaults={
                    'amount': member.amount_paid,
                    'payment_method': random.choice(['cash', 'card', 'transfer']),
                    'notes': f'Subscription payment for {member.membership_plan.name if member.membership_plan else "N/A"}',
                }
            )
            count += 1
        
        self.stdout.write(f'  Created {count} payment records')
