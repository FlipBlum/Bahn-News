# Bahn-News
Ich lasse mir morgen von Montag - Donnerstag um 07:30, 09:30 und 11:30 die Züge von Köln nach Montabaur auf Ausfälle etc. checken.

## Installation

1. Stelle sicher, dass Python 3 installiert ist.
2. Klone das Repository und wechsle in das Projektverzeichnis.
3. (Optional) Erstelle und aktiviere eine virtuelle Umgebung:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Installiere die Abhängigkeiten:

   ```bash
   pip install -r requirements.txt
   ```

## Konfiguration

### Benötigte Umgebungsvariablen

Die Anwendung verwendet folgende Variablen, die üblicherweise als Repository-Secrets hinterlegt werden:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` – Zugangsdaten zum SMTP-Server
- `MAIL_FROM` – Absenderadresse
- `MAIL_TO` – Empfängeradresse
- `API_URL` – Endpoint der Bahn-API
- `API_TOKEN` – Token zur Authentifizierung bei der API

### Geplanter GitHub Action-Workflow

Der Workflow in `.github/workflows/bahn-mailer.yml` sendet die E-Mails automatisch zu festen Zeiten. Standardmäßig wird er täglich um **04:30 UTC**, **06:30 UTC** und **08:30 UTC** ausgeführt.

### Zeitplan anpassen

Um andere Ausführungszeiten zu verwenden, passe die `cron`-Einträge im oben genannten Workflow an. Die Cron-Syntax orientiert sich immer an UTC.


