import html
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

try:
    import requests
except ImportError:
    requests = None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Notification(ABC):
    @abstractmethod
    def send(self, message: str) -> str:
        pass

    @abstractmethod
    def channel_name(self) -> str:
        pass


class EmailNotification(Notification):
    def __init__(self, recipient: str):
        self.recipient = recipient.strip()

    @staticmethod
    def _grades_to_html(message: str) -> str:
        return (
            "<html><body>"
            "<div style=\"font-family:Arial,Helvetica,sans-serif;line-height:1.5;\">"
            f"{html.escape(message).replace(chr(10), '<br>')}"
            "</div></body></html>"
        )

    def send(self, message: str) -> str:
        api_key = os.getenv("BREVO_API_KEY", "").strip()
        sender_email = os.getenv("BREVO_SENDER_EMAIL", "").strip()
        sender_name = os.getenv("BREVO_SENDER_NAME", "Activity 1 Notification App").strip()
        if not api_key:
            raise RuntimeError("BREVO_API_KEY is not configured.")
        if not sender_email:
            raise RuntimeError("BREVO_SENDER_EMAIL is not configured.")
        if not self.recipient:
            raise RuntimeError("Email recipient is required. Enter it in the application.")
        payload = {"sender": {"name": sender_name, "email": sender_email}, "to": [{"email": self.recipient}], "subject": "CSPC 103 Notification", "textContent": message, "htmlContent": self._grades_to_html(message)}
        request = Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode("utf-8"), headers={"accept": "application/json", "api-key": api_key, "content-type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Brevo API error ({exc.code}): {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not connect to Brevo: {exc.reason}") from exc
        message_id = result.get("messageId", "unknown")
        line = f"EMAIL -> {message} | Brevo messageId: {message_id}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "Email (Brevo)"


class SMSNotification(Notification):
    def __init__(self, recipient: str):
        self.recipient = recipient.strip()

    def send(self, message: str) -> str:
        if requests is None:
            raise RuntimeError("requests is not installed. Run: pip install -r requirements.txt")
        api_token = os.getenv("PHILSMS_API_TOKEN", "").strip()
        sender_id = os.getenv("PHILSMS_SENDER_ID", "").strip()
        if not api_token:
            raise RuntimeError("PHILSMS_API_TOKEN is not configured.")
        if not sender_id:
            raise RuntimeError("PHILSMS_SENDER_ID is not configured.")
        if not self.recipient:
            raise RuntimeError("SMS recipient is required. Enter an international phone number such as +639171234567.")
        payload = {"recipient": self.recipient, "sender_id": sender_id, "type": "plain", "message": message}
        try:
            response = requests.post("https://app.philsms.com/api/v3/sms/send", json=payload, headers={"Authorization": f"Bearer {api_token}", "Accept": "application/json", "Content-Type": "application/json"}, timeout=30)
        except requests.RequestException as exc:
            raise RuntimeError(f"Could not connect to PhilSMS: {exc}") from exc
        if not response.ok:
            raise RuntimeError(f"PhilSMS API error ({response.status_code}): {response.text.strip()}")
        try:
            result = response.json()
        except ValueError:
            result = {"response": response.text.strip()}
        reference = result.get("message_id", result.get("id", result.get("data", "accepted")))
        line = f"SMS -> {message} | PhilSMS: {reference} | Recipient: {self.recipient}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "SMS (PhilSMS)"


class PushNotification(Notification):
    def __init__(self, recipient: str = ""):
        self.recipient = recipient.strip()

    def send(self, message: str) -> str:
        line = f"PUSH -> {message} [Push]"
        print(line)
        return line

    def channel_name(self) -> str:
        return "Push"


class WhatsAppNotification(Notification):
    def __init__(self, recipient: str):
        self.recipient = recipient.strip()

    def send(self, message: str) -> str:
        line = f"WHATSAPP -> {message} | Recipient: {self.recipient}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "WhatsApp"


class NotificationService(ABC):
    def __init__(self):
        self.recipient = ""

    def set_recipient(self, recipient: str) -> None:
        self.recipient = recipient.strip()

    @abstractmethod
    def create_notification(self) -> Notification:
        pass

    def notify(self, message: str) -> str:
        if not message.strip():
            raise ValueError("Message must not be empty.")
        notification = self.create_notification()
        return notification.send(message)


class EmailService(NotificationService):
    def create_notification(self) -> Notification:
        return EmailNotification(self.recipient)


class SMSService(NotificationService):
    def create_notification(self) -> Notification:
        return SMSNotification(self.recipient)


class PushService(NotificationService):
    def create_notification(self) -> Notification:
        return PushNotification(self.recipient)


class WhatsAppService(NotificationService):
    def create_notification(self) -> Notification:
        return WhatsAppNotification(self.recipient)


SERVICES: dict[str, type[NotificationService]] = {"Email": EmailService, "SMS": SMSService, "Push": PushService, "WhatsApp": WhatsAppService}
