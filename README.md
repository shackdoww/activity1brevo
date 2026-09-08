# CSPC 103 Activity 1 — Factory Method Notification GUI

A simple Python/Tkinter implementation of the Factory Method activity.

## Channels

- Email
- SMS
- Push
- WhatsApp

## Run

```bash
python app.py
```

No third-party packages are required. Tkinter is included with standard Python installations on Windows and macOS. On Ubuntu/Debian, install it with `sudo apt install python3-tk` if necessary.

## Activity evidence

Send the same message through all four channels. The Delivery Log will show all four delivery lines, and the proof label will identify the Creator and Product used for the last selected channel.

The Factory Method is `create_notification()`. The stable workflow is `notify()`, which validates the message, creates a notification through the factory method, and sends it without naming a concrete notification class.
