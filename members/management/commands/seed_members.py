
from django.core.management.base import BaseCommand
from django.utils import timezone
from members.models import Member
from gym.models import ActivityType, MembershipPlan
from users.models import User
import random
from datetime import timedelta
import string

class Command(BaseCommand):
    help = 'Seeds the database with 300 members'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Ensure Activities exist
        activities = ['Bodybuilding', 'Cardio', 'CrossFit', 'Yoga', 'Boxing']
        activity_objs = []
        for name in activities:
            obj, _ = ActivityType.objects.get_or_create(name=name, defaults={'description': f'{name} classes'})
            activity_objs.append(obj)
        
        # 2. Ensure Plans exist
        plans_data = [
            ('Monthly Standard', 30, 3000),
            ('Monthly Premium', 30, 5000),
            ('Quarterly', 90, 8000),
            ('Yearly', 365, 25000),
        ]
        plan_objs = []
        for name, duration, price in plans_data:
            # Assign random activity type for the plan default
            act = random.choice(activity_objs)
            obj, _ = MembershipPlan.objects.get_or_create(
                name=name, 
                defaults={
                    'duration_days': duration, 
                    'price': price,
                    'activity_type': act
                }
            )
            plan_objs.append(obj)

        # 3. Create Members
        first_names_male = ['Ahmed', 'Mohamed', 'Youssef', 'Omar', 'Karim', 'Hassan', 'Ali', 'Ibrahim', 'Khaled', 'Bilal']
        first_names_female = ['Fatima', 'Aya', 'Sarah', 'Khadija', 'Noura', 'Salma', 'Yasmin', 'Mariam', 'Hajar', 'Leila']
        last_names = ['Benali', 'Idrissi', 'Alaoui', 'Chraibi', 'Tazi', 'Berrada', 'Fassi', 'Saidi', 'Mansocuri', 'Ziani']

        count = 0
        target = 300
        
        while count < target:
            # Gender and Names
            gender = random.choice(['M', 'F'])
            if gender == 'M':
                fname = random.choice(first_names_male)
            else:
                fname = random.choice(first_names_female)
            lname = random.choice(last_names)
            
            # Age Category (20% kids)
            if random.random() < 0.2:
                age_category = 'CHILD'
                birth_year = timezone.now().year - random.randint(5, 12)
            else:
                age_category = 'ADULT'
                birth_year = timezone.now().year - random.randint(18, 50)
            
            dob = timezone.now().replace(year=birth_year, month=random.randint(1, 12), day=random.randint(1, 28)).date()

            # Create User for member
            username = f"{fname.lower()}{lname.lower()}{random.randint(1000, 9999)}"
            # Check if user exists
            if User.objects.filter(username=username).exists():
                continue
                
            user = User.objects.create_user(username=username, password='password123', role='MEMBER')

            # Status determination
            # 50% Active, 30% Expired, 10% Expiring Soon, 10% Suspended
            rand_status = random.random()
            
            is_active = True
            sub_start = timezone.now().date() - timedelta(days=random.randint(1, 60))
            sub_end = sub_start + timedelta(days=30) # Default monthly

            if rand_status < 0.5:
                # Active (Valid end date in future > 7 days)
                sub_end = timezone.now().date() + timedelta(days=random.randint(8, 60))
            elif rand_status < 0.6:
                # Expiring Soon (Active, end date in 1-7 days)
                sub_end = timezone.now().date() + timedelta(days=random.randint(1, 7))
            elif rand_status < 0.9:
                # Expired (End date in past)
                sub_end = timezone.now().date() - timedelta(days=random.randint(1, 30))
            else:
                # Suspended
                is_active = False
                sub_end = timezone.now().date() + timedelta(days=random.randint(10, 30))

            plan = random.choice(plan_objs)
            
            member = Member.objects.create(
                user=user,
                first_name=fname,
                last_name=lname,
                date_of_birth=dob,
                gender=gender,
                age_category=age_category,
                phone=f"06{random.randint(10000000, 99999999)}",
                emergency_contact_name=f"Parent of {fname}" if age_category == 'CHILD' else "Spouse",
                emergency_contact_phone=f"06{random.randint(10000000, 99999999)}",
                activity_type=plan.activity_type,
                membership_plan=plan,
                subscription_start=sub_start,
                subscription_end=sub_end,
                is_active=is_active,
                notes="Auto-generated member"
            )

            # Create Payment for the subscription
            # Only if subscription exists (it does for all right now)
            if plan.price > 0:
                from subscriptions.models import Payment
                Payment.objects.create(
                    member=member,
                    membership_plan=plan,
                    amount=plan.price,
                    payment_date=sub_start,
                    period_start=sub_start,
                    period_end=sub_end,
                    payment_method=random.choice(['CASH', 'CARD', 'TRANSFER']),
                    created_by=user, # Ideally staff, but using member user for simplicity
                    notes="Auto-generated payment"
                )
            count += 1
            if count % 50 == 0:
                self.stdout.write(f'Created {count} members...')

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} members!'))
