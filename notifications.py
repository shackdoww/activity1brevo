from abc import ABC, abstractmethod
import base64
import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None

BASE_DIR = Path(__file__).resolve().parent


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

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": self.recipient}],
            "subject": "CSPC 103 Notification",
            "textContent": message,
            "htmlContent": self._grades_to_html(message),
        }
        request = Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            method="POST",
        )

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

        api_secret = os.getenv("UNISMS_API_SECRET", "").strip()
        sender_id = os.getenv("UNISMS_SENDER_ID", "").strip()

        if not api_secret:
            raise RuntimeError("UNISMS_API_SECRET is not configured.")
        if not sender_id:
            raise RuntimeError("UNISMS_SENDER_ID is not configured.")
        if not self.recipient:
            raise RuntimeError("SMS recipient is required. Enter an international phone number such as +639171234567.")

        payload = {
            "recipient": self.recipient,
            "content": message,
            "sender_id": sender_id,
        }

        try:
            response = requests.post(
                "https://unismsapi.com/api/sms",
                json=payload,
                auth=(api_secret, ""),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0 Safari/537.36",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Could not connect to UniSMS: {exc}") from exc

        if not response.ok:
            details = response.text.strip()
            if response.status_code == 403 and "cloudflare" in details.lower():
                raise RuntimeError(
                    "UniSMS blocked this request with Cloudflare (403). The API credentials were not rejected. "
                    "Try again later or contact UniSMS support if the block continues."
                )
            raise RuntimeError(f"UniSMS API error ({response.status_code}): {details}")

        try:
            result = response.json()
        except ValueError:
            result = {"response": response.text.strip()}

        reference = result.get("id", result.get("message_id", result.get("bulk_id", "accepted")))
        line = f"SMS -> {message} | UniSMS: {reference} | Recipient: {self.recipient}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "SMS (UniSMS)"


class PushNotification(Notification):
    def __init__(self, recipient: str):
        self.recipient = recipient.strip()

    @staticmethod
    def _firebase_app():
        if firebase_admin is None:
            raise RuntimeError("firebase-admin is not installed. Run: pip install -r requirements.txt")

        if firebase_admin._apps:
            return firebase_admin.get_app()

        credential_setting = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if credential_setting:
            credential_path = Path(credential_setting)
            if not credential_path.is_absolute():
                credential_path = BASE_DIR / credential_path
            if not credential_path.exists():
                raise RuntimeError(f"Firebase service account file was not found: {credential_path}")
            return firebase_admin.initialize_app(credentials.Certificate(str(credential_path)))

        return firebase_admin.initialize_app()

    def send(self, message: str) -> str:
        if not self.recipient:
            raise RuntimeError("Push recipient is required. Enter a Firebase Cloud Messaging device registration token.")

        self._firebase_app()
        fcm_message = messaging.Message(
            notification=messaging.Notification(
                title="NDMU Notification",
                body=message,
            ),
            token=self.recipient,
        )

        try:
            message_id = messaging.send(fcm_message)
        except Exception as exc:
            raise RuntimeError(f"Firebase Cloud Messaging error: {exc}") from exc

        line = f"PUSH -> {message} | FCM messageId: {message_id} | Recipient: {self.recipient}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "Push (Firebase)"


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


SERVICES: dict[str, type[NotificationService]] = {
    "Email": EmailService,
    "SMS": SMSService,
    "Push": PushService,
    "WhatsApp": WhatsAppService,
}
