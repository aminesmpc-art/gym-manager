"""
Django signals for automatic WhatsApp notifications.

Sends notifications when:
- New member is created (welcome message)
- Payment is recorded (confirmation)
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from members.models import Member
from subscriptions.models import Payment
from notifications.services import whatsapp_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Member)
def send_welcome_message(sender, instance, created, **kwargs):
    """Send welcome WhatsApp message when a new member is created."""
    if created and instance.phone:
        try:
            activity_name = instance.activity_type.name if instance.activity_type else None
            result = whatsapp_service.send_welcome_message(
                member_name=instance.full_name,
                phone=instance.phone,
                activity_name=activity_name
            )
            if result['success']:
                logger.info(f"Welcome message sent to {instance.full_name} (SID: {result['sid']})")
            else:
                logger.warning(f"Failed to send welcome message to {instance.full_name}: {result['error']}")
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")


@receiver(post_save, sender=Payment)
def send_payment_confirmation(sender, instance, created, **kwargs):
    """Send payment confirmation WhatsApp message."""
    if created and instance.member and instance.member.phone:
        try:
            member = instance.member
            plan_name = instance.plan.name if instance.plan else None
            new_expiry = member.subscription_end.strftime('%B %d, %Y') if member.subscription_end else None
            
            result = whatsapp_service.send_payment_confirmation(
                member_name=member.full_name,
                phone=member.phone,
                amount=float(instance.amount),
                plan_name=plan_name,
                new_expiry=new_expiry
            )
            if result['success']:
                logger.info(f"Payment confirmation sent to {member.full_name} (SID: {result['sid']})")
            else:
                logger.warning(f"Failed to send payment confirmation to {member.full_name}: {result['error']}")
        except Exception as e:
            logger.error(f"Error sending payment confirmation: {e}")
