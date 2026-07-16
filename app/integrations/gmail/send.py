
import base64
from email.message import EmailMessage

from app.integrations.gmail.client import request_gmail

# --------------SEND---------------


GOOGLE_SENDEMAIL_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

def gmail_send_email_message(access_token: str, recipient_email: str, subject: str, body:str ):

    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    message= EmailMessage()
    message.set_content(body)
    message["To"] = recipient_email
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload = {
        "raw": encoded_message,
    }

    response = request_gmail(
        method="POST",
        url=GOOGLE_SENDEMAIL_URL,
        headers=headers,
        json=payload,
    )
    return response.json()
