from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import Menu, CartItem
from ..services import cart_service


@login_required(login_url="login")
def add_to_cart(request, item_id):
    menu = get_object_or_404(Menu, id=item_id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1
        messages.error(request, _("Invalid quantity. Using quantity 1."))
    option_ids = request.POST.getlist("options")
    cart_service.add_item_to_cart(request.user, menu, quantity, option_ids)
    messages.success(request, _("%(name)s added to cart.") % {"name": menu.item.item_name})
    return redirect("menu_detail", item_id=item_id)


@login_required(login_url="login")
def view_cart(request):
    cart = cart_service.get_or_create_cart(request.user)
    items_with_prices, subtotal = cart_service.get_cart_items_with_prices(cart)
    cart_items = []
    for entry in items_with_prices:
        item = entry["item"]
        item.unit_price = entry["unit_price"]
        item.line_total = entry["line_total"]
        cart_items.append(item)
    return render(
        request, "cart/cart.html", {"cart_items": cart_items, "subtotal": subtotal}
    )


@login_required(login_url="login")
def update_cart_item(request, item_id):
    from ..models import Cart
    cart = get_object_or_404(Cart, user=request.user)
    try:
        qty = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        qty = 1
        messages.error(request, _("Invalid quantity. Using quantity 1."))
    try:
        cart_service.update_cart_item_quantity(cart, item_id, qty)
    except CartItem.DoesNotExist:
        pass
    return redirect("view_cart")


@login_required(login_url="login")
def add_to_cart_and_checkout(request, item_id):
    menu = get_object_or_404(Menu, id=item_id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1
        messages.error(request, _("Invalid quantity. Using quantity 1."))
    option_ids = request.POST.getlist("options")
    cart_service.add_item_to_cart(request.user, menu, quantity, option_ids)
    return redirect("checkout")


@login_required(login_url="login")
def remove_from_cart(request, item_id):
    from ..models import Cart
    cart = get_object_or_404(Cart, user=request.user)
    try:
        cart_service.remove_cart_item(cart, item_id)
        messages.info(request, _("Item removed from cart."))
    except CartItem.DoesNotExist:
        pass
    return redirect("view_cart")
