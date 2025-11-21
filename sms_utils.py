# sms_utils.py
def send_sms(to_phone: str, message: str) -> None:
    # For now just print (dev). Replace with Twilio or local SMS API in production.
    print(f"[SMS] To: {to_phone} | Msg: {message}")
    # Example Twilio logic can be added here later
