import base64
import logging
from io import BytesIO

import qrcode

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

logger = logging.getLogger(__name__)


def _imports():
    from ..models import Order, OrderItem, Cart, CartItem, Inventory, MenuCustomizationOption, ReservationSystem
    from . import cart_service
    from . import payment_service
    return Order, OrderItem, Cart, CartItem, Inventory, MenuCustomizationOption, ReservationSystem, cart_service, payment_service


def get_checkout_data(user):
    _, _, Cart, CartItem, _, MenuCustomizationOption, _, cart_service, payment_service = _imports()
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return None
    items_with_prices, subtotal = cart_service.get_cart_items_with_prices(cart)
    payment_methods = payment_service.get_user_payment_methods(user)
    return {
        "items": items_with_prices,
        "subtotal": subtotal,
        "cart": cart,
        "payment_methods": payment_methods,
    }


def _calculate_item_price(cartitem):
    _, _, _, _, _, MenuCustomizationOption, _, _, _ = _imports()
    base = cartitem.menu.price
    extra = 0
    if cartitem.options_text and cartitem.option is None:
        opt_names = [s.strip() for s in cartitem.options_text.split(",")]
        extras = MenuCustomizationOption.objects.filter(
            menu=cartitem.menu, option_name__in=opt_names
        ).values_list("extra_price", flat=True)
        extra = sum(extras)
    elif cartitem.option:
        extra = cartitem.option.extra_price
    return base + extra


def place_order(
    user,
    delivery_type,
    delivery_address="",
    pickup_date=None,
    pickup_time=None,
    reservation_date=None,
    reservation_time=None,
    seats=None,
    payment_type="card",
    payment_method_id=None,
    card_number=None,
):
    Order, OrderItem, Cart, CartItem, Inventory, _, ReservationSystem, _, payment_service = _imports()
    from . import reservation_service

    delivery_type = "dine_in" if delivery_type == "dine-in" else delivery_type

    try:
        with transaction.atomic():
            cart = Cart.objects.get(user=user)
            items = CartItem.objects.filter(cart=cart).select_related(
                "menu__item", "menu__category", "option"
            )
            if not items:
                raise ValueError("Your cart is empty")

            for cartitem in items:
                if (
                    not cartitem.menu.available
                    or cartitem.menu.item is None
                    or (cartitem.menu.item.item_count or 0) < cartitem.quantity
                ):
                    raise ValueError("Sorry, an item in your cart is out of stock")

            reservation = None

            if delivery_type == "delivery":
                if not delivery_address:
                    raise ValueError("Please enter a delivery address")
            elif delivery_type == "dine_in":
                parsed_date, parsed_time, parsed_seats = reservation_service.validate_reservation_input(
                    str(reservation_date) if reservation_date else "",
                    str(reservation_time) if reservation_time else "",
                    seats,
                )
                reservation = ReservationSystem.objects.create(
                    user=user,
                    reservation_date=parsed_date,
                    reservation_time=parsed_time,
                    seats=parsed_seats,
                    status="pending",
                )
            elif delivery_type == "pickup":
                if not pickup_date:
                    raise ValueError("Please select a pickup date")

            total_price = 0
            for cartitem in items:
                total_price += _calculate_item_price(cartitem) * cartitem.quantity

            order_number = Order.objects.filter(user=user).count() + 1
            while Order.objects.filter(user=user, order_number=order_number).exists():
                order_number += 1

            order = Order.objects.create(
                user=user,
                delivery_type=delivery_type,
                delivery_address=delivery_address,
                pickup_date=pickup_date,
                pickup_time=pickup_time,
                reservation=reservation,
                order_number=order_number,
                status="pending",
                total_price=total_price,
            )

            for cartitem in items:
                unit_price = _calculate_item_price(cartitem)
                opts_text = cartitem.options_text or ""
                if cartitem.option:
                    opts_text = cartitem.option.option_name
                OrderItem.objects.create(
                    order=order,
                    menu=cartitem.menu,
                    option=cartitem.option,
                    quantity=cartitem.quantity,
                    unit_price=unit_price,
                    options_text=opts_text,
                )
                inv = cartitem.menu.item
                inv.ordered = (inv.ordered or 0) + cartitem.quantity
                inv.save()

            base_url = getattr(settings, "BASE_URL", "http://localhost:8000").rstrip("/")
            qr = qrcode.make(f"{base_url}/menu?from=order_{order.id}")
            buf = BytesIO()
            qr.save(buf, format="PNG")
            order.qr_data = base64.b64encode(buf.getvalue()).decode()
            order.save(update_fields=["qr_data"])

            if payment_type == "cash":
                payment_method = payment_service.get_or_create_cash_method(user)
                payment_service.create_payment(
                    order=order,
                    payment_method=payment_method,
                    amount=total_price,
                    status="confirmed",
                    paid_at=None,
                )
            else:
                if payment_method_id:
                    from ..models import PaymentMethod
                    try:
                        payment_method = PaymentMethod.objects.get(id=payment_method_id, user=user)
                    except ObjectDoesNotExist:
                        raise ValueError("Please select a valid payment method")
                elif card_number:
                    payment_method = payment_service.create_or_get_card_method(user, card_number)
                else:
                    order.delete()
                    if reservation:
                        reservation.delete()
                    raise ValueError("Please select or enter a payment method")
                payment_service.create_payment(
                    order=order,
                    payment_method=payment_method,
                    amount=total_price,
                    status="completed",
                )

            cart.delete()
    except Cart.DoesNotExist:
        raise ValueError("Your cart is empty")

    try:
        from .telegram_service import send_new_order_to_staff
        send_new_order_to_staff(order)
    except Exception:
        logger.exception("Failed to notify staff about new order %s", order.id)

    return order


def get_user_orders(user):
    Order, _, _, _, _, _, _, _, _ = _imports()
    return Order.objects.filter(user=user).order_by("-created_at")


def get_order_detail(user, order_id):
    from django.core.exceptions import ObjectDoesNotExist
    Order, _, _, _, _, _, _, _, _ = _imports()
    try:
        return Order.objects.prefetch_related(
            "orderitem_set__menu__item", "orderitem_set__option", "payment__payment_method"
        ).get(id=order_id, user=user)
    except ObjectDoesNotExist:
        return None
