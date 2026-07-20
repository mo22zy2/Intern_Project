import json
from urllib.request import Request, urlopen
from urllib.error import URLError

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Set Telegram bot webhook URL"

    def add_arguments(self, parser):
        parser.add_argument("webhook_url", type=str, help="Full public URL to the webhook endpoint (e.g. https://example.com/telegram-webhook/)")

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set in settings/.env")
        url = options["webhook_url"].rstrip("/") + "/"
        payload = json.dumps({"url": url}).encode()
        req = Request(
            f"https://api.telegram.org/bot{token}/setWebhook",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except (URLError, json.JSONDecodeError) as e:
            raise CommandError(f"Failed to set webhook: {e}")

        if data.get("ok"):
            self.stdout.write(self.style.SUCCESS(f"Webhook set to: {url}"))
        else:
            raise CommandError(f"Telegram API error: {data.get('description', 'unknown')}")
