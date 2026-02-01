"""
Phone Number Verification via WhatsApp OTP.

Provides methods to:
- Generate and send OTP codes via WhatsApp
- Verify OTP codes
- Track verification status
"""

import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from notifications.services import whatsapp_service


class PhoneVerificationService:
    """Service for phone number verification via OTP."""
    
    # OTP settings
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    
    def _generate_otp(self) -> str:
        """Generate a random numeric OTP code."""
        return ''.join(random.choices(string.digits, k=self.OTP_LENGTH))
    
    def _get_cache_key(self, phone: str) -> str:
        """Get cache key for storing OTP."""
        # Normalize phone number
        phone_clean = phone.replace(' ', '').replace('-', '').replace('+', '')
        return f'otp:phone:{phone_clean}'
    
    def _get_attempts_key(self, phone: str) -> str:
        """Get cache key for tracking verification attempts."""
        phone_clean = phone.replace(' ', '').replace('-', '').replace('+', '')
        return f'otp:attempts:{phone_clean}'
    
    def send_otp(self, phone: str, member_name: str = None) -> dict:
        """
        Generate and send OTP code to phone number via WhatsApp.
        
        Args:
            phone: Phone number to verify
            member_name: Optional member name for personalization
        
        Returns:
            dict with 'success', 'message', and optionally 'error'
        """
        if not whatsapp_service.is_configured:
            return {
                'success': False,
                'error': 'WhatsApp service not configured'
            }
        
        # Generate OTP
        otp_code = self._generate_otp()
        
        # Store in cache with expiry
        cache_key = self._get_cache_key(phone)
        cache.set(
            cache_key, 
            otp_code, 
            timeout=self.OTP_EXPIRY_MINUTES * 60
        )
        
        # Reset attempts counter
        attempts_key = self._get_attempts_key(phone)
        cache.set(attempts_key, 0, timeout=self.OTP_EXPIRY_MINUTES * 60)
        
        # Build message
        name_text = f", {member_name}" if member_name else ""
        body = (
            f"🏋️ Anti-Gravité Gym Verification\n\n"
            f"Hello{name_text}!\n\n"
            f"Your verification code is:\n\n"
            f"🔐 {otp_code}\n\n"
            f"This code expires in {self.OTP_EXPIRY_MINUTES} minutes.\n\n"
            f"If you didn't request this, please ignore this message."
        )
        
        # Send via WhatsApp
        result = whatsapp_service.send_message(phone, body)
        
        if result['success']:
            return {
                'success': True,
                'message': f'Verification code sent to {phone}',
                'expires_in_minutes': self.OTP_EXPIRY_MINUTES
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to send verification code')
            }
    
    def verify_otp(self, phone: str, code: str) -> dict:
        """
        Verify OTP code for phone number.
        
        Args:
            phone: Phone number being verified
            code: OTP code entered by user
        
        Returns:
            dict with 'success', 'verified', and optionally 'error'
        """
        cache_key = self._get_cache_key(phone)
        attempts_key = self._get_attempts_key(phone)
        
        # Get stored OTP
        stored_otp = cache.get(cache_key)
        
        if stored_otp is None:
            return {
                'success': False,
                'verified': False,
                'error': 'Verification code expired or not found. Please request a new code.'
            }
        
        # Check attempts
        attempts = cache.get(attempts_key, 0)
        if attempts >= self.MAX_ATTEMPTS:
            # Clear OTP after max attempts
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return {
                'success': False,
                'verified': False,
                'error': 'Too many failed attempts. Please request a new code.'
            }
        
        # Verify code
        if code == stored_otp:
            # Success - clear cache
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return {
                'success': True,
                'verified': True,
                'message': 'Phone number verified successfully!'
            }
        else:
            # Wrong code - increment attempts
            cache.set(attempts_key, attempts + 1, timeout=self.OTP_EXPIRY_MINUTES * 60)
            remaining = self.MAX_ATTEMPTS - attempts - 1
            return {
                'success': False,
                'verified': False,
                'error': f'Invalid code. {remaining} attempts remaining.'
            }
    
    def is_otp_pending(self, phone: str) -> bool:
        """Check if there's a pending OTP for this phone number."""
        cache_key = self._get_cache_key(phone)
        return cache.get(cache_key) is not None


# Singleton instance
phone_verification = PhoneVerificationService()
