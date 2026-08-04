from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, time, datetime


# ----- Auth -----
class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    birth: Optional[date] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


# ----- User / Profile -----
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone: str
    birth: Optional[date] = None
    address: str = ""

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth: Optional[date] = None
    address: Optional[str] = None
    dark_mode: Optional[bool] = None
    locale: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


# ----- Menu -----
class MenuOptionOut(BaseModel):
    id: int
    option_name: str
    extra_price: float

    class Config:
        from_attributes = True


class MenuItemOut(BaseModel):
    id: int
    item_name: str
    category_name: str
    image_url: str
    price: float
    popularity_score: int
    available: bool
    customization_options: list[MenuOptionOut] = []

    class Config:
        from_attributes = True


# ----- Cart -----
class CartItemCreate(BaseModel):
    menu_id: Optional[int] = None
    option_ids: list[int] = []
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemOut(BaseModel):
    id: int
    menu_id: int
    item_name: str
    price: float
    option_name: Optional[str] = None
    extra_price: float = 0
    quantity: int
    options_text: str = ""

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    id: int
    items: list[CartItemOut] = []
    total: float = 0

    class Config:
        from_attributes = True


# ----- Order -----
class OrderItemCreate(BaseModel):
    menu_id: int
    option_id: Optional[int] = None
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    options_text: str = ""


class PlaceOrderRequest(BaseModel):
    delivery_type: str = "delivery"
    delivery_address: str = ""
    pickup_date: Optional[date] = None
    pickup_time: Optional[time] = None
    reservation_id: Optional[int] = None
    reservation_date: Optional[date] = None
    reservation_time: Optional[time] = None
    seats: Optional[int] = Field(default=None, gt=0)
    items: list[OrderItemCreate] = []
    payment_type: str = "card"
    payment_method_id: Optional[int] = None
    card_number: Optional[str] = None
    save_address: bool = False


class OrderItemOut(BaseModel):
    id: int
    menu_id: int
    item_name: str
    quantity: int
    unit_price: float
    options_text: str = ""

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    user_id: int
    delivery_type: str
    delivery_address: str
    order_number: int = 0
    status: str
    total_price: float
    created_at: datetime
    qr_data: Optional[str] = None
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


# ----- Reservation -----
class ReservationCreate(BaseModel):
    reservation_date: date
    reservation_time: time
    seats: int = Field(gt=0)


class ReservationUpdate(BaseModel):
    reservation_date: Optional[date] = None
    reservation_time: Optional[time] = None
    seats: Optional[int] = Field(default=None, gt=0)


class ReservationOut(BaseModel):
    id: int
    user_id: int
    reservation_date: date
    reservation_time: time
    seats: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Review -----
class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class ReviewOut(BaseModel):
    id: int
    user_id: int
    menu_id: int
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True


# ----- Payment -----
class PaymentMethodCreate(BaseModel):
    card_number: str
    cardholder_name: Optional[str] = None
    expiry: Optional[str] = None
    cvv: Optional[str] = None
    is_default: bool = False


class PaymentMethodOut(BaseModel):
    id: int
    method_type: str
    is_default: bool

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    status: str
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----- Admin -----
class CategoryCreate(BaseModel):
    category_name: str


class MenuItemCreate(BaseModel):
    item_name: str
    category_id: int
    price: float
    image_url: str = ""
    available: bool = True
    stock_count: int = 0


class CustomizationCreate(BaseModel):
    option_name: str
    extra_price: float = 0


class StatusUpdate(BaseModel):
    status: str


class InventoryUpdate(BaseModel):
    item_count: int = Field(ge=0)


class ReportQuery(BaseModel):
    type: str = "sales"
    days: int = 30


# ----- Generic -----
class MessageResponse(BaseModel):
    message: str
