import pytest
from datetime import date, time
from pydantic import ValidationError

from api_endpoints.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserOut,
    ProfileUpdate,
    ChangePasswordRequest,
    MenuOptionOut,
    MenuItemOut,
    CartItemCreate,
    CartItemUpdate,
    CartItemOut,
    CartOut,
    OrderItemCreate,
    PlaceOrderRequest,
    ReservationCreate,
    ReservationUpdate,
    ReviewCreate,
    PaymentMethodCreate,
    MessageResponse,
)


# ========== Auth Schemas ==========


class TestRegisterRequest:
    def test_valid_full_data(self):
        data = RegisterRequest(
            username="alice",
            password="secret",
            confirm_password="secret",
            email="a@b.com",
            first_name="Alice",
            last_name="Smith",
            phone="123456789",
            birth=date(1990, 1, 1),
        )
        assert data.username == "alice"
        assert data.password == "secret"
        assert data.confirm_password == "secret"
        assert data.email == "a@b.com"
        assert data.first_name == "Alice"
        assert data.last_name == "Smith"
        assert data.phone == "123456789"
        assert data.birth == date(1990, 1, 1)

    def test_defaults(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="bob", password="pass")

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            RegisterRequest()

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                username="u", confirm_password="c", email="e@e.com",
                first_name="F", last_name="L", phone="0", birth=date(2000, 1, 1),
            )

    def test_field_types(self):
        data = RegisterRequest(
            username="u", password="p", confirm_password="c", email="e@e.com",
            first_name="F", last_name="L", phone="0", birth=date(2000, 1, 1),
        )
        assert isinstance(data.username, str)
        assert isinstance(data.password, str)
        assert isinstance(data.confirm_password, str)
        assert isinstance(data.email, str)
        assert isinstance(data.first_name, str)
        assert isinstance(data.last_name, str)
        assert isinstance(data.phone, str)
        assert isinstance(data.birth, date)


class TestLoginRequest:
    def test_valid(self):
        data = LoginRequest(username="alice", password="secret")
        assert data.username == "alice"
        assert data.password == "secret"

    def test_missing_username(self):
        with pytest.raises(ValidationError):
            LoginRequest(password="p")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="u")

    def test_empty_strings(self):
        data = LoginRequest(username="", password="")
        assert data.username == ""
        assert data.password == ""

    def test_field_types(self):
        data = LoginRequest(username="u", password="p")
        assert isinstance(data.username, str)
        assert isinstance(data.password, str)


class TestTokenResponse:
    def test_valid_full(self):
        data = TokenResponse(
            access_token="abc123",
            user_id=1,
            username="alice",
        )
        assert data.access_token == "abc123"
        assert data.token_type == "bearer"
        assert data.user_id == 1
        assert data.username == "alice"

    def test_token_type_default(self):
        data = TokenResponse(access_token="t", user_id=42, username="u")
        assert data.token_type == "bearer"

    def test_token_type_custom(self):
        data = TokenResponse(
            access_token="t", token_type="Bearer", user_id=42, username="u"
        )
        assert data.token_type == "Bearer"

    def test_missing_access_token(self):
        with pytest.raises(ValidationError):
            TokenResponse(user_id=1, username="u")

    def test_missing_user_id(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="t", username="u")

    def test_missing_username(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="t", user_id=1)

    def test_user_id_non_integer(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="t", user_id="abc", username="u")

    def test_field_types(self):
        data = TokenResponse(access_token="t", user_id=5, username="u")
        assert isinstance(data.access_token, str)
        assert isinstance(data.token_type, str)
        assert isinstance(data.user_id, int)
        assert isinstance(data.username, str)


# ========== Profile Schemas ==========


class TestUserOut:
    def test_valid(self):
        data = UserOut(
            id=1,
            username="alice",
            email="a@b.com",
            first_name="Alice",
            last_name="Smith",
            phone="123",
        )
        assert data.id == 1
        assert data.username == "alice"
        assert data.email == "a@b.com"
        assert data.first_name == "Alice"
        assert data.last_name == "Smith"
        assert data.phone == "123"
        assert data.birth is None

    def test_with_birth(self):
        d = date(1999, 1, 15)
        data = UserOut(
            id=2,
            username="bob",
            email="b@b.com",
            first_name="Bob",
            last_name="Jones",
            phone="456",
            birth=d,
        )
        assert data.birth == d

    def test_birth_as_string(self):
        data = UserOut(
            id=3,
            username="c",
            email="c@c.com",
            first_name="C",
            last_name="D",
            phone="0",
            birth="2000-06-15",
        )
        assert data.birth == date(2000, 6, 15)

    def test_missing_required_id(self):
        with pytest.raises(ValidationError):
            UserOut(username="u", email="e@e.com", first_name="F", last_name="L", phone="0")

    def test_missing_required_username(self):
        with pytest.raises(ValidationError):
            UserOut(id=1, email="e@e.com", first_name="F", last_name="L", phone="0")

    def test_field_types(self):
        data = UserOut(id=1, username="u", email="e", first_name="F", last_name="L", phone="0")
        assert isinstance(data.id, int)
        assert isinstance(data.username, str)
        assert isinstance(data.email, str)
        assert isinstance(data.first_name, str)
        assert isinstance(data.last_name, str)
        assert isinstance(data.phone, str)
        assert data.birth is None or isinstance(data.birth, date)

    def test_from_attributes_config(self):
        assert UserOut.model_config.get("from_attributes") is True


class TestProfileUpdate:
    def test_all_none(self):
        data = ProfileUpdate()
        assert data.first_name is None
        assert data.last_name is None
        assert data.email is None
        assert data.phone is None
        assert data.birth is None
        assert data.dark_mode is None
        assert data.locale is None

    def test_partial(self):
        data = ProfileUpdate(first_name="Alice", email="a@b.com")
        assert data.first_name == "Alice"
        assert data.email == "a@b.com"
        assert data.last_name is None
        assert data.phone is None
        assert data.birth is None
        assert data.dark_mode is None
        assert data.locale is None

    def test_all_fields(self):
        d = date(1995, 5, 10)
        data = ProfileUpdate(
            first_name="X",
            last_name="Y",
            email="x@y.com",
            phone="999",
            birth=d,
            dark_mode=True,
            locale="en",
        )
        assert data.first_name == "X"
        assert data.last_name == "Y"
        assert data.email == "x@y.com"
        assert data.phone == "999"
        assert data.birth == d
        assert data.dark_mode is True
        assert data.locale == "en"

    def test_birth_string_coercion(self):
        data = ProfileUpdate(birth="1995-05-10")
        assert data.birth == date(1995, 5, 10)

    def test_invalid_birth_type(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(birth="not-a-date")

    def test_dark_mode(self):
        data = ProfileUpdate(dark_mode=False)
        assert data.dark_mode is False

    def test_locale(self):
        data = ProfileUpdate(locale="fr")
        assert data.locale == "fr"


class TestChangePasswordRequest:
    def test_valid(self):
        data = ChangePasswordRequest(
            old_password="old", new_password="new", confirm_password="new"
        )
        assert data.old_password == "old"
        assert data.new_password == "new"
        assert data.confirm_password == "new"

    def test_missing_old(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(new_password="new", confirm_password="new")

    def test_missing_new(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password="old", confirm_password="old")

    def test_missing_confirm_password(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password="old", new_password="new")

    def test_both_empty(self):
        data = ChangePasswordRequest(old_password="", new_password="", confirm_password="")
        assert data.old_password == ""
        assert data.new_password == ""
        assert data.confirm_password == ""


# ========== Menu Schemas ==========


class TestMenuOptionOut:
    def test_valid(self):
        data = MenuOptionOut(id=1, option_name="Extra Cheese", extra_price=2.5)
        assert data.id == 1
        assert data.option_name == "Extra Cheese"
        assert data.extra_price == 2.5

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            MenuOptionOut(id=1, option_name="X")

    def test_price_as_int(self):
        data = MenuOptionOut(id=1, option_name="X", extra_price=3)
        assert data.extra_price == 3.0

    def test_field_types(self):
        data = MenuOptionOut(id=1, option_name="N", extra_price=1.0)
        assert isinstance(data.id, int)
        assert isinstance(data.option_name, str)
        assert isinstance(data.extra_price, float)

    def test_from_attributes_config(self):
        assert MenuOptionOut.model_config.get("from_attributes") is True


class TestMenuItemOut:
    def test_valid_full(self):
        option = MenuOptionOut(id=1, option_name="Cheese", extra_price=1.0)
        data = MenuItemOut(
            id=10,
            item_name="Pizza",
            category_name="Main",
            image_url="http://img.com/p.jpg",
            price=12.99,
            popularity_score=5,
            available=True,
            customization_options=[option],
        )
        assert data.id == 10
        assert data.item_name == "Pizza"
        assert data.category_name == "Main"
        assert data.image_url == "http://img.com/p.jpg"
        assert data.price == 12.99
        assert data.popularity_score == 5
        assert data.available is True
        assert len(data.customization_options) == 1
        assert data.customization_options[0].option_name == "Cheese"

    def test_empty_customization_options_default(self):
        data = MenuItemOut(
            id=1,
            item_name="Burger",
            category_name="Main",
            image_url="http://img.com/b.jpg",
            price=9.99,
            popularity_score=3,
            available=False,
        )
        assert data.customization_options == []

    def test_price_as_int(self):
        data = MenuItemOut(
            id=1,
            item_name="N",
            category_name="C",
            image_url="u",
            price=10,
            popularity_score=0,
            available=True,
        )
        assert data.price == 10.0

    def test_popularity_score_zero(self):
        data = MenuItemOut(
            id=1,
            item_name="N",
            category_name="C",
            image_url="u",
            price=1.0,
            popularity_score=0,
            available=True,
        )
        assert data.popularity_score == 0

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            MenuItemOut(
                item_name="N",
                category_name="C",
                image_url="u",
                price=1.0,
                popularity_score=1,
                available=True,
            )

    def test_missing_price(self):
        with pytest.raises(ValidationError):
            MenuItemOut(
                id=1,
                item_name="N",
                category_name="C",
                image_url="u",
                popularity_score=1,
                available=True,
            )

    def test_field_types(self):
        data = MenuItemOut(
            id=1, item_name="N", category_name="C", image_url="u",
            price=1.0, popularity_score=1, available=True,
        )
        assert isinstance(data.id, int)
        assert isinstance(data.item_name, str)
        assert isinstance(data.category_name, str)
        assert isinstance(data.image_url, str)
        assert isinstance(data.price, float)
        assert isinstance(data.popularity_score, int)
        assert isinstance(data.available, bool)
        assert isinstance(data.customization_options, list)

    def test_from_attributes_config(self):
        assert MenuItemOut.model_config.get("from_attributes") is True


# ========== Cart Schemas ==========


class TestCartItemCreate:
    def test_valid_minimal(self):
        data = CartItemCreate(menu_id=1)
        assert data.menu_id == 1
        assert data.option_ids == []
        assert data.quantity == 1

    def test_valid_full(self):
        data = CartItemCreate(menu_id=2, option_ids=[5, 6], quantity=3)
        assert data.menu_id == 2
        assert data.option_ids == [5, 6]
        assert data.quantity == 3

    def test_missing_menu_id(self):
        data = CartItemCreate()
        assert data.menu_id is None

    def test_quantity_default(self):
        data = CartItemCreate(menu_id=1)
        assert data.quantity == 1

    def test_quantity_zero(self):
        with pytest.raises(ValidationError):
            CartItemCreate(menu_id=1, quantity=0)

    def test_field_types(self):
        data = CartItemCreate(menu_id=1)
        assert isinstance(data.menu_id, int)
        assert isinstance(data.option_ids, list)
        assert isinstance(data.quantity, int)


class TestCartItemUpdate:
    def test_valid(self):
        data = CartItemUpdate(quantity=3)
        assert data.quantity == 3

    def test_zero_quantity(self):
        with pytest.raises(ValidationError):
            CartItemUpdate(quantity=0)

    def test_missing_quantity(self):
        with pytest.raises(ValidationError):
            CartItemUpdate()

    def test_non_integer(self):
        with pytest.raises(ValidationError):
            CartItemUpdate(quantity="abc")

    def test_field_type(self):
        data = CartItemUpdate(quantity=5)
        assert isinstance(data.quantity, int)


class TestCartItemOut:
    def test_valid_full(self):
        data = CartItemOut(
            id=1,
            menu_id=10,
            item_name="Pizza",
            price=12.99,
            option_name="Extra Cheese",
            extra_price=1.5,
            quantity=2,
            options_text="Extra Cheese: +1.50",
        )
        assert data.id == 1
        assert data.menu_id == 10
        assert data.item_name == "Pizza"
        assert data.price == 12.99
        assert data.option_name == "Extra Cheese"
        assert data.extra_price == 1.5
        assert data.quantity == 2
        assert data.options_text == "Extra Cheese: +1.50"

    def test_defaults(self):
        data = CartItemOut(
            id=1, menu_id=10, item_name="Burger", price=9.99, quantity=1,
        )
        assert data.option_name is None
        assert data.extra_price == 0.0
        assert data.options_text == ""

    def test_missing_required_id(self):
        with pytest.raises(ValidationError):
            CartItemOut(menu_id=1, item_name="N", price=1.0, quantity=1)

    def test_missing_required_menu_id(self):
        with pytest.raises(ValidationError):
            CartItemOut(id=1, item_name="N", price=1.0, quantity=1)

    def test_missing_required_item_name(self):
        with pytest.raises(ValidationError):
            CartItemOut(id=1, menu_id=1, price=1.0, quantity=1)

    def test_missing_required_price(self):
        with pytest.raises(ValidationError):
            CartItemOut(id=1, menu_id=1, item_name="N", quantity=1)

    def test_missing_required_quantity(self):
        with pytest.raises(ValidationError):
            CartItemOut(id=1, menu_id=1, item_name="N", price=1.0)

    def test_field_types(self):
        data = CartItemOut(id=1, menu_id=1, item_name="N", price=1.0, quantity=1)
        assert isinstance(data.id, int)
        assert isinstance(data.menu_id, int)
        assert isinstance(data.item_name, str)
        assert isinstance(data.price, float)
        assert isinstance(data.quantity, int)
        assert isinstance(data.options_text, str)

    def test_extra_price_type_when_set(self):
        data = CartItemOut(id=1, menu_id=1, item_name="N", price=1.0, quantity=1, extra_price=2.5)
        assert isinstance(data.extra_price, float)

    def test_price_coercion(self):
        data = CartItemOut(id=1, menu_id=1, item_name="N", price=5, quantity=1)
        assert data.price == 5.0

    def test_from_attributes_config(self):
        assert CartItemOut.model_config.get("from_attributes") is True


class TestCartOut:
    def test_valid(self):
        items = [
            CartItemOut(id=1, menu_id=1, item_name="A", price=5.0, quantity=2),
        ]
        data = CartOut(id=1, items=items, total=10.0)
        assert data.id == 1
        assert len(data.items) == 1
        assert data.items[0].item_name == "A"
        assert data.total == 10.0

    def test_defaults(self):
        data = CartOut(id=1)
        assert data.items == []
        assert data.total == 0.0

    def test_missing_id(self):
        with pytest.raises(ValidationError):
            CartOut()

    def test_total_coercion(self):
        data = CartOut(id=1, total=10)
        assert data.total == 10.0

    def test_field_types(self):
        data = CartOut(id=1)
        assert isinstance(data.id, int)
        assert isinstance(data.items, list)

    def test_total_type_when_set(self):
        data = CartOut(id=1, total=5.5)
        assert isinstance(data.total, float)

    def test_from_attributes_config(self):
        assert CartOut.model_config.get("from_attributes") is True


# ========== Order Schemas ==========


class TestOrderItemCreate:
    def test_valid_full(self):
        data = OrderItemCreate(
            menu_id=1, option_id=2, quantity=3, unit_price=10.99,
            options_text="Cheese",
        )
        assert data.menu_id == 1
        assert data.option_id == 2
        assert data.quantity == 3
        assert data.unit_price == 10.99
        assert data.options_text == "Cheese"

    def test_defaults(self):
        data = OrderItemCreate(menu_id=1, quantity=2, unit_price=5.0)
        assert data.option_id is None
        assert data.options_text == ""

    def test_missing_menu_id(self):
        with pytest.raises(ValidationError):
            OrderItemCreate(quantity=1, unit_price=1.0)

    def test_missing_quantity(self):
        with pytest.raises(ValidationError):
            OrderItemCreate(menu_id=1, unit_price=1.0)

    def test_missing_unit_price(self):
        with pytest.raises(ValidationError):
            OrderItemCreate(menu_id=1, quantity=1)

    def test_field_types(self):
        data = OrderItemCreate(menu_id=1, quantity=1, unit_price=1.0)
        assert isinstance(data.menu_id, int)
        assert isinstance(data.quantity, int)
        assert isinstance(data.unit_price, float)
        assert isinstance(data.options_text, str)

    def test_price_coercion(self):
        data = OrderItemCreate(menu_id=1, quantity=1, unit_price=5)
        assert data.unit_price == 5.0


class TestPlaceOrderRequest:
    def test_valid_full(self):
        items = [OrderItemCreate(menu_id=1, quantity=2, unit_price=5.0)]
        data = PlaceOrderRequest(
            delivery_type="pickup",
            delivery_address="123 St",
            reservation_id=42,
            items=items,
        )
        assert data.delivery_type == "pickup"
        assert data.delivery_address == "123 St"
        assert data.reservation_id == 42
        assert len(data.items) == 1

    def test_defaults(self):
        items = [OrderItemCreate(menu_id=1, quantity=1, unit_price=1.0)]
        data = PlaceOrderRequest(items=items)
        assert data.delivery_type == "delivery"
        assert data.delivery_address == ""
        assert data.reservation_id is None

    def test_missing_items(self):
        data = PlaceOrderRequest()
        assert data.items == []

    def test_empty_items_list(self):
        data = PlaceOrderRequest(items=[])
        assert data.items == []

    def test_field_types(self):
        data = PlaceOrderRequest(items=[])
        assert isinstance(data.delivery_type, str)
        assert isinstance(data.delivery_address, str)
        assert isinstance(data.items, list)


# ========== Reservation Schemas ==========


class TestReservationCreate:
    def test_valid(self):
        data = ReservationCreate(
            reservation_date=date(2025, 12, 25),
            reservation_time=time(18, 30),
            seats=4,
        )
        assert data.reservation_date == date(2025, 12, 25)
        assert data.reservation_time == time(18, 30)
        assert data.seats == 4

    def test_missing_date(self):
        with pytest.raises(ValidationError):
            ReservationCreate(reservation_time=time(12, 0), seats=2)

    def test_missing_time(self):
        with pytest.raises(ValidationError):
            ReservationCreate(reservation_date=date.today(), seats=2)

    def test_missing_seats(self):
        with pytest.raises(ValidationError):
            ReservationCreate(
                reservation_date=date.today(), reservation_time=time(12, 0)
            )

    def test_date_string_coercion(self):
        data = ReservationCreate(
            reservation_date="2025-12-25",
            reservation_time="18:30",
            seats=4,
        )
        assert data.reservation_date == date(2025, 12, 25)
        assert data.reservation_time == time(18, 30)

    def test_field_types(self):
        data = ReservationCreate(
            reservation_date=date.today(),
            reservation_time=time(12, 0),
            seats=2,
        )
        assert isinstance(data.reservation_date, date)
        assert isinstance(data.reservation_time, time)
        assert isinstance(data.seats, int)


class TestReservationUpdate:
    def test_all_none(self):
        data = ReservationUpdate()
        assert data.reservation_date is None
        assert data.reservation_time is None
        assert data.seats is None

    def test_partial_date_only(self):
        data = ReservationUpdate(reservation_date=date(2025, 6, 1))
        assert data.reservation_date == date(2025, 6, 1)
        assert data.reservation_time is None
        assert data.seats is None

    def test_partial_time_only(self):
        data = ReservationUpdate(reservation_time=time(14, 0))
        assert data.reservation_date is None
        assert data.reservation_time == time(14, 0)
        assert data.seats is None

    def test_partial_seats_only(self):
        data = ReservationUpdate(seats=6)
        assert data.reservation_date is None
        assert data.reservation_time is None
        assert data.seats == 6

    def test_all_fields(self):
        data = ReservationUpdate(
            reservation_date=date(2025, 7, 4),
            reservation_time=time(20, 0),
            seats=8,
        )
        assert data.reservation_date == date(2025, 7, 4)
        assert data.reservation_time == time(20, 0)
        assert data.seats == 8

    def test_string_coercion(self):
        data = ReservationUpdate(
            reservation_date="2025-07-04",
            reservation_time="20:00",
        )
        assert data.reservation_date == date(2025, 7, 4)
        assert data.reservation_time == time(20, 0)


# ========== Review Schemas ==========


class TestReviewCreate:
    def test_valid(self):
        data = ReviewCreate(rating=5, comment="Great!")
        assert data.rating == 5
        assert data.comment == "Great!"

    def test_default_comment(self):
        data = ReviewCreate(rating=3)
        assert data.comment == ""

    def test_min_rating(self):
        with pytest.raises(ValidationError):
            ReviewCreate(rating=0)

    def test_negative_rating(self):
        with pytest.raises(ValidationError):
            ReviewCreate(rating=-1)

    def test_missing_rating(self):
        with pytest.raises(ValidationError):
            ReviewCreate()

    def test_non_integer_rating(self):
        with pytest.raises(ValidationError):
            ReviewCreate(rating="good", comment="ok")

    def test_field_types(self):
        data = ReviewCreate(rating=4, comment="Nice")
        assert isinstance(data.rating, int)
        assert isinstance(data.comment, str)


# ========== Payment Schemas ==========


class TestPaymentMethodCreate:
    def test_valid(self):
        data = PaymentMethodCreate(
            card_number="4111111111111111",
            cardholder_name="Alice Smith",
            expiry="12/28",
            cvv="123",
        )
        assert data.card_number == "4111111111111111"
        assert data.cardholder_name == "Alice Smith"
        assert data.expiry == "12/28"
        assert data.cvv == "123"
        assert data.is_default is False

    def test_with_default(self):
        data = PaymentMethodCreate(
            card_number="4111111111111111",
            cardholder_name="Alice",
            expiry="12/28",
            cvv="123",
            is_default=True,
        )
        assert data.is_default is True

    def test_empty_strings(self):
        data = PaymentMethodCreate(
            card_number="", cardholder_name="", expiry="", cvv=""
        )
        assert data.card_number == ""
        assert data.cardholder_name == ""
        assert data.expiry == ""
        assert data.cvv == ""

    def test_missing_card_number(self):
        with pytest.raises(ValidationError):
            PaymentMethodCreate(cardholder_name="A", expiry="12/28", cvv="123")

    def test_field_types(self):
        data = PaymentMethodCreate(
            card_number="1", cardholder_name="A", expiry="E", cvv="C"
        )
        assert isinstance(data.card_number, str)
        assert isinstance(data.cardholder_name, str)
        assert isinstance(data.expiry, str)
        assert isinstance(data.cvv, str)
        assert isinstance(data.is_default, bool)


# ========== Generic Schemas ==========


class TestMessageResponse:
    def test_valid(self):
        data = MessageResponse(message="Success")
        assert data.message == "Success"

    def test_empty_message(self):
        data = MessageResponse(message="")
        assert data.message == ""

    def test_missing_message(self):
        with pytest.raises(ValidationError):
            MessageResponse()

    def test_non_string_message(self):
        with pytest.raises(ValidationError):
            MessageResponse(message=123)

    def test_field_type(self):
        data = MessageResponse(message="ok")
        assert isinstance(data.message, str)
