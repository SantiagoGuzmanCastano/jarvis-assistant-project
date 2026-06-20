
import base64
from email.message import EmailMessage

import requests


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

    response = requests.post(GOOGLE_SENDEMAIL_URL,headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
