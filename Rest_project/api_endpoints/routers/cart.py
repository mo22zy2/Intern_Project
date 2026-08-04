from django.core.exceptions import ObjectDoesNotExist
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas import CartItemCreate, CartItemUpdate, CartOut, CartItemOut, MessageResponse
from ..auth_utils import get_current_user
from api.services import cart_service, menu_service

router = APIRouter(prefix="/cart", tags=["Cart"])


def _cart_item_to_out(ci) -> dict:
    return {
        "id": ci.id,
        "menu_id": ci.menu.id,
        "item_name": ci.menu.item.item_name,
        "price": ci.menu.price,
        "option_name": None,
        "extra_price": 0,
        "quantity": ci.quantity,
        "options_text": ci.options_text or "",
    }


@router.get("/")
def view_cart(
    user=Depends(get_current_user),
):
    cart = cart_service.get_or_create_cart(user)
    items_with_prices, subtotal = cart_service.get_cart_items_with_prices(cart)
    items = []
    for entry in items_with_prices:
        ci = entry["item"]
        out = _cart_item_to_out(ci)
        out["extra_price"] = entry["unit_price"] - ci.menu.price
        items.append(out)
    return {"id": cart.id, "items": items, "total": round(subtotal, 2)}


@router.post("/add/{item_id}", response_model=MessageResponse, status_code=201)
def add_to_cart(
    item_id: int,
    body: CartItemCreate = None,
    user=Depends(get_current_user),
):
    menu = menu_service.get_menu_item_by_id(item_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu item not found")

    quantity = body.quantity if body else 1
    option_ids = body.option_ids if body else []
    cart_service.add_item_to_cart(user, menu, quantity, option_ids)
    return MessageResponse(message="Item added to cart")


@router.post("/add-checkout/{item_id}", response_model=MessageResponse, status_code=201)
def add_to_cart_and_checkout(
    item_id: int,
    body: CartItemCreate = None,
    user=Depends(get_current_user),
):
    menu = menu_service.get_menu_item_by_id(item_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu item not found")
    quantity = body.quantity if body else 1
    option_ids = body.option_ids if body else []
    cart_service.add_item_to_cart(user, menu, quantity, option_ids)
    return MessageResponse(message="Item added and ready for checkout")


@router.put("/update/{item_id}", response_model=MessageResponse)
def update_cart_item(
    item_id: int,
    body: CartItemUpdate,
    user=Depends(get_current_user),
):
    cart = cart_service.get_or_create_cart(user)
    try:
        cart_service.update_cart_item_quantity(cart, item_id, body.quantity)
    except ObjectDoesNotExist:
        raise HTTPException(status_code=404, detail="Item not in cart")
    return MessageResponse(message="Cart updated")


@router.delete("/remove/{item_id}", response_model=MessageResponse)
def remove_from_cart(
    item_id: int,
    user=Depends(get_current_user),
):
    cart = cart_service.get_or_create_cart(user)
    try:
        cart_service.remove_cart_item(cart, item_id)
    except ObjectDoesNotExist:
        raise HTTPException(status_code=404, detail="Item not in cart")
    return MessageResponse(message="Item removed from cart")
