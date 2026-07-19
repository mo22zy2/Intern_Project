from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import Cart, CartItem, Menu, MenuCustomizationOption


def _add_item_to_cart(user, menu, quantity, option_ids):
    cart, _ = Cart.objects.get_or_create(user=user)

    if option_ids:
        options = MenuCustomizationOption.objects.filter(id__in=option_ids, menu=menu)
        names = []
        extra = 0
        for o in options:
            names.append(o.option_name)
            extra += o.extra_price
        options_text = ", ".join(names) if names else ""
    else:
        options_text = ""
        extra = 0

    existing = CartItem.objects.filter(cart=cart, menu=menu, options_text=options_text, option=None).first()
    if existing:
        existing.quantity += quantity
        existing.save()
    else:
        CartItem.objects.create(
            cart=cart,
            menu=menu,
            option=None,
            quantity=quantity,
            options_text=options_text,
        )

    return extra


@login_required(login_url="login")
def add_to_cart(request, item_id):
    menu = get_object_or_404(Menu, id=item_id)
    quantity = int(request.POST.get("quantity", 1))
    option_ids = request.POST.getlist("options")
    _add_item_to_cart(request.user, menu, quantity, option_ids)
    messages.success(request, _("%(name)s added to cart.") % {"name": menu.item.item_name})
    return redirect("menu_detail", item_id=item_id)


@login_required(login_url="login")
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart).select_related(
        "menu__item", "menu__category", "option"
    )

    subtotal = 0
    for cartitem in items:
        base_cost = cartitem.menu.price
        extra = 0

        # Case 1: Comma-separated customization strings
        if cartitem.options_text and cartitem.option is None:
            # Clean the string names out into a flat list
            option_names = [
                name.strip() for name in cartitem.options_text.split(",") if name.strip()
            ]
            
            # FIXED: Added __in modifier to look up multiple names simultaneously
            extra_prices = MenuCustomizationOption.objects.filter(
                menu=cartitem.menu, 
                option_name__in=option_names  
            ).values_list("extra_price", flat=True)
            
            extra = sum(extra_prices)

        # Case 2: Single direct relation option
        elif cartitem.option:
            extra = cartitem.option.extra_price

        # FIXED: Pulled out of the conditional blocks so BOTH cases calculate totals
        cartitem.unit_price = base_cost + extra
        cartitem.line_total = cartitem.unit_price * cartitem.quantity
        subtotal += cartitem.line_total

    return render(
        request, "cart/cart.html", {"cart_items": items, "subtotal": subtotal}
    )
 

@login_required(login_url="login")
def update_cart_item(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    qty = int(request.POST.get("quantity", 1))
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return redirect("view_cart")


@login_required(login_url="login")
def add_to_cart_and_checkout(request, item_id):
    menu = get_object_or_404(Menu, id=item_id)
    quantity = int(request.POST.get("quantity", 1))
    option_ids = request.POST.getlist("options")
    _add_item_to_cart(request.user, menu, quantity, option_ids)
    return redirect("checkout")


@login_required(login_url="login")
def remove_from_cart(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    messages.info(request, _("Item removed from cart."))
    return redirect("view_cart")
