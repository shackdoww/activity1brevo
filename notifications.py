from abc import ABC, abstractmethod
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # The app can still use normal OS environment variables if python-dotenv
    # is not installed.
    pass


# ---------------- PRODUCT ----------------
class Notification(ABC):
    @abstractmethod
    def send(self, message: str) -> str:
        """Deliver the message and return the delivery line."""

    @abstractmethod
    def channel_name(self) -> str:
        """Return the human-readable channel name."""


# ------------ CONCRETE PRODUCTS ------------
class EmailNotification(Notification):
    """Real email delivery through Brevo's transactional email API."""

    def send(self, message: str) -> str:
        api_key = os.getenv("BREVO_API_KEY", "").strip()
        sender_email = os.getenv("BREVO_SENDER_EMAIL", "").strip()
        sender_name = os.getenv("BREVO_SENDER_NAME", "Activity 1 Notification App").strip()
        recipient_email = os.getenv("BREVO_RECIPIENT_EMAIL", "").strip()

        if not api_key:
            raise RuntimeError(
                "BREVO_API_KEY is not configured. Put it in a .env file or set it as an OS environment variable."
            )
        if not sender_email:
            raise RuntimeError("BREVO_SENDER_EMAIL is not configured.")
        if not recipient_email:
            raise RuntimeError("BREVO_RECIPIENT_EMAIL is not configured.")

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": recipient_email}],
            "subject": "CSPC 103 Notification",
            "textContent": message,
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
    def send(self, message: str) -> str:
        line = f"SMS -> {message}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "SMS"


class PushNotification(Notification):
    def send(self, message: str) -> str:
        line = f"PUSH -> {message}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "Push"


class WhatsAppNotification(Notification):
    def send(self, message: str) -> str:
        line = f"WHATSAPP -> {message}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "WhatsApp"


# ---------------- CREATOR ----------------
class NotificationService(ABC):
    @abstractmethod
    def create_notification(self) -> Notification:
        """THE FACTORY METHOD. Subclasses decide the concrete product."""

    # Stable algorithm: do not change when a new channel is added.
    def notify(self, message: str) -> str:
        if not message.strip():
            raise ValueError("Message must not be empty.")
        notification = self.create_notification()
        return notification.send(message)


# ------------ CONCRETE CREATORS ------------
class EmailService(NotificationService):
    def create_notification(self) -> Notification:
        return EmailNotification()


class SMSService(NotificationService):
    def create_notification(self) -> Notification:
        return SMSNotification()


class PushService(NotificationService):
    def create_notification(self) -> Notification:
        return PushNotification()


class WhatsAppService(NotificationService):
    def create_notification(self) -> Notification:
        return WhatsAppNotification()


# The one place where the concrete creator is selected.
SERVICES: dict[str, type[NotificationService]] = {
    "Email": EmailService,
    "SMS": SMSService,
    "Push": PushService,
    "WhatsApp": WhatsAppService,
}


if __name__ == "__main__":
    for label in SERVICES:
        try:
            SERVICES[label]().notify(
                f"Grades are now viewable in the portal. [{label}]"
            )
        except RuntimeError as exc:
            print(f"{label} ERROR -> {exc}")
