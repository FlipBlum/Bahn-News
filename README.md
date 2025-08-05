# Bahn-News
Ich lasse mir morgen von Montag - Donnerstag um 07:30, 09:30 und 11:30 die Züge von Köln nach Montabaur auf Ausfälle etc. checken.

## GitHub Actions

Dieses Repository enthält einen Workflow, der Benachrichtigungen über SMTP versendet. Damit er funktioniert, müssen in den Repository-Einstellungen folgende Secrets hinterlegt sein:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `MAIL_FROM`
- `MAIL_TO`
- `DB_API_KEY` (optional)

Im Workflow wird auf diese Werte über die Syntax `${{ secrets.NAME }}` zugegriffen.
