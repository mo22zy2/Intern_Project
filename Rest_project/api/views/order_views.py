import base64
from datetime import date
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from ..models import Cart, CartItem, Order, OrderItem, Inventory, MenuCustomizationOption, PaymentMethod, Payment, ReservationSystem
import qrcode


@login_required(login_url="login")
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        messages.error(request, _("Your cart is empty."))
        return redirect("view_cart")

    items = CartItem.objects.filter(cart=cart).select_related("menu__item", "option")
    if not items:
        messages.error(request, _("Your cart is empty."))
        return redirect("view_cart")

    subtotal = 0
    for cartitem in items:
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
        cartitem.unit_price = base + extra
        cartitem.line_total = cartitem.unit_price * cartitem.quantity
        subtotal += cartitem.line_total

    payment_methods = PaymentMethod.objects.filter(user=request.user)

    return render(request, "orders/checkout.html", {
        "cart_items": items,
        "subtotal": subtotal,
        "payment_methods": payment_methods,
    })


@login_required(login_url="login")
def place_order(request):
    if request.method != "POST":
        return redirect("checkout")

    cart = get_object_or_404(Cart, user=request.user)
    items = CartItem.objects.filter(cart=cart).select_related("menu__item", "menu__category", "option")

    if not items:
        messages.error(request, _("Your cart is empty."))
        return redirect("view_cart")

    delivery_type = request.POST.get("delivery_type", "delivery")

    reservation = None
    delivery_address = ""

    if delivery_type == "delivery":
        delivery_address = request.POST.get("delivery_address", "").strip()
        if not delivery_address:
            messages.error(request, _("Please enter a delivery address."))
            return redirect("checkout")
    else:
        reservation_date = request.POST.get("reservation_date", "").strip()
        reservation_time = request.POST.get("reservation_time", "").strip()
        seats = request.POST.get("seats", "").strip()

        if not reservation_date or not reservation_time or not seats:
            messages.error(request, _("Please fill in all reservation details."))
            return redirect("checkout")

        try:
            seats = int(seats)
            if seats < 1:
                raise ValueError
        except ValueError:
            messages.error(request, _("Seats must be a positive number."))
            return redirect("checkout")

        reservation = ReservationSystem.objects.create(
            user=request.user,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            seats=seats,
            status="confirmed",
        )

    total_price = 0
    for cartitem in items:
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
        total_price += (base + extra) * cartitem.quantity

    order = Order.objects.create(
        user=request.user,
        delivery_type=delivery_type,
        delivery_address=delivery_address,
        reservation=reservation,
        status="confirmed",
        total_price=total_price,
    )

    for cartitem in items:
        base = cartitem.menu.price
        extra = 0
        opts_text = cartitem.options_text or ""
        if cartitem.options_text and cartitem.option is None:
            opt_names = [s.strip() for s in cartitem.options_text.split(",")]
            extras = MenuCustomizationOption.objects.filter(
                menu=cartitem.menu, option_name__in=opt_names
            ).values_list("extra_price", flat=True)
            extra = sum(extras)
        elif cartitem.option:
            extra = cartitem.option.extra_price
            opts_text = cartitem.option.option_name
        unit_price = base + extra
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

    qr = qrcode.make(f"http://localhost:8000/menu?from=order_{order.id}")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    order.qr_data = base64.b64encode(buf.getvalue()).decode()
    order.save(update_fields=["qr_data"])

    payment_type = request.POST.get("payment_type", "card")

    if payment_type == "cash":
        payment_method, pm_created = PaymentMethod.objects.get_or_create(
            user=request.user,
            method_type="Cash on Restaurant",
        )
        Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=total_price,
            status="confirmed",
        )
        cart.delete()
        messages.success(request, _("Order placed! Pay with cash when you arrive."))
        return redirect("order_history")

    payment_method_id = request.POST.get("payment_method_id")
    card_number = request.POST.get("card_number", "").strip()

    if payment_method_id:
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id, user=request.user)
    elif card_number:
        digits = "".join(c for c in card_number if c.isdigit())
        if len(digits) < 13:
            messages.error(request, _("Invalid card number."))
            order.delete()
            return redirect("checkout")
        last_four = digits[-4:]
        method_type = f"•••• {last_four}"
        payment_method = PaymentMethod.objects.create(
            user=request.user,
            method_type=method_type,
        )
    else:
        messages.error(request, _("Please select or enter a payment method."))
        order.delete()
        return redirect("checkout")

    Payment.objects.create(
        order=order,
        payment_method=payment_method,
        amount=total_price,
        status="completed",
        paid_at=timezone.now(),
    )

    cart.delete()

    messages.success(request, _("Payment successful! Your order has been placed."))
    return redirect("order_history")


@login_required(login_url="login")
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("orderitem_set__menu__item", "orderitem_set__option", "payment__payment_method"),
        id=order_id,
        user=request.user,
    )
    items = order.orderitem_set.all()
    for item in items:
        item.line_total = item.unit_price * item.quantity
        item.menu_options_text = item.options_text if item.options_text else (item.option.option_name if item.option else "")
    return render(request, "orders/order_detail.html", {"order": order, "items": items})


@login_required(login_url="login")
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/order_history.html", {"orders": orders})
