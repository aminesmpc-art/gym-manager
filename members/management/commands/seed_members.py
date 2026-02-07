"""
Seed script to create test members with realistic data.
Uses all Member model fields properly.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from members.models import Member
from gym.models import ActivityType, MembershipPlan
from users.models import User
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seeds the database with test members'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of members to create (default: 100)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing seeded members first'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        today = timezone.now().date()
        
        if options['clear']:
            self.stdout.write('Clearing existing seeded members...')
            # Delete members with [SEEDED] in notes
            seeded_members = Member.objects.filter(notes__contains='[SEEDED]')
            user_ids = list(seeded_members.values_list('user_id', flat=True))
            seeded_members.delete()
            User.objects.filter(id__in=user_ids).delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))

        if count == 0:
            return

        self.stdout.write(f'Seeding {count} members...')

        # 1. Ensure Activities exist
        activities_data = [
            ('Bodybuilding', 'Weight training and muscle building'),
            ('Cardio', 'Cardiovascular exercises'),
            ('Yoga', 'Yoga and flexibility training'),
            ('Boxing', 'Boxing and martial arts'),
            ('CrossFit', 'High-intensity functional training'),
        ]
        activities = []
        for name, desc in activities_data:
            obj, _ = ActivityType.objects.get_or_create(
                name=name, 
                defaults={'description': desc}
            )
            activities.append(obj)

        # 2. Ensure Plans exist for each activity
        plans = []
        for activity in activities:
            monthly, _ = MembershipPlan.objects.get_or_create(
                name=f'{activity.name} Monthly',
                defaults={
                    'duration_days': 30,
                    'price': random.randint(200, 350),
                    'activity_type': activity
                }
            )
            quarterly, _ = MembershipPlan.objects.get_or_create(
                name=f'{activity.name} Quarterly',
                defaults={
                    'duration_days': 90,
                    'price': random.randint(500, 800),
                    'activity_type': activity
                }
            )
            yearly, _ = MembershipPlan.objects.get_or_create(
                name=f'{activity.name} Yearly',
                defaults={
                    'duration_days': 365,
                    'price': random.randint(2000, 3000),
                    'activity_type': activity
                }
            )
            plans.extend([monthly, quarterly, yearly])

        # 3. Name pools - Moroccan names
        male_names = ['Ahmed', 'Mohamed', 'Youssef', 'Omar', 'Karim', 'Hassan', 'Ali', 'Ibrahim', 'Khaled', 'Bilal', 'Amine', 'Rachid', 'Samir', 'Mehdi', 'Zakaria', 'Hamza', 'Adil', 'Nabil', 'Ismail', 'Driss']
        female_names = ['Fatima', 'Aya', 'Sarah', 'Khadija', 'Noura', 'Salma', 'Yasmin', 'Mariam', 'Hajar', 'Leila', 'Soukaina', 'Imane', 'Naima', 'Houda', 'Amina', 'Sara', 'Laila', 'Zineb', 'Nadia', 'Ghita']
        last_names = ['Benali', 'Idrissi', 'Alaoui', 'Chraibi', 'Tazi', 'Berrada', 'Fassi', 'Saidi', 'Mansouri', 'Ziani', 'Naciri', 'Bennani', 'El Amrani', 'Bouazza', 'Ouazzani', 'Hajji', 'Regragui', 'Benchekroun', 'El Khayat', 'Mouline']
        cities = ['Casablanca', 'Rabat', 'Fès', 'Marrakech', 'Tanger', 'Agadir', 'Meknès', 'Oujda', 'Kenitra', 'Tétouan']
        addresses = ['Hay Riad', 'Quartier Palmier', 'Centre Ville', 'Hay Mohammadi', 'Maarif', 'Agdal', 'Médina', 'Hassan', 'Souissi', 'Océan']

        created = 0
        for i in range(count):
            # Gender distribution: 55% male, 35% female, 10% children
            rand = random.random()
            if rand < 0.55:
                gender = 'M'
                first_name = random.choice(male_names)
                age_category = 'ADULT'
                birth_year = today.year - random.randint(18, 55)
            elif rand < 0.90:
                gender = 'F'
                first_name = random.choice(female_names)
                age_category = 'ADULT'
                birth_year = today.year - random.randint(18, 50)
            else:
                gender = random.choice(['M', 'F'])
                first_name = random.choice(male_names if gender == 'M' else female_names)
                age_category = 'CHILD'
                birth_year = today.year - random.randint(6, 15)

            last_name = random.choice(last_names)
            
            # Create unique username
            username = f"seed_{first_name.lower()}_{i}"
            
            # Skip if exists
            if User.objects.filter(username=username).exists():
                continue

            # Create user
            user = User.objects.create_user(
                username=username,
                password='test123',
                role='MEMBER',
                email=f"{first_name.lower()}.{last_name.lower()}@example.com" if random.random() > 0.3 else ''
            )

            # Pick random plan
            plan = random.choice(plans)
            
            # Status distribution: 45% active, 15% expiring, 25% expired, 10% suspended, 5% archived
            status_rand = random.random()
            is_archived = False
            
            if status_rand < 0.45:
                # Active - ends in 8-60 days
                sub_start = today - timedelta(days=random.randint(1, 30))
                sub_end = today + timedelta(days=random.randint(8, 60))
                is_active = True
            elif status_rand < 0.60:
                # Expiring soon - ends in 1-7 days
                sub_start = today - timedelta(days=random.randint(20, 30))
                sub_end = today + timedelta(days=random.randint(1, 7))
                is_active = True
            elif status_rand < 0.85:
                # Expired - ended 1-30 days ago
                sub_start = today - timedelta(days=random.randint(31, 90))
                sub_end = today - timedelta(days=random.randint(1, 30))
                is_active = True
            elif status_rand < 0.95:
                # Suspended
                sub_start = today - timedelta(days=random.randint(10, 60))
                sub_end = today + timedelta(days=random.randint(10, 30))
                is_active = False
            else:
                # Archived
                sub_start = today - timedelta(days=random.randint(60, 180))
                sub_end = today - timedelta(days=random.randint(30, 60))
                is_active = False
                is_archived = True

            # Date of birth
            dob = today.replace(
                year=birth_year,
                month=random.randint(1, 12),
                day=random.randint(1, 28)
            )
            
            # Phone numbers
            phone = f"06{random.randint(10000000, 99999999)}"
            whatsapp = phone if random.random() > 0.3 else f"06{random.randint(10000000, 99999999)}"
            
            # CIN for adults only (70% have it)
            cin = ''
            if age_category == 'ADULT' and random.random() > 0.3:
                cin = f"{random.choice(['A', 'B', 'C', 'D', 'BE', 'BK'])}{random.randint(100000, 999999)}"
            
            # Insurance (60% have paid)
            insurance_paid = random.random() > 0.4
            insurance_year = str(today.year) if insurance_paid else ''
            
            # Amount paid (80% paid full, 15% partial, 5% nothing)
            payment_rand = random.random()
            from decimal import Decimal
            if payment_rand < 0.80:
                amount_paid = plan.price
            elif payment_rand < 0.95:
                amount_paid = plan.price * Decimal(str(round(random.uniform(0.3, 0.8), 2)))
            else:
                amount_paid = Decimal('0')

            # Create member
            member = Member.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                place_of_birth=random.choice(cities),
                gender=gender,
                age_category=age_category,
                phone=phone,
                whatsapp=whatsapp,
                email=user.email,
                address=f"{random.randint(1, 200)} {random.choice(addresses)}, {random.choice(cities)}",
                cin=cin,
                member_code=f"GYM{2024}{i:04d}" if random.random() > 0.2 else None,
                insurance_paid=insurance_paid,
                insurance_year=insurance_year,
                amount_paid=amount_paid,
                emergency_contact_name=f"Parent of {first_name}" if age_category == 'CHILD' else random.choice(['Spouse', 'Brother', 'Sister', 'Parent']),
                emergency_contact_phone=f"06{random.randint(10000000, 99999999)}",
                activity_type=plan.activity_type,
                membership_plan=plan,
                subscription_start=sub_start,
                subscription_end=sub_end,
                is_active=is_active,
                is_archived=is_archived,
                archived_at=timezone.now() if is_archived else None,
                notes="[SEEDED] Auto-generated test member"
            )
            
            created += 1
            if created % 25 == 0:
                self.stdout.write(f'  Created {created} members...')

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully seeded {created} members!'))
        
        # Show summary
        total = Member.objects.filter(is_archived=False).count()
        active = Member.objects.filter(is_active=True, is_archived=False, subscription_end__gt=today).count()
        expiring = Member.objects.filter(
            is_active=True,
            is_archived=False,
            subscription_end__gt=today,
            subscription_end__lte=today + timedelta(days=7)
        ).count()
        expired = Member.objects.filter(is_active=True, is_archived=False, subscription_end__lt=today).count()
        suspended = Member.objects.filter(is_active=False, is_archived=False).count()
        archived = Member.objects.filter(is_archived=True).count()

        self.stdout.write(f'\nDatabase Summary:')
        self.stdout.write(f'  Total (non-archived): {total}')
        self.stdout.write(f'  Active: {active}')
        self.stdout.write(f'  Expiring Soon: {expiring}')
        self.stdout.write(f'  Expired: {expired}')
        self.stdout.write(f'  Suspended: {suspended}')
        self.stdout.write(f'  Archived: {archived}')
