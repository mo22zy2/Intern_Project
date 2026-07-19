from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Cart, CartItem, Menu, MenuCustomizationOption
from ..schemas import CartItemCreate, CartItemUpdate, CartOut, CartItemOut, MessageResponse
from ..auth_utils import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


def _get_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _cart_item_to_out(ci: CartItem, db: Session = None) -> dict:
    extra = 0.0
    if ci.options_text and db:
        option_names = [name.strip() for name in ci.options_text.split(",") if name.strip()]
        extras = db.query(MenuCustomizationOption.extra_price).filter(
            MenuCustomizationOption.menu_id == ci.menu_id,
            MenuCustomizationOption.option_name.in_(option_names),
        ).all()
        extra = sum(e[0] for e in extras)
    return {
        "id": ci.id,
        "menu_id": ci.menu_id,
        "item_name": ci.menu.item_ref.item_name if ci.menu and ci.menu.item_ref else "",
        "price": ci.menu.price if ci.menu else 0,
        "option_name": None,
        "extra_price": extra,
        "quantity": ci.quantity,
        "options_text": ci.options_text or "",
    }


@router.get("/")
def view_cart(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = _get_cart(user.id, db)
    items = []
    total = 0.0
    for ci in cart.items:
        item_out = _cart_item_to_out(ci, db)
        extra = item_out["extra_price"]
        total += (ci.menu.price + extra) * ci.quantity
        items.append(item_out)
    return {"id": cart.id, "items": items, "total": round(total, 2)}


@router.post("/add/{item_id}", response_model=MessageResponse, status_code=201)
def add_to_cart(
    item_id: int,
    body: CartItemCreate = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    menu = db.query(Menu).filter(Menu.id == item_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu item not found")

    cart = _get_cart(user.id, db)
    option_ids = body.option_ids if body else []

    options_text = ""
    if option_ids:
        options = db.query(MenuCustomizationOption).filter(
            MenuCustomizationOption.id.in_(option_ids),
            MenuCustomizationOption.menu_id == item_id,
        ).all()
        names = [o.option_name for o in options]
        options_text = ", ".join(names) if names else ""

    existing = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.menu_id == item_id,
            CartItem.options_text == options_text,
        )
        .first()
    )
    if existing:
        existing.quantity += body.quantity if body else 1
    else:
        ci = CartItem(
            cart_id=cart.id,
            menu_id=item_id,
            option_id=None,
            quantity=body.quantity if body else 1,
            options_text=options_text,
        )
        db.add(ci)
    db.commit()
    return MessageResponse(message="Item added to cart")


@router.post("/add-checkout/{item_id}", response_model=MessageResponse, status_code=201)
def add_to_cart_and_checkout(
    item_id: int,
    body: CartItemCreate = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    add_to_cart(item_id, body, user, db)
    return MessageResponse(message="Item added and ready for checkout")


@router.put("/update/{item_id}", response_model=MessageResponse)
def update_cart_item(
    item_id: int,
    body: CartItemUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = _get_cart(user.id, db)
    ci = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not ci:
        raise HTTPException(status_code=404, detail="Item not in cart")
    if body.quantity <= 0:
        db.delete(ci)
    else:
        ci.quantity = body.quantity
    db.commit()
    return MessageResponse(message="Cart updated")


@router.delete("/remove/{item_id}", response_model=MessageResponse)
def remove_from_cart(
    item_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = _get_cart(user.id, db)
    ci = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not ci:
        raise HTTPException(status_code=404, detail="Item not in cart")
    db.delete(ci)
    db.commit()
    return MessageResponse(message="Item removed from cart")
