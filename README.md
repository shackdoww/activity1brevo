# CSPC 103 Activity 1 — Factory Method Notification GUI

A simple Python/Tkinter implementation of the Factory Method activity, with **real Email delivery through Brevo**.

## Channels

- Email — real Brevo transactional email
- SMS — simulated
- Push — simulated
- WhatsApp — simulated

## Run

```bash
python app.py
```

Tkinter is included with standard Python installations on Windows and macOS. On Ubuntu/Debian, install it with `sudo apt install python3-tk` if necessary.

## Brevo setup

The app uses Brevo's transactional email API endpoint `POST https://api.brevo.com/v3/smtp/email` and authenticates with the `api-key` header. Your sender must be configured/verified in Brevo before sending.

1. Copy `.env.example` to `.env`.
2. Put your Brevo API key in `BREVO_API_KEY`.
3. Put your verified Brevo sender address in `BREVO_SENDER_EMAIL`.
4. Put the destination address in `BREVO_RECIPIENT_EMAIL`.
5. Load the variables into your shell before running the app. For example on PowerShell:

```powershell
$env:BREVO_API_KEY="your_api_key"
$env:BREVO_SENDER_EMAIL="your_verified_sender@example.com"
$env:BREVO_SENDER_NAME="CSPC 103 Notification App"
$env:BREVO_RECIPIENT_EMAIL="recipient@example.com"
python app.py
```

On Linux/macOS:

```bash
export BREVO_API_KEY="your_api_key"
export BREVO_SENDER_EMAIL="your_verified_sender@example.com"
export BREVO_SENDER_NAME="CSPC 103 Notification App"
export BREVO_RECIPIENT_EMAIL="recipient@example.com"
python app.py
```

**Never commit your real API key.** `.env` is ignored by Git.

## Activity evidence

Send the same message through all four channels. The Email option now makes a real Brevo API request and shows the returned Brevo `messageId` in the Delivery Log. SMS, Push, and WhatsApp remain simulated so the Factory Method activity can demonstrate all four products without requiring separate provider accounts.

The Factory Method is `create_notification()`. The stable workflow is `notify()`, which validates the message, creates a notification through the factory method, and sends it without naming a concrete notification class.
