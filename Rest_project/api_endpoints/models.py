from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Time, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "api_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_superuser = Column(Boolean, default=False)
    username = Column(String(150), unique=True, nullable=False)
    first_name = Column(String(150), default="")
    last_name = Column(String(150), default="")
    email = Column(String(254), default="")
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    date_joined = Column(DateTime, default=func.now())
    phone = Column(String(15), default="")
    birth = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())


class UserSettings(Base):
    __tablename__ = "api_usersettings"

    user_id = Column(Integer, ForeignKey("api_user.id"), primary_key=True)
    dark_mode = Column(Boolean, default=False)
    locale = Column(String(10), default="en")


class Category(Base):
    __tablename__ = "api_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), unique=True, nullable=False)

    menu_items = relationship("Menu", back_populates="category")


class Inventory(Base):
    __tablename__ = "api_inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(100), unique=True, nullable=False)
    item_count = Column(Integer, default=0)
    ordered = Column(Integer, default=0)

    menu_items = relationship("Menu", back_populates="item_ref")


class Menu(Base):
    __tablename__ = "api_menu"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("api_inventory.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("api_category.id"), nullable=False)
    image_url = Column(String(500), nullable=False, default="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZFcnA0ic2J7aKFnIbiQe_162HCFpokxlijmoaPNz07Q&s=10")
    price = Column(Float, nullable=False)
    popularity_score = Column(Integer, default=0)
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    item_ref = relationship("Inventory", back_populates="menu_items")
    category = relationship("Category", back_populates="menu_items")
    customization_options = relationship("MenuCustomizationOption", back_populates="menu")
    cart_items = relationship("CartItem", back_populates="menu")
    order_items = relationship("OrderItem", back_populates="menu")
    reviews = relationship("Review", back_populates="menu")


class MenuCustomizationOption(Base):
    __tablename__ = "api_menucustomizationoption"

    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_id = Column(Integer, ForeignKey("api_menu.id"), nullable=False)
    option_name = Column(String(100), nullable=False)
    extra_price = Column(Float, default=0)

    menu = relationship("Menu", back_populates="customization_options")


class Cart(Base):
    __tablename__ = "api_cart"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("api_user.id"), unique=True, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    items = relationship("CartItem", back_populates="cart")


class CartItem(Base):
    __tablename__ = "api_cartitem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("api_cart.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("api_menu.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("api_menucustomizationoption.id"), nullable=True)
    quantity = Column(Integer, default=1)
    options_text = Column(String(500), default="")

    cart = relationship("Cart", back_populates="items")
    menu = relationship("Menu", back_populates="cart_items")


class Order(Base):
    __tablename__ = "api_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("api_user.id"), nullable=False)
    delivery_type = Column(String(20), default="delivery")
    delivery_address = Column(Text, default="")
    reservation_id = Column(Integer, ForeignKey("api_reservationsystem.id"), nullable=True)
    status = Column(String(20), default="confirmed")
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    qr_data = Column(Text, nullable=True)

    items = relationship("OrderItem", back_populates="order")
    payment_rel = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "api_orderitem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("api_order.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("api_menu.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("api_menucustomizationoption.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    options_text = Column(String(500), default="")

    order = relationship("Order", back_populates="items")
    menu = relationship("Menu", back_populates="order_items")


class ReservationSystem(Base):
    __tablename__ = "api_reservationsystem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("api_user.id"), nullable=False)
    reservation_date = Column(Date, nullable=False)
    reservation_time = Column(Time, nullable=False)
    seats = Column(Integer, nullable=False)
    status = Column(String(20), default="confirmed")
    created_at = Column(DateTime, default=func.now())


class Review(Base):
    __tablename__ = "api_review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("api_user.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("api_menu.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "menu_id"),
    )

    menu = relationship("Menu", back_populates="reviews")


class PaymentMethod(Base):
    __tablename__ = "api_paymentmethod"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("api_user.id"), nullable=False)
    method_type = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)


class Payment(Base):
    __tablename__ = "api_payment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("api_order.id"), unique=True, nullable=False)
    payment_method_id = Column(Integer, ForeignKey("api_paymentmethod.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    paid_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="payment_rel")
    payment_method = relationship("PaymentMethod")
