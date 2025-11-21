# sms_utils.py
"""
SMS utilities for sending text messages.
Currently a placeholder - can be extended with Twilio SMS, Vonage, or other SMS providers.
"""

def send_sms(to_phone: str, message: str) -> None:
    """
    Send SMS message to specified phone number.
    
    Current implementation: Placeholder (prints to console)
    Production: Replace with Twilio SMS, Vonage, or other SMS provider
    
    Args:
        to_phone: Recipient phone number
        message: SMS message content
    """
    # For now just print (dev). Replace with Twilio or local SMS API in production.
    print(f"[SMS] To: {to_phone} | Msg: {message}")
    # Example Twilio SMS logic:
    # from twilio.rest import Client
    # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    # client.messages.create(body=message, from_='+1234567890', to=to_phone)
