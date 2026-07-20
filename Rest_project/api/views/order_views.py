from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..services import order_service


@login_required(login_url="login")
def checkout(request):
    data = order_service.get_checkout_data(request.user)
    if not data or not data["items"]:
        messages.error(request, _("Your cart is empty."))
        return redirect("view_cart")

    items = []
    for entry in data["items"]:
        cartitem = entry["item"]
        cartitem.unit_price = entry["unit_price"]
        cartitem.line_total = entry["line_total"]
        items.append(cartitem)

    card_methods = [pm for pm in data["payment_methods"] if not pm.method_type.startswith("Cash")]
    return render(request, "orders/checkout.html", {
        "cart_items": items,
        "subtotal": data["subtotal"],
        "card_methods": card_methods,
    })


@login_required(login_url="login")
def place_order(request):
    if request.method != "POST":
        return redirect("checkout")

    try:
        order_service.place_order(
            user=request.user,
            delivery_type=request.POST.get("delivery_type", "delivery"),
            delivery_address=request.POST.get("delivery_address", "").strip(),
            reservation_date=request.POST.get("reservation_date", "").strip(),
            reservation_time=request.POST.get("reservation_time", "").strip(),
            seats=request.POST.get("seats", "").strip(),
            payment_type=request.POST.get("payment_type", "card"),
            payment_method_id=request.POST.get("payment_method_id"),
            card_number=request.POST.get("card_number", "").strip(),
        )
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("checkout")

    messages.success(request, _("Your order has been placed."))
    return redirect("order_history")


@login_required(login_url="login")
def order_detail(request, order_id):
    order = order_service.get_order_detail(request.user, order_id)
    if not order:
        from django.http import Http404
        raise Http404("Order not found")
    items = order.orderitem_set.all()
    for item in items:
        item.line_total = item.unit_price * item.quantity
        item.menu_options_text = item.options_text if item.options_text else (item.option.option_name if item.option else "")
    return render(request, "orders/order_detail.html", {"order": order, "items": items})


@login_required(login_url="login")
def order_history(request):
    orders = order_service.get_user_orders(request.user)
    return render(request, "orders/order_history.html", {"orders": orders})
