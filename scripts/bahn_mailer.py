import os
import smtplib
from email.mime.text import MIMEText

import requests
import schedule
import time


def fetch_bahn_data() -> str:
    """Fetch train data from the configured API."""
    api_url = os.environ["API_URL"]
    api_token = os.environ["API_TOKEN"]

    response = requests.get(api_url, headers={"Authorization": f"Bearer {api_token}"})
    response.raise_for_status()
    return response.text


def send_mail() -> None:
    """Send an e-mail containing the latest train data."""
    body = fetch_bahn_data()

    msg = MIMEText(body)
    msg["Subject"] = "Bahn News"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["MAIL_TO"]

    with smtplib.SMTP(
        os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587"))
    ) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.send_message(msg)


def main() -> None:
    """Schedule periodic mail with the latest train data."""
    for day in ("monday", "tuesday", "wednesday", "thursday"):
        day_schedule = getattr(schedule.every(), day)
        for moment in ("07:30", "09:30", "11:30"):
            day_schedule.at(moment).do(send_mail)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
