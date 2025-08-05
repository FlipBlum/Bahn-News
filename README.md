# Bahn-News
Ich lasse mir morgen von Montag - Donnerstag um 07:30, 09:30 und 11:30 die Züge von Köln nach Montabaur auf Ausfälle etc. checken.

## Installation & Nutzung

```bash
pip install -r requirements.txt
python bahn_news.py
```

## GitHub Actions

Der Workflow benötigt folgende GitHub-Secrets:

- `RAPIDAPI_KEY` – Schlüssel für den Zugriff auf die Bahn-API.
- `TELEGRAM_BOT_TOKEN` – Token des Telegram-Bots.
- `TELEGRAM_CHAT_ID` – Ziel-Chat für die Benachrichtigungen.

GitHub interpretiert die Cron-Zeiten im Workflow in UTC. Ein auf 07:30 Uhr deutsche Zeit geplanter Lauf entspricht daher 05:30 UTC im Winter bzw. 06:30 UTC im Sommer.
