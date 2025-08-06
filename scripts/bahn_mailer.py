import os
import requests
import smtplib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from email.message import EmailMessage
import xml.etree.ElementTree as ET
import traceback

# Lade Umgebungsvariablen aus .env
load_dotenv()

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
EVA_KOELN = "8000207"            # Köln Hbf
EVA_MONTABAUR = "8000667"        # Montabaur (optional)
DB_API_KEY   = os.environ.get("DB_API_KEY")
DB_CLIENT_ID = os.environ.get("DB_CLIENT_ID")
DB_API_BASE  = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"

WINDOW_MINUTES = 60  # nur Züge innerhalb der nächsten Stunde

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def send_mail(subject: str, body: str) -> None:
    """Versendet eine reine Text-E-Mail via STARTTLS."""
    print("==> Sende E-Mail …")
    try:
        smtp_host = os.environ["SMTP_HOST"]
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ["SMTP_USER"]
        smtp_pass = os.environ["SMTP_PASS"]
        mail_from = os.environ["MAIL_FROM"]
        mail_to   = os.environ["MAIL_TO"]

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"]    = mail_from
        msg["To"]      = mail_to
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception:
        print("Fehler beim E-Mail-Versand:")
        print(traceback.format_exc())


# ---------------------------------------------------------------------------
# Zeit-Utilities
# ---------------------------------------------------------------------------

def _parse_time(val: str | None):
    if val and len(val) == 10:
        return datetime.strptime(val, "%y%m%d%H%M").replace(tzinfo=ZoneInfo("Europe/Berlin"))
    return None


def _fmt_time(val: str | None):
    dt = _parse_time(val)
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "?"


# ---------------------------------------------------------------------------
# E-Mail-Body
# ---------------------------------------------------------------------------

def build_mail_body(trains: list[dict]) -> str:
    ts = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M")
    header = [
        "Bahn-News: Köln Hbf → Montabaur",
        f"Stand: {ts} (lokal)",
        ""
    ]

    if not trains:
        body_lines = ["Keine Verbindungen in der nächsten Stunde."]
    else:
        body_lines = []
        for t in sorted(trains, key=lambda x: x["planned_dep"]):
            planned, actual = t["planned_dep"], t["actual_dep"]
            planned_dt, actual_dt = _parse_time(planned), _parse_time(actual)

            is_cancelled = t["cancelled"]
            is_delayed = (not is_cancelled) and planned_dt and actual_dt and planned_dt != actual_dt

            if is_cancelled:
                status_icon, status_text = "🚫", "Ausgefallen"
            elif is_delayed:
                status_icon, status_text = "☢️", "Verspätet"
            else:
                status_icon, status_text = "✅", "Pünktlich"

            delay = ""
            if is_delayed:
                delta = int((actual_dt - planned_dt).total_seconds() // 60)
                delay = f" (+{delta} min)"

            body_lines.append(
                f"{status_icon} Zug {t['train_no']}: {_fmt_time(planned)} → {_fmt_time(actual)}{delay} [{status_text}]"
            )

    footer = [
        "",
        "Legende: ✅ pünktlich   ☢️ verspätet   🚫 ausgefallen",
        "Datenquelle: DB Timetable API (live)"
    ]

    return "\n".join(header + body_lines + footer)


# ---------------------------------------------------------------------------
# DB-API-Abfrage (nur nächste Stunde)
# ---------------------------------------------------------------------------

def fetch_trains_koeln_to_montabaur() -> list[dict]:
    now   = datetime.now(ZoneInfo("Europe/Berlin"))
    later = now + timedelta(minutes=WINDOW_MINUTES)

    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    headers = {"DB-Api-Key": DB_API_KEY, "DB-Client-Id": DB_CLIENT_ID}

    # Wir rufen nur die aktuelle Stunde ab (Performance) — reicht für 60-Minuten-Fenster
    date = now.strftime("%y%m%d")
    hour = now.hour
    url  = f"{DB_API_BASE}/plan/{EVA_KOELN}/{date}/{hour:02d}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception:
        print("API-Fehler:")
        print(traceback.format_exc())
        return []

    root = ET.fromstring(resp.content)

    for stop in root.iter("s"):
        tl_elem  = stop.find("tl")
        train_no = tl_elem.attrib.get("n", "Unbekannt") if tl_elem is not None else "Unbekannt"

        for tag in ("dp", "ar"):
            elem = stop.find(tag)
            if elem is None:
                continue

            ppth = elem.attrib.get("ppth", "")
            if "montabaur" not in ppth.lower():
                continue

            planned   = elem.attrib.get("pt")
            actual    = elem.attrib.get("ct", planned)
            cancelled = elem.attrib.get("cs") == "c"

            planned_dt = _parse_time(planned)
            if not planned_dt or not (now <= planned_dt < later):
                continue  # außerhalb des 60-Min-Fensters

            key = (train_no, planned)
            if key in seen:
                continue
            seen.add(key)

            results.append(
                {
                    "planned_dep": planned,
                    "actual_dep": actual,
                    "cancelled": cancelled,
                    "train_no": train_no,
                }
            )

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    trains = fetch_trains_koeln_to_montabaur()
    body   = build_mail_body(trains)
    print(body)
    send_mail(subject="Bahn-News: Köln → Montabaur (nächste Stunde)", body=body)


if __name__ == "__main__":
    main()
