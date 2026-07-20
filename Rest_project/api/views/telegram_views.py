import json
import logging

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string

from ..models import User
from ..services.telegram_service import send_message

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    message = data.get("message", {})
    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")
    if not text or not chat_id:
        return HttpResponse(status=200)

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Welcome! Use /start <code> to connect your account.")
            return HttpResponse(status=200)
        code = parts[1].strip()
        try:
            user = User.objects.get(telegram_verification_code=code)
        except User.DoesNotExist:
            send_message(chat_id, "Invalid or expired code. Please generate a new one from your profile.")
            return HttpResponse(status=200)

        user.telegram_chat_id = str(chat_id)
        user.telegram_verification_code = None
        user.save(update_fields=["telegram_chat_id", "telegram_verification_code"])

        send_message(
            chat_id,
            f"\U00002705 Successfully connected, {user.first_name or user.username}! "
            f"You will now receive order and reservation notifications here."
        )

    return HttpResponse(status=200)


@login_required(login_url="login")
def connect_telegram(request):
    code = get_random_string(length=32)
    request.user.telegram_verification_code = code
    request.user.save(update_fields=["telegram_verification_code"])
    messages.success(request, _("Verification code generated. Send it to the bot on Telegram."))
    return redirect("profile")


@login_required(login_url="login")
def disconnect_telegram(request):
    request.user.telegram_chat_id = None
    request.user.telegram_verification_code = None
    request.user.save(update_fields=["telegram_chat_id", "telegram_verification_code"])
    messages.success(request, _("Telegram disconnected."))
    return redirect("profile")
