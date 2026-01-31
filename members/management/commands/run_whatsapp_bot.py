from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from members.models import Member, NotificationLog
from members.services import WhatsAppService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the daily WhatsApp notification bot for expiring/expired subscriptions.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting WhatsApp Notification Bot...'))
        
        today = timezone.now().date()
        target_reminder_date = today + timedelta(days=3)
        
        counts = {
            'reminder_sent': 0,
            'reminder_skipped': 0,
            'expired_sent': 0,
            'expired_skipped': 0,
            'failed': 0,
            'missing_phone': 0,
        }
        
        # 1. 3-Day Reminders
        # Query: Active members whose subscription ends in exactly 3 days
        reminders = Member.objects.filter(
            is_active=True,
            subscription_end=target_reminder_date
        )
        
        self.stdout.write(f"Found {reminders.count()} potential 3-day reminders.")
        
        for member in reminders:
            if not member.phone:
                counts['missing_phone'] += 1
                continue
                
            # Anti-duplicate check
            already_sent = NotificationLog.objects.filter(
                member=member,
                notification_type=NotificationLog.NotificationType.REMINDER_3_DAYS,
                subscription_end_date=member.subscription_end
            ).exists()
            
            if already_sent:
                counts['reminder_skipped'] += 1
                continue
            
            # Send Message
            msg = (
                f"Hi {member.first_name}, your subscription will expire in 3 days on "
                f"{member.subscription_end.strftime('%Y-%m-%d')}. "
                f"Please renew to keep access."
            )
            
            if WhatsAppService.send_message(member.phone, msg):
                NotificationLog.objects.create(
                    member=member,
                    notification_type=NotificationLog.NotificationType.REMINDER_3_DAYS,
                    subscription_end_date=member.subscription_end,
                    status='SENT'
                )
                counts['reminder_sent'] += 1
                self.stdout.write(f"Sent reminder to {member.full_name}")
            else:
                counts['failed'] += 1
        
        # 2. Expired & Unpaid Notifications
        # Query: Members whose subscription has ended (before today)
        # We assume if subscription_end < today, they are unpaid effectively (or haven't renewed)
        # We iterate to find those who haven't received an EXPIRED notice for this specific end date.
        expired_members = Member.objects.filter(
            is_active=True, # Account is active (not banned), but sub is expired
            subscription_end__lt=today
        )
        
        self.stdout.write(f"Found {expired_members.count()} expired members to check.")
        
        for member in expired_members:
            if not member.phone:
                counts['missing_phone'] += 1
                continue
            
            # Anti-duplicate check
            already_sent = NotificationLog.objects.filter(
                member=member,
                notification_type=NotificationLog.NotificationType.EXPIRED_UNPAID,
                subscription_end_date=member.subscription_end
            ).exists()
            
            if already_sent:
                counts['expired_skipped'] += 1
                continue
            
            # Send Message
            msg = (
                f"Hi {member.first_name}, your subscription ended on "
                f"{member.subscription_end.strftime('%Y-%m-%d')} and hasn't been renewed. "
                f"Please pay to reactivate your membership."
            )
            
            if WhatsAppService.send_message(member.phone, msg):
                NotificationLog.objects.create(
                    member=member,
                    notification_type=NotificationLog.NotificationType.EXPIRED_UNPAID,
                    subscription_end_date=member.subscription_end,
                    status='SENT'
                )
                counts['expired_sent'] += 1
                self.stdout.write(f"Sent expired alert to {member.full_name}")
            else:
                counts['failed'] += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Stats: {counts}"))
