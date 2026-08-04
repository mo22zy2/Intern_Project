from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_endpoints.auth_utils import get_current_user, get_current_user_optional
from api_endpoints.main import app


def make_category(**kwargs):
    cat = SimpleNamespace()
    cat.id = kwargs.get("id", 1)
    cat.category_name = kwargs.get("name", "Main")
    return cat


def make_menu_item(**kwargs):
    item = SimpleNamespace()
    item.id = kwargs.get("id", 1)
    item.item = SimpleNamespace(item_name=kwargs.get("item_name", "Burger"))
    item.category = SimpleNamespace(category_name=kwargs.get("category_name", "Main"))
    item.image_url = kwargs.get("image_url", "https://example.com/img.jpg")
    item.price = kwargs.get("price", 12.99)
    item.popularity_score = kwargs.get("popularity_score", 95)
    item.available = kwargs.get("available", True)
    item.avg_rating = kwargs.get("avg_rating", None)
    item.menucustomizationoption_set = SimpleNamespace(all=lambda: [])
    return item


def make_cart_item(**kwargs):
    ci = SimpleNamespace()
    ci.id = kwargs.get("id", 1)
    ci.menu = SimpleNamespace(
        id=kwargs.get("menu_id", 1),
        price=kwargs.get("price", 10.0),
        item=SimpleNamespace(item_name=kwargs.get("item_name", "Burger")),
    )
    ci.quantity = kwargs.get("quantity", 2)
    ci.options_text = kwargs.get("options_text", "")
    return ci


def make_order(**kwargs):
    order = SimpleNamespace()
    order.id = kwargs.get("id", 1)
    order.user_id = kwargs.get("user_id", 1)
    order.delivery_type = kwargs.get("delivery_type", "delivery")
    order.delivery_address = kwargs.get("delivery_address", "123 Test St")
    order.order_number = kwargs.get("order_number", 1)
    order.status = kwargs.get("status", "pending")
    order.total_price = kwargs.get("total_price", 25.98)
    order.created_at = kwargs.get("created_at", datetime(2025, 6, 15, 12, 0, 0))
    order.qr_data = kwargs.get("qr_data", None)
    order.payment = kwargs.get("payment", None)
    order.orderitem_set = SimpleNamespace(all=lambda: [])
    return order


@pytest.fixture
def mock_user():
    return SimpleNamespace(
        id=1,
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone="1234567890",
        birth=None,
        address="",
        is_active=True,
        is_staff=False,
    )


@pytest.fixture
def client(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ───────────────────────────── Home ─────────────────────────────


class TestHomeRouter:
    def test_home_returns_popular_and_categories(self, client):
        featured = [make_menu_item(id=1, item_name="Burger", category_name="Main", avg_rating=4.5)]
        categories = [make_category(id=1, name="Main")]

        with patch(
            "api.services.menu_service.get_featured_items", return_value=featured
        ), patch(
            "api.services.menu_service.get_all_categories", return_value=categories
        ), patch(
            "api.services.menu_service.get_total_menu_items_count", return_value=10
        ), patch(
            "api.services.menu_service.get_total_categories_count", return_value=5
        ):
            response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "popular" in data
        assert "categories" in data
        assert len(data["popular"]) == 1
        assert data["popular"][0]["item_name"] == "Burger"
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Main"


# ───────────────────────────── Auth ─────────────────────────────


class TestAuthRouter:
    def test_register_success(self, client):
        user = SimpleNamespace(id=1, username="newuser")

        with patch("api.services.auth_service.validate_registration_data"), patch(
            "api.services.auth_service.register_user", return_value=user
        ), patch(
            "api_endpoints.routers.auth.create_access_token", return_value="test_token"
        ):
            response = client.post(
                "/auth/register",
                json={
                    "username": "newuser",
                    "password": "secret",
                    "confirm_password": "secret",
                    "email": "new@example.com",
                    "first_name": "New",
                    "last_name": "User",
                    "phone": "1234567890",
                    "birth": "2000-01-01",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["user_id"] == 1
        assert data["username"] == "newuser"

    def test_register_duplicate_username(self, client):
        with patch("api.services.auth_service.validate_registration_data"), patch(
            "api.services.auth_service.register_user",
            side_effect=ValueError("This username is taken. Try a different one."),
        ):
            response = client.post(
                "/auth/register",
                json={
                    "username": "takenuser",
                    "password": "secret",
                    "confirm_password": "secret",
                    "email": "taken@example.com",
                    "first_name": "Taken",
                    "last_name": "User",
                    "phone": "1234567890",
                    "birth": "2000-01-01",
                },
            )

        assert response.status_code == 400
        assert response.json()["detail"] is not None

    def test_login_success(self, client):
        user = SimpleNamespace(id=1, username="testuser")

        with patch(
            "api.services.auth_service.authenticate_user", return_value=user
        ), patch(
            "api_endpoints.routers.auth.create_access_token", return_value="test_token"
        ):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "correctpassword"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["username"] == "testuser"

    def test_login_invalid_credentials(self, client):
        with patch("api.services.auth_service.authenticate_user", return_value=None):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "wrongpassword"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"


# ───────────────────────────── Menu ─────────────────────────────


class TestMenuRouter:
    def test_menu_list(self, client):
        items = [make_menu_item(id=1, item_name="Pizza", category_name="Main", avg_rating=4.5)]
        categories = [make_category(id=1, name="Main")]

        with patch(
            "api.services.menu_service.get_available_menu_items", return_value=items
        ), patch(
            "api.services.menu_service.get_all_categories", return_value=categories
        ):
            response = client.get("/menu/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["item_name"] == "Pizza"

    def test_menu_detail_found(self, client):
        detail = {
            "item": make_menu_item(id=1, item_name="Pizza", category_name="Main"),
            "reviews": [],
            "avg_rating": 4.5,
            "user_review": None,
        }

        with patch("api.services.menu_service.get_menu_detail", return_value=detail):
            response = client.get("/menu/1")

        assert response.status_code == 200
        data = response.json()
        assert data["item_name"] == "Pizza"

    def test_menu_detail_not_found(self, client):
        with patch("api.services.menu_service.get_menu_detail", return_value=None):
            response = client.get("/menu/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Menu item not found"


# ───────────────────────────── Cart ─────────────────────────────


class TestCartRouter:
    def test_view_cart(self, client):
        cart = SimpleNamespace(id=1)
        ci = make_cart_item(id=1, menu_id=1, item_name="Burger", price=10.0, quantity=2)

        with patch(
            "api.services.cart_service.get_or_create_cart", return_value=cart
        ), patch(
            "api.services.cart_service.get_cart_items_with_prices",
            return_value=([{"item": ci, "unit_price": 10.0, "line_total": 20.0}], 20.0),
        ):
            response = client.get("/cart/")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["item_name"] == "Burger"
        assert data["total"] == 20.0

    def test_add_to_cart(self, client):
        menu = make_menu_item(id=1)

        with patch(
            "api.services.menu_service.get_menu_item_by_id", return_value=menu
        ), patch("api.services.cart_service.add_item_to_cart"):
            response = client.post(
                "/cart/add/1",
                json={"menu_id": 1, "option_ids": [], "quantity": 2},
            )

        assert response.status_code == 201
        assert response.json()["message"] == "Item added to cart"

    def test_add_to_cart_item_not_found(self, client):
        with patch("api.services.menu_service.get_menu_item_by_id", return_value=None):
            response = client.post(
                "/cart/add/999",
                json={"menu_id": 999, "option_ids": [], "quantity": 1},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Menu item not found"

    def test_remove_from_cart(self, client):
        cart = SimpleNamespace(id=1)

        with patch(
            "api.services.cart_service.get_or_create_cart", return_value=cart
        ), patch("api.services.cart_service.remove_cart_item"):
            response = client.delete("/cart/remove/1")

        assert response.status_code == 200
        assert response.json()["message"] == "Item removed from cart"


# ───────────────────────────── Order ─────────────────────────────


class TestOrderRouter:
    def test_checkout_empty_cart(self, client):
        with patch("api.services.order_service.get_checkout_data", return_value=None):
            response = client.get("/orders/checkout")

        assert response.status_code == 400
        assert response.json()["detail"] == "Cart is empty"

    def test_place_order(self, client):
        order = make_order(id=1, total_price=25.98)

        with patch("api_endpoints.routers.order._sync_cart_from_items"), patch(
            "api.services.order_service.place_order", return_value=order
        ):
            response = client.post(
                "/orders/checkout/place",
                json={
                    "delivery_type": "delivery",
                    "delivery_address": "123 Test St",
                    "payment_type": "cash",
                    "items": [
                        {
                            "menu_id": 1,
                            "quantity": 2,
                            "unit_price": 12.99,
                            "options_text": "",
                        }
                    ],
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "pending"

    def test_order_history(self, client):
        order = make_order(id=5, total_price=15.0)

        with patch("api.services.order_service.get_user_orders", return_value=[order]):
            response = client.get("/orders/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 5

    def test_order_detail_found(self, client):
        order = make_order(id=7, total_price=15.0)

        with patch(
            "api.services.order_service.get_order_detail", return_value=order
        ):
            response = client.get("/orders/7")

        assert response.status_code == 200
        assert response.json()["id"] == 7

    def test_order_detail_not_found(self, client):
        with patch("api.services.order_service.get_order_detail", return_value=None):
            response = client.get("/orders/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"


# ───────────────────────────── Reservation ─────────────────────────────


class TestReservationRouter:
    def test_make_reservation(self, client):
        with patch("api.services.reservation_service.create_reservation"):
            response = client.post(
                "/reservations/new",
                json={
                    "reservation_date": "2099-12-31",
                    "reservation_time": "14:00:00",
                    "seats": 4,
                },
            )

        assert response.status_code == 201
        assert response.json()["message"] == "Reservation created successfully"

    def test_make_reservation_past_date(self, client):
        with patch(
            "api.services.reservation_service.create_reservation",
            side_effect=ValueError("Reservation cannot be in the past"),
        ):
            response = client.post(
                "/reservations/new",
                json={
                    "reservation_date": "2020-01-01",
                    "reservation_time": "12:00:00",
                    "seats": 4,
                },
            )

        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()


# ───────────────────────────── Profile ─────────────────────────────


class TestProfileRouter:
    def test_get_profile(self, client, mock_user):
        settings = SimpleNamespace(dark_mode=False, locale="en")

        with patch(
            "api.services.profile_service.get_profile_data",
            return_value={"user": mock_user, "settings": settings},
        ), patch("api.models.Review.objects") as review_objects, patch(
            "api.models.PaymentMethod.objects"
        ) as pm_objects:
            review_objects.filter.return_value.order_by.return_value = []
            pm_objects.filter.return_value = []

            response = client.get("/profile/")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"

    def test_edit_profile(self, client):
        with patch("api.services.profile_service.update_profile") as mock_update:
            response = client.put(
                "/profile/edit",
                json={
                    "first_name": "Updated",
                    "last_name": "Name",
                    "email": "updated@example.com",
                    "phone": "0987654321",
                },
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Profile updated successfully"
        assert mock_update.call_args.kwargs["first_name"] == "Updated"
        assert mock_update.call_args.kwargs["last_name"] == "Name"
        assert mock_update.call_args.kwargs["email"] == "updated@example.com"
        assert mock_update.call_args.kwargs["phone"] == "0987654321"

    def test_change_password(self, client):
        with patch("api.services.auth_service.change_password"):
            response = client.put(
                "/profile/change-password",
                json={
                    "old_password": "oldpass",
                    "new_password": "newpass",
                    "confirm_password": "newpass",
                },
            )

        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"


# ───────────────────────────── Review ─────────────────────────────


class TestReviewRouter:
    def test_add_review(self, client):
        menu = make_menu_item(id=1)

        with patch(
            "api.services.menu_service.get_menu_item_by_id", return_value=menu
        ), patch("api.services.review_service.add_review"):
            response = client.post(
                "/reviews/add/1",
                json={"rating": 5, "comment": "Excellent!"},
            )

        assert response.status_code == 201
        assert response.json()["message"] == "Review added successfully"

    def test_add_review_duplicate(self, client):
        menu = make_menu_item(id=1)

        with patch(
            "api.services.menu_service.get_menu_item_by_id", return_value=menu
        ), patch(
            "api.services.review_service.add_review",
            side_effect=ValueError("You already reviewed this item"),
        ):
            response = client.post(
                "/reviews/add/1",
                json={"rating": 4, "comment": "Good"},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "You already reviewed this item"

    def test_delete_review(self, client):
        review = SimpleNamespace(id=1)

        with patch(
            "api.services.review_service.get_review", return_value=review
        ), patch("api.services.review_service.delete_review"):
            response = client.delete("/reviews/1/delete")

        assert response.status_code == 200
        assert response.json()["message"] == "Review deleted successfully"


# ───────────────────────────── Payment ─────────────────────────────


class TestPaymentRouter:
    def test_list_payment_methods(self, client):
        pm = SimpleNamespace(id=1, method_type="credit_card", is_default=True)

        with patch(
            "api.services.payment_service.get_user_payment_methods",
            return_value=[pm],
        ):
            response = client.get("/payment-methods/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["method_type"] == "credit_card"
        assert data[0]["is_default"] is True

    def test_add_payment_method(self, client):
        with patch("api.services.payment_service.add_payment_method"):
            response = client.post(
                "/payment-methods/add",
                json={
                    "card_number": "4111111111111111",
                    "cardholder_name": "Test User",
                    "expiry": "12/28",
                    "cvv": "123",
                },
            )

        assert response.status_code == 201
        assert response.json()["message"] == "Card saved successfully"
