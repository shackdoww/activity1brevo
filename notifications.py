from abc import ABC, abstractmethod
import html
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

    @staticmethod
    def _grades_to_html(message: str) -> str:
        """Turn a grades notification into a broadly compatible HTML email."""
        if "\n\nGrades:\n" not in message:
            return (
                "<html><body>"
                "<div style=\"font-family:Arial,Helvetica,sans-serif;line-height:1.5;\">"
                f"{html.escape(message).replace(chr(10), '<br>')}"
                "</div></body></html>"
            )

        student_part, grades_part = message.split("\n\nGrades:\n", 1)
        grade_lines = grades_part.splitlines()

        total_units = ""
        weighted_average = ""
        rows = []

        for line in grade_lines:
            if line.startswith("Total Units:"):
                total_units = line.split(":", 1)[1].strip()
            elif line.startswith("Weighted Average:"):
                weighted_average = line.split(":", 1)[1].strip()
            elif line.strip():
                try:
                    course_code, remainder = line.split(" - ", 1)
                    subject, remainder = remainder.rsplit(": ", 1)
                    grade, units_part = remainder.rsplit(" (Units: ", 1)
                    units = units_part.rstrip(")")
                    rows.append((course_code, subject, units, grade))
                except ValueError:
                    continue

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
      <tbody>
        {table_rows}
      </tbody>
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
        recipient_email = os.getenv("BREVO_RECIPIENT_EMAIL", "").strip()

        if not api_key:
            raise RuntimeError(
                "BREVO_API_KEY is not configured. Put it in a .env file or set it as an OS environment variable."
            )
        if not sender_email:
            raise RuntimeError("BREVO_SENDER_EMAIL is not configured.")
        if not recipient_email:
            raise RuntimeError(
                "Email recipient is not configured. Enter a recipient in the application first."
            )

        payload = {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": recipient_email}],
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
