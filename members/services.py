import logging
# import requests # Uncomment when ready for real API
from django.conf import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Service to handle sending WhatsApp messages.
    Currently stubbed for testing/logging.
    """
    
    @staticmethod
    def send_message(phone_number, message_text):
        """
        Sends a WhatsApp message to the specified phone number.
        
        Args:
            phone_number (str): The recipient's phone number.
            message_text (str): The content of the message.
            
        Returns:
            bool: True if sent successfully (or mocked), False otherwise.
        """
        if not phone_number:
            logger.warning("WhatsAppService: Skipped sending. No phone number provided.")
            return False
            
        try:
            # TODO: Integrate with actual provider (Twilio, Meta, ClickSend, etc.)
            # Example Twilio:
            # client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            # message = client.messages.create(
            #     body=message_text,
            #     from_='whatsapp:+14155238886',
            #     to=f'whatsapp:{phone_number}'
            # )
            
            # For now, we log it as a successful "mock" send
            logger.info(f"WhatsAppService: [MOCK SEND] To: {phone_number} | Body: {message_text}")
            print(f"WhatsApp Mock: Sending to {phone_number}: {message_text}")
            
            return True
            
        except Exception as e:
            logger.error(f"WhatsAppService: Failed to send message to {phone_number}. Error: {e}")
            return False
