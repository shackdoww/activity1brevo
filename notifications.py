from abc import ABC, abstractmethod


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
    def send(self, message: str) -> str:
        line = f"EMAIL -> {message}"
        print(line)
        return line

    def channel_name(self) -> str:
        return "Email"


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
        SERVICES[label]().notify(
            f"Grades are now viewable in the portal. [{label}]"
        )
