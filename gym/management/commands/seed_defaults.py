"""
Seed script to create default activities and membership plans only.
"""

from django.core.management.base import BaseCommand
from gym.models import ActivityType, MembershipPlan


class Command(BaseCommand):
    help = 'Creates default activities and membership plans'

    def handle(self, *args, **options):
        # Create default activities
        activities = [
            ('Bodybuilding', 'Weight training and muscle building'),
            ('Cardio', 'Cardiovascular exercises'),
            ('Yoga', 'Yoga and flexibility training'),
            ('Boxing', 'Boxing and martial arts'),
        ]

        self.stdout.write('Creating activities...')
        for name, desc in activities:
            obj, created = ActivityType.objects.get_or_create(
                name=name, 
                defaults={'description': desc}
            )
            status = 'created' if created else 'exists'
            self.stdout.write(f'  {name}: {status}')

        # Create default plans for each activity
        self.stdout.write('\nCreating plans...')
        for activity in ActivityType.objects.all():
            monthly, c1 = MembershipPlan.objects.get_or_create(
                name=f'{activity.name} Monthly',
                defaults={'duration_days': 30, 'price': 250, 'activity_type': activity}
            )
            quarterly, c2 = MembershipPlan.objects.get_or_create(
                name=f'{activity.name} Quarterly', 
                defaults={'duration_days': 90, 'price': 600, 'activity_type': activity}
            )
            yearly, c3 = MembershipPlan.objects.get_or_create(
                name=f'{activity.name} Yearly',
                defaults={'duration_days': 365, 'price': 2000, 'activity_type': activity}
            )
            self.stdout.write(f'  {activity.name}: Monthly, Quarterly, Yearly')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Activities: {ActivityType.objects.count()} | Plans: {MembershipPlan.objects.count()}'
        ))
