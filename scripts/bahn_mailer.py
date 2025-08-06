import os
import time
import schedule
import requests
import smtplib
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Konfiguration
EVA_KOELN = "8000207"
EVA_MONTABAUR = "8000667"
DB_API_KEY = os.environ.get("DB_API_KEY")
DB_CLIENT_ID = os.environ.get("DB_CLIENT_ID")
DB_API_BASE = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"

def send_mail(subject, body):
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    mail_from = os.environ["MAIL_FROM"]
    mail_to = os.environ["MAIL_TO"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

def format_train_info(trains):
    if not trains:
        return "Keine Verbindungen gefunden."
    lines = []
    for t in trains:
        planned_dep = t.get("scheduledDepartureTime")
        actual_dep = t.get("actualDepartureTime", planned_dep)
        train_no = t.get("trainNum", "Unbekannt")
        cancelled = t.get("cancelled", False)
        delay = ""
        if planned_dep and actual_dep and planned_dep != actual_dep:
            delay = f" (+{int((datetime.fromisoformat(actual_dep) - datetime.fromisoformat(planned_dep)).total_seconds() // 60)} min)"
        status = "🚫 Ausgefallen" if cancelled else "✅"
        lines.append(f"Zug {train_no}: {planned_dep} → {actual_dep}{delay} {status}")
    return "\n".join(lines)

def fetch_trains_koeln_to_montabaur():
    now = datetime.now()
    results = []
    headers = {
        "DB-Api-Key": DB_API_KEY,
        "DB-Client-Id": DB_CLIENT_ID
    }
    for offset in range(2):  # aktuelle Stunde + nächste Stunde
        date = now.strftime("%Y-%m-%d")
        hour = (now.hour + offset) % 24
        url = f"{DB_API_BASE}/{EVA_KOELN}/{date}/{hour:02d}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Filtere alle Fahrten, die nach Montabaur gehen
            for entry in data.get("plan", []):
                if any(stop.get("stationEvaNr") == EVA_MONTABAUR for stop in entry.get("stopInfo", [])):
                    results.append(entry)
        else:
            print(f"Fehler bei API-Request: {resp.status_code} {resp.text}")
    return results

def job():
    print(f"Starte Abfrage: {datetime.now()}")
    trains = fetch_trains_koeln_to_montabaur()
    info = format_train_info(trains)
    print(info)
    send_mail(
        subject="Bahn-News: Köln Hbf → Montabaur",
        body=info
    )

def main():
    # Mo–Do, 7:30, 9:30, 11:30
    schedule.every().monday.at("07:30").do(job)
    schedule.every().monday.at("09:30").do(job)
    schedule.every().monday.at("11:30").do(job)
    schedule.every().tuesday.at("07:30").do(job)
    schedule.every().tuesday.at("09:30").do(job)
    schedule.every().tuesday.at("11:30").do(job)
    schedule.every().wednesday.at("07:30").do(job)
    schedule.every().wednesday.at("09:30").do(job)
    schedule.every().wednesday.at("11:30").do(job)
    schedule.every().thursday.at("07:30").do(job)
    schedule.every().thursday.at("09:30").do(job)
    schedule.every().thursday.at("11:30").do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
