def _imports():
    from ..models import Cart, CartItem, Menu, MenuCustomizationOption
    return Cart, CartItem, Menu, MenuCustomizationOption


def get_or_create_cart(user):
    Cart, _, _, _ = _imports()
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def add_item_to_cart(user, menu, quantity, option_ids=None):
    Cart, CartItem, _, MenuCustomizationOption = _imports()
    cart = get_or_create_cart(user)
    option_ids = option_ids or []

    if option_ids:
        options = MenuCustomizationOption.objects.filter(id__in=option_ids, menu=menu)
        names = [o.option_name for o in options]
        options_text = ", ".join(names) if names else ""
    else:
        options_text = ""

    existing = CartItem.objects.filter(
        cart=cart, menu=menu, options_text=options_text, option=None
    ).first()
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


def get_cart_items_with_prices(cart):
    _, CartItem, _, MenuCustomizationOption = _imports()
    items = CartItem.objects.filter(cart=cart).select_related(
        "menu__item", "menu__category", "option"
    )
    subtotal = 0
    result = []
    for cartitem in items:
        base_cost = cartitem.menu.price
        extra = 0
        if cartitem.options_text and cartitem.option is None:
            option_names = [
                name.strip() for name in cartitem.options_text.split(",") if name.strip()
            ]
            extra_prices = MenuCustomizationOption.objects.filter(
                menu=cartitem.menu,
                option_name__in=option_names,
            ).values_list("extra_price", flat=True)
            extra = sum(extra_prices)
        elif cartitem.option:
            extra = cartitem.option.extra_price
        unit_price = base_cost + extra
        line_total = unit_price * cartitem.quantity
        subtotal += line_total
        result.append({
            "item": cartitem,
            "unit_price": unit_price,
            "line_total": line_total,
        })
    return result, subtotal


def update_cart_item_quantity(cart, item_id, quantity):
    _, CartItem, _, _ = _imports()
    item = CartItem.objects.get(id=item_id, cart=cart)
    if quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    return item


def remove_cart_item(cart, item_id):
    _, CartItem, _, _ = _imports()
    item = CartItem.objects.get(id=item_id, cart=cart)
    item.delete()
