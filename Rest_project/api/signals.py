from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from .models import Order, ReservationSystem, Inventory, Review, Notification, User
from .services.telegram_service import (
    send_order_confirmed,
    send_reservation_confirmed,
    send_low_inventory_to_staff,
    send_new_review_to_staff,
)

LOW_STOCK_THRESHOLD = 10


@receiver(pre_save, sender=Order)
def capture_old_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Order.objects.get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(pre_save, sender=ReservationSystem)
def capture_old_reservation_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = ReservationSystem.objects.get(pk=instance.pk).status
        except ReservationSystem.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(pre_save, sender=Inventory)
def capture_old_inventory_count(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_item_count = Inventory.objects.get(pk=instance.pk).item_count
        except Inventory.DoesNotExist:
            instance._old_item_count = None
    else:
        instance._old_item_count = None


@receiver(post_save, sender=Order)
def notify_order_confirmed(sender, instance, created, **kwargs):
    if created:
        return
    old_status = getattr(instance, "_old_status", None)
    if old_status != "confirmed" and instance.status == "confirmed":
        items_list = ", ".join(
            oi.menu.item.item_name for oi in instance.orderitem_set.select_related("menu__item").all()
        )
        Notification.objects.create(
            user=instance.user,
            notification_type="order_confirmed",
            title=_("Order Confirmed"),
            message=_("Your order #{id} ({items}) has been confirmed! Total: ${total:.2f}").format(
                id=instance.id, items=items_list, total=instance.total_price
            ),
            related_order=instance,
        )
        send_order_confirmed(instance.user, instance)


@receiver(post_save, sender=ReservationSystem)
def notify_reservation_confirmed(sender, instance, created, **kwargs):
    if created:
        return
    old_status = getattr(instance, "_old_status", None)
    if old_status != "confirmed" and instance.status == "confirmed":
        Notification.objects.create(
            user=instance.user,
            notification_type="reservation_confirmed",
            title=_("Reservation Confirmed"),
            message=_("Your reservation for {date} at {time} ({seats} seats) has been confirmed!").format(
                date=instance.reservation_date,
                time=instance.reservation_time,
                seats=instance.seats,
            ),
            related_reservation=instance,
        )
        send_reservation_confirmed(instance.user, instance)


@receiver(post_save, sender=Inventory)
def notify_staff_low_inventory(sender, instance, created, **kwargs):
    old_count = getattr(instance, "_old_item_count", None)
    if old_count is None:
        return
    if old_count >= LOW_STOCK_THRESHOLD and instance.item_count < LOW_STOCK_THRESHOLD:
        for staff in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=staff,
                notification_type="low_inventory",
                title=_("Low Inventory: {item}").format(item=instance.item_name),
                message=_("{item} is running low ({count} remaining).").format(
                    item=instance.item_name, count=instance.item_count,
                ),
            )
        send_low_inventory_to_staff(instance)


@receiver(post_save, sender=Review)
def notify_staff_new_review(sender, instance, created, **kwargs):
    if not created:
        return
    for staff in User.objects.filter(is_staff=True):
        Notification.objects.create(
            user=staff,
            notification_type="new_review",
            title=_("New Review for {item}").format(item=instance.menu.item.item_name),
            message=_("{user} rated {item} {rating}/5. Comment: {comment}").format(
                user=instance.user.first_name or instance.user.username,
                item=instance.menu.item.item_name,
                rating=instance.rating,
                comment=instance.comment or "(no comment)",
            ),
        )
    send_new_review_to_staff(instance)
