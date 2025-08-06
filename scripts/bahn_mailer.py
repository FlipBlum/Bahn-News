import os
import time
import schedule
import requests
import smtplib
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage
import xml.etree.ElementTree as ET

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
        planned_dep = t.get("planned_dep")
        actual_dep = t.get("actual_dep", planned_dep)
        train_no = t.get("train_no", "Unbekannt")
        cancelled = t.get("cancelled", False)
        delay = ""
        # Zeitformat: YYMMDDHHMM → lesbar
        def parse_time(val):
            if val and len(val) == 10:
                return datetime.strptime(val, "%y%m%d%H%M").strftime("%Y-%m-%d %H:%M")
            return val
        pd = parse_time(planned_dep)
        ad = parse_time(actual_dep)
        if planned_dep and actual_dep and planned_dep != actual_dep:
            try:
                delay_min = (datetime.strptime(actual_dep, "%y%m%d%H%M") - datetime.strptime(planned_dep, "%y%m%d%H%M")).total_seconds() // 60
                delay = f" (+{int(delay_min)} min)"
            except Exception:
                delay = ""
        status = "🚫 Ausgefallen" if cancelled else "✅"
        lines.append(f"Zug {train_no}: {pd} → {ad}{delay} {status}")
    return "\n".join(lines)

def fetch_trains_koeln_to_montabaur():
    now = datetime.now()
    results = []
    headers = {
        "DB-Api-Key": DB_API_KEY,
        "DB-Client-Id": DB_CLIENT_ID
    }
    for offset in range(2):  # aktuelle Stunde + nächste Stunde
        date = now.strftime("%y%m%d")  # YYMMDD
        hour = (now.hour + offset) % 24
        url = f"{DB_API_BASE}/plan/{EVA_KOELN}/{date}/{hour:02d}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            # XML-Parsing
            root = ET.fromstring(resp.content)
            # Suche alle <s> (TimetableStop) mit Ziel Montabaur
            for stop in root.findall(".//s"):
                found = False
                # Prüfe, ob eine Verbindung nach Montabaur existiert
                for conn in stop.findall("conn"):
                    eva_elem = conn.find("eva")
                    if eva_elem is not None and eva_elem.text and str(eva_elem.text) == EVA_MONTABAUR:
                        found = True
                # Alternativ: Prüfe, ob der Halt selbst Montabaur ist
                eva_elem = stop.find("eva")
                if eva_elem is not None and eva_elem.text and str(eva_elem.text) == EVA_MONTABAUR:
                    found = True
                if found:
                    # Extrahiere relevante Infos
                    planned_dep = None
                    actual_dep = None
                    cancelled = False
                    train_no = None
                    # planned departure
                    dp_elem = stop.find("dp")
                    if dp_elem is not None:
                        pt_elem = dp_elem.find("pt")
                        if pt_elem is not None and pt_elem.text:
                            planned_dep = pt_elem.text
                        ct_elem = dp_elem.find("ct")
                        if ct_elem is not None and ct_elem.text:
                            actual_dep = ct_elem.text
                        cs_elem = dp_elem.find("cs")
                        if cs_elem is not None and cs_elem.text == "c":
                            cancelled = True
                    # train number
                    tl_elem = stop.find("tl")
                    if tl_elem is not None:
                        n_elem = tl_elem.find("n")
                        if n_elem is not None and n_elem.text:
                            train_no = n_elem.text
                    results.append({
                        "planned_dep": planned_dep,
                        "actual_dep": actual_dep,
                        "cancelled": cancelled,
                        "train_no": train_no
                    })
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
