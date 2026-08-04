import html
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError

from django.conf import settings

logger = logging.getLogger(__name__)


def _bot_url(method):
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


def send_message(chat_id, text, parse_mode="HTML"):
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram message")
        return False
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode()
    req = Request(_bot_url("sendMessage"), data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except URLError as e:
        logger.error("Telegram sendMessage failed: %s", e)
        return False


def send_order_confirmed(user, order):
    if not user.telegram_chat_id:
        return False
    items_list = ", ".join(
        html.escape(oi.menu.item.item_name)
        for oi in order.orderitem_set.select_related("menu__item").all()
    )
    text = (
        f"\U00002705 <b>Order Confirmed!</b>\n\n"
        f"Order #{order.id}\n"
        f"Items: {items_list}\n"
        f"Total: ${order.total_price:.2f}\n"
        f"Type: {html.escape(order.delivery_type)}\n"
        f"Status: Confirmed"
    )
    return send_message(user.telegram_chat_id, text)


def send_reservation_confirmed(user, reservation):
    if not user.telegram_chat_id:
        return False
    text = (
        f"\U00002705 <b>Reservation Confirmed!</b>\n\n"
        f"Date: {html.escape(str(reservation.reservation_date))}\n"
        f"Time: {html.escape(str(reservation.reservation_time))}\n"
        f"Seats: {html.escape(str(reservation.seats))}\n"
        f"Status: Confirmed"
    )
    return send_message(user.telegram_chat_id, text)


def _notify_all_staff(text):
    from ..models import User
    staff = User.objects.filter(is_staff=True).exclude(telegram_chat_id__isnull=True).exclude(telegram_chat_id__exact="")
    for user in staff:
        send_message(user.telegram_chat_id, text)


def _build_new_order_text(order):
    customer_name = html.escape(order.user.first_name or order.user.username)
    phone = html.escape(order.user.phone or "—")
    email = html.escape(order.user.email or "—")
    lines = [f"\U0001F514 <b>New Order #{order.id}</b>\n"]
    lines.append(f"Customer: {customer_name}")
    lines.append(f"Phone: {phone}")
    lines.append(f"Email: {email}")
    lines.append("")
    lines.append(f"<b>Items:</b>")
    for oi in order.orderitem_set.select_related("menu__item", "option").all():
        name = html.escape(oi.menu.item.item_name)
        qty = oi.quantity
        price = oi.unit_price
        opts = f" ({html.escape(oi.options_text)})" if oi.options_text else ""
        subtotal = qty * price
        lines.append(f"  \u2022 {name}{opts} x{qty} @ ${price:.2f} = ${subtotal:.2f}")
    lines.append("")
    lines.append(f"<b>Total: ${order.total_price:.2f}</b>")
    lines.append(f"Type: {html.escape(order.delivery_type)}")
    if order.delivery_type == "delivery" and order.delivery_address:
        lines.append(f"Address: {html.escape(order.delivery_address)}")
    if order.reservation_id:
        r = order.reservation
        if r:
            lines.append(
                f"Reservation: {html.escape(str(r.reservation_date))} @ "
                f"{html.escape(str(r.reservation_time))} ({html.escape(str(r.seats))} seats)"
            )
    lines.append("")
    lines.append("Review in dashboard to confirm or cancel.")
    return "\n".join(lines)


def send_new_order_to_staff(order):
    from ..models import Notification, User
    message = _build_new_order_text(order)
    try:
        for staff in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=staff,
                notification_type="new_order_pending",
                title=f"New Order #{order.id}",
                message=f"New order #{order.id} from {order.user.first_name or order.user.username}. Total: ${order.total_price:.2f}",
                related_order=order,
            )
    except Exception:
        logger.exception("Failed to create staff notifications for order %s", order.id)
    _notify_all_staff(message)


def send_low_inventory_to_staff(inventory):
    text = (
        f"\u26A0\uFE0F <b>Low Inventory Alert</b>\n\n"
        f"Item: {html.escape(inventory.item_name)}\n"
        f"Remaining: {html.escape(str(inventory.item_count))}\n\n"
        f"Please restock soon."
    )
    _notify_all_staff(text)


def send_new_review_to_staff(review):
    text = (
        f"\U0001F4AC <b>New Review</b>\n\n"
        f"User: {html.escape(review.user.first_name or review.user.username)}\n"
        f"Item: {html.escape(review.menu.item.item_name)}\n"
        f"Rating: {chr(11088) * review.rating} ({review.rating}/5)\n"
        f"Comment: {html.escape(review.comment or '(no comment)')}"
    )
    _notify_all_staff(text)
