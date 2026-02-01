"""
WhatsApp Notification Service using Twilio API.

Provides methods to send WhatsApp messages for:
- Membership expiring reminders
- Payment confirmations
- Welcome messages for new members
"""

from decouple import config
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class WhatsAppService:
    """Service class for sending WhatsApp messages via Twilio."""
    
    def __init__(self):
        self.account_sid = config('TWILIO_ACCOUNT_SID', default='')
        self.auth_token = config('TWILIO_AUTH_TOKEN', default='')
        self.from_number = config('TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Twilio client."""
        if self._client is None and self.account_sid and self.auth_token:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client
    
    @property
    def is_configured(self):
        """Check if Twilio credentials are configured."""
        return bool(self.account_sid and self.auth_token)
    
    def _format_phone(self, phone_number: str) -> str:
        """Format phone number for WhatsApp.
        
        Args:
            phone_number: Phone number (e.g., '0622080217' or '+212622080217')
        
        Returns:
            Formatted WhatsApp number (e.g., 'whatsapp:+212622080217')
        """
        # Remove any existing whatsapp: prefix
        phone = phone_number.replace('whatsapp:', '').strip()
        
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Handle Moroccan numbers
        if phone.startswith('0'):
            phone = '+212' + phone[1:]
        elif phone.startswith('212') and not phone.startswith('+'):
            phone = '+' + phone
        elif not phone.startswith('+'):
            phone = '+212' + phone
        
        return f'whatsapp:{phone}'
    
    def send_message(self, to_phone: str, body: str) -> dict:
        """Send a WhatsApp message.
        
        Args:
            to_phone: Recipient phone number
            body: Message body text
        
        Returns:
            dict with 'success', 'sid', and optionally 'error'
        """
        if not self.is_configured:
            return {'success': False, 'error': 'Twilio credentials not configured'}
        
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                to=self._format_phone(to_phone),
                body=body
            )
            return {
                'success': True,
                'sid': message.sid,
                'status': message.status
            }
        except TwilioRestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_welcome_message(self, member_name: str, phone: str, activity_name: str = None) -> dict:
        """Send welcome message to new member.
        
        Args:
            member_name: Member's full name
            phone: Member's phone number
            activity_name: Optional activity type name
        """
        activity_text = f" for {activity_name}" if activity_name else ""
        body = (
            f"🏋️ Welcome to Anti-Gravité Gym, {member_name}! 🎉\n\n"
            f"Thank you for joining us{activity_text}. "
            f"We're excited to have you as part of our fitness family!\n\n"
            f"📱 Save this number to receive important updates about your membership.\n\n"
            f"See you at the gym! 💪"
        )
        return self.send_message(phone, body)
    
    def send_expiring_reminder(self, member_name: str, phone: str, days_left: int, expiry_date: str) -> dict:
        """Send membership expiring reminder.
        
        Args:
            member_name: Member's full name
            phone: Member's phone number
            days_left: Number of days until expiry
            expiry_date: Formatted expiry date string
        """
        if days_left <= 0:
            urgency = "⚠️ EXPIRED"
            body = (
                f"⚠️ {member_name}, your Anti-Gravité membership has expired!\n\n"
                f"📅 Expired on: {expiry_date}\n\n"
                f"Renew now to continue your fitness journey with us. "
                f"Visit the gym or contact us to renew.\n\n"
                f"We miss seeing you! 💪"
            )
        elif days_left == 1:
            body = (
                f"⏰ {member_name}, your membership expires TOMORROW!\n\n"
                f"📅 Expiry date: {expiry_date}\n\n"
                f"Don't lose your progress - renew before tomorrow to avoid interruption.\n\n"
                f"See you at the gym! 💪"
            )
        elif days_left <= 3:
            body = (
                f"🔔 {member_name}, your membership expires in {days_left} days!\n\n"
                f"📅 Expiry date: {expiry_date}\n\n"
                f"Renew soon to keep your streak going!\n\n"
                f"See you at the gym! 💪"
            )
        else:
            body = (
                f"📋 Reminder: {member_name}, your Anti-Gravité membership expires in {days_left} days.\n\n"
                f"📅 Expiry date: {expiry_date}\n\n"
                f"Visit the gym to renew and continue your fitness journey!\n\n"
                f"Keep up the great work! 💪"
            )
        return self.send_message(phone, body)
    
    def send_payment_confirmation(self, member_name: str, phone: str, amount: float, 
                                   plan_name: str = None, new_expiry: str = None) -> dict:
        """Send payment confirmation message.
        
        Args:
            member_name: Member's full name
            phone: Member's phone number
            amount: Payment amount
            plan_name: Optional plan name
            new_expiry: Optional new expiry date
        """
        plan_text = f" ({plan_name})" if plan_name else ""
        expiry_text = f"\n📅 Valid until: {new_expiry}" if new_expiry else ""
        
        body = (
            f"✅ Payment Confirmed!\n\n"
            f"👤 Member: {member_name}\n"
            f"💰 Amount: {amount:.2f} DH{plan_text}{expiry_text}\n\n"
            f"Thank you for your payment! See you at the gym! 💪"
        )
        return self.send_message(phone, body)
    
    def send_checkin_notification(self, member_name: str, phone: str, time: str) -> dict:
        """Send check-in confirmation message.
        
        Args:
            member_name: Member's full name
            phone: Member's phone number
            time: Check-in time
        """
        body = (
            f"✅ Check-in Confirmed!\n\n"
            f"👤 {member_name}\n"
            f"⏰ Time: {time}\n\n"
            f"Have a great workout! 💪"
        )
        return self.send_message(phone, body)


# Singleton instance
whatsapp_service = WhatsAppService()
