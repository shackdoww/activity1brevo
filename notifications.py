from abc import ABC, abstractmethod
import html
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, Request, build_opener, urlopen

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
        """Deliver the message and return the delivery line."""

    @abstractmethod
    def channel_name(self) -> str:
        """Return the human-readable channel name."""


class EmailNotification(Notification):
    """Real email delivery through Brevo's transactional email API."""

    def __init__(self, recipient: str):
        self.recipient = recipient.strip()

    @staticmethod
    def _grades_to_html(message: str) -> str:
        if "\n\nGrades:\n" not in message:
            return (
                "<html><body>"
                "<div style=\"font-family:Arial,Helvetica,sans-serif;line-height:1.5;\">"
                f"{html.escape(message).replace(chr(10), '<br>')}"
                "</div></body></html>"
            )

        student_part, grades_part = message.split("\n\nGrades:\n", 1)
        rows = []
        total_units = ""
        weighted_average = ""
        row_pattern = re.compile(
            r"^\s*(.*?)\s*-\s*(.*?)\s*:\s*([^()]+?)\s*\(\s*Units\s*:\s*([^\)]+)\s*\)\s*$"
        )

        for line in grades_part.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.lower().startswith("total units:"):
                total_units = stripped.split(":", 1)[1].strip()
                continue
            if stripped.lower().startswith("weighted average:"):
                weighted_average = stripped.split(":", 1)[1].strip()
                continue
            match = row_pattern.match(stripped)
            if match:
                code, subject, grade, units = match.groups()
                rows.append((code.strip(), subject.strip(), units.strip(), grade.strip()))

        table_rows = "".join(
            "<tr>"
            f"<td style=\"border:1px solid #999999;padding:8px;\">{html.escape(code)}</td>"
            f"<td style=\"border:1px solid #999999;padding:8px;\">{html.escape(subject)}</td>"
            f"<td style=\"border:1px solid #999999;padding:8px;text-align:center;\">{html.escape(units)}</td>"
            f"<td style=\"border:1px solid #999999;padding:8px;text-align:center;font-weight:bold;\">{html.escape(grade)}</td>"
            "</tr>"
            for code, subject, units, grade in rows
        )

        if not table_rows:
            table_rows = (
                "<tr><td colspan=\"4\" style=\"border:1px solid #999999;padding:8px;\">"
                "No grade rows found.</td></tr>"
            )

        return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;font-family:Arial,Helvetica,sans-serif;color:#1A1A2E;">
  <div style="max-width:760px;margin:0 auto;">
    <h2 style="margin:0 0 6px 0;color:#1F3864;">CSPC 103 Grade Notification</h2>
    <p style="margin:0 0 18px 0;">{html.escape(student_part)}</p>
    <table border="1" cellpadding="8" cellspacing="0" width="100%" style="border-collapse:collapse;border:1px solid #999999;font-size:14px;">
      <thead>
        <tr>
          <th bgcolor="#1F3864" style="border:1px solid #999999;color:#FFFFFF;text-align:left;padding:9px;">Course Code</th>
          <th bgcolor="#1F3864" style="border:1px solid #999999;color:#FFFFFF;text-align:left;padding:9px;">Course Title</th>
          <th bgcolor="#1F3864" style="border:1px solid #999999;color:#FFFFFF;text-align:center;padding:9px;">Units</th>
          <th bgcolor="#1F3864" style="border:1px solid #999999;color:#FFFFFF;text-align:center;padding:9px;">Grade</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
    <br>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;border:1px solid #999999;font-size:14px;">
      <tr>
        <td bgcolor="#FFF2CC" style="border:1px solid #999999;font-weight:bold;">Total Units</td>
        <td style="border:1px solid #999999;">{html.escape(total_units)}</td>
        <td bgcolor="#FFF2CC" style="border:1px solid #999999;font-weight:bold;">Weighted Average</td>
        <td style="border:1px solid #999999;font-weight:bold;">{html.escape(weighted_average)}</td>
      </tr>
    </table>
  </div>
</body>
</html>"""

    def send(self, message: str) -> str:
        api_key = os.getenv("BREVO_API_KEY", "").strip()
        sender_email = os.getenv("BREVO_SENDER_EMAIL", "").strip()
        sender_name = os.getenv("BREVO_SENDER_NAME", "Activity 1 Notification App").strip()

        if not api_key:
            raise RuntimeError("BREVO_API_KEY is not configured. Put it in a .env file or set it as an OS environment variable.")
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
    """Real SMS delivery through UniSMS."""

    def __init__(self, recipient: str):
        self.recipient = recipient.strip()

    def send(self, message: str) -> str:
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
        request = Request(
            "https://unismsapi.com/api/sms",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "accept": "application/json",
                "content-type": "application/json",
            },
            method="POST",
        )
        auth = (api_secret + ":").encode("utf-8")
        import base64
        request.add_header("Authorization", "Basic " + base64.b64encode(auth).decode("ascii"))

        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8", errors="replace")
                try:
                    result = json.loads(raw)
                except json.JSONDecodeError:
                    result = {"response": raw}
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"UniSMS API error ({exc.code}): {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not connect to UniSMS: {exc.reason}") from exc

        status = result.get("status", result.get("message", "accepted")) if isinstance(result, dict) else "accepted"
        line = f"SMS -> {message} | UniSMS: {status} | Recipient: {self.recipient}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "SMS (UniSMS)"


class PushNotification(Notification):
    """Real push notification delivery through Firebase Cloud Messaging."""

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
        """THE FACTORY METHOD. Subclasses decide the concrete product."""

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


if __name__ == "__main__":
    for label in SERVICES:
        try:
            service = SERVICES[label]()
            service.notify(f"Grades are now viewable in the portal. [{label}]")
        except RuntimeError as exc:
            print(f"{label} ERROR -> {exc}")
