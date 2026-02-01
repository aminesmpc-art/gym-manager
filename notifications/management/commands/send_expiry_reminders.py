"""
Django management command to send WhatsApp reminders for expiring memberships.

Usage:
    python manage.py send_expiry_reminders          # 7 days before
    python manage.py send_expiry_reminders --days 3 # 3 days before
    python manage.py send_expiry_reminders --dry-run # Test without sending
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from members.models import Member
from notifications.services import whatsapp_service


class Command(BaseCommand):
    help = 'Send WhatsApp reminders to members with expiring memberships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Send reminders to members expiring within this many days (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=days)
        
        if not whatsapp_service.is_configured:
            self.stderr.write(self.style.ERROR(
                'Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env'
            ))
            return
        
        # Find members expiring within the specified days
        expiring_members = Member.objects.filter(
            subscription_end__gte=today,
            subscription_end__lte=expiry_threshold,
            is_active=True,
            phone__isnull=False
        ).exclude(phone='')
        
        total = expiring_members.count()
        success_count = 0
        fail_count = 0
        
        self.stdout.write(f'Found {total} members with memberships expiring within {days} days')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No messages will be sent'))
        
        for member in expiring_members:
            days_left = (member.subscription_end - today).days
            expiry_date = member.subscription_end.strftime('%B %d, %Y')
            
            self.stdout.write(f'  - {member.full_name} ({member.phone}): expires in {days_left} days')
            
            if not dry_run:
                result = whatsapp_service.send_expiring_reminder(
                    member_name=member.full_name,
                    phone=member.phone,
                    days_left=days_left,
                    expiry_date=expiry_date
                )
                
                if result['success']:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Sent (SID: {result["sid"]})'))
                else:
                    fail_count += 1
                    self.stderr.write(self.style.ERROR(f'    ✗ Failed: {result["error"]}'))
        
        # Summary
        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN complete. Would send {total} messages.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Complete: {success_count} sent, {fail_count} failed'))
