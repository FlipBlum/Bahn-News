import os
import smtplib
from email.message import EmailMessage


def main():
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    mail_from = os.environ["MAIL_FROM"]
    mail_to = os.environ["MAIL_TO"]
    db_api_key = os.environ.get("DB_API_KEY")

    msg = EmailMessage()
    msg["Subject"] = "Bahn-News notification"
    msg["From"] = mail_from
    msg["To"] = mail_to
    body = "DB API key configured." if db_api_key else "No DB API key configured."
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


if __name__ == "__main__":
    main()
