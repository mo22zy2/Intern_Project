from datetime import date, time, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api_endpoints.auth_utils import get_current_user, get_current_user_optional
from api_endpoints.database import get_db
from api_endpoints.main import app
from api_endpoints.models import (
    Cart,
    CartItem,
    Category,
    Inventory,
    Menu,
    MenuCustomizationOption,
    PaymentMethod,
    Review,
    User,
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.phone = "1234567890"
    user.birth = None
    user.password = "$2b$12$hashedpassword"
    user.is_active = True
    return user


@pytest.fixture
def client(mock_db, mock_user):
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_user_optional] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


# ───────────────────────────── Home ─────────────────────────────


class TestHomeRouter:
    def test_home_returns_popular_and_categories(self, client, mock_db):
        menu_mock = MagicMock(spec=Menu)
        menu_mock.id = 1
        menu_mock.image_url = "https://example.com/img.jpg"
        menu_mock.price = 12.99
        menu_mock.popularity_score = 95
        menu_mock.available = True
        menu_mock.item_ref.item_name = "Burger"
        menu_mock.category.category_name = "Main"
        menu_mock.customization_options = []

        cat_mock = MagicMock(spec=Category)
        cat_mock.id = 1
        cat_mock.category_name = "Main"

        subq_mock = MagicMock()
        subq_mock.c.avg_rating = 4.5

        subq_chain = MagicMock()
        subq_chain.group_by.return_value.subquery.return_value = subq_mock

        menu_query = MagicMock()
        menu_query.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            (menu_mock, 4.5)
        ]

        cat_query = MagicMock()
        cat_query.all.return_value = [cat_mock]

        count_query = MagicMock()
        count_query.filter.return_value.count.return_value = 10
        count_query.count.return_value = 5

        mock_db.query.side_effect = [
            subq_chain,
            menu_query,
            cat_query,
            count_query,
            count_query,
        ]

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
    @patch("api_endpoints.routers.auth.validate_password")
    @patch("api_endpoints.routers.auth.User")
    @patch("api_endpoints.routers.auth.hash_password", return_value="hashed_pw")
    @patch("api_endpoints.routers.auth.create_access_token", return_value="test_token")
    def test_register_success(
        self, mock_token, mock_hash, mock_user_cls, mock_validate, client, mock_db
    ):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_instance = MagicMock(spec=User)
        user_instance.id = 1
        user_instance.username = "newuser"
        mock_user_cls.return_value = user_instance

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

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["user_id"] == 1
        assert data["username"] == "newuser"
        assert mock_db.add.called
        assert mock_db.commit.called

    @patch("api_endpoints.routers.auth.validate_password")
    def test_register_duplicate_username(self, mock_validate, client, mock_db):
        existing = MagicMock(spec=User)
        existing.username = "takenuser"
        mock_db.query.return_value.filter.return_value.first.return_value = existing

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

    @patch("api_endpoints.routers.auth.create_access_token", return_value="test_token")
    def test_login_success(self, mock_token, client, mock_db):
        user_mock = MagicMock(spec=User)
        user_mock.id = 1
        user_mock.username = "testuser"
        user_mock.password = "$2b$12$hashedpassword"
        mock_db.query.return_value.filter.return_value.first.return_value = user_mock

        with patch("api_endpoints.routers.auth.verify_password", return_value=True):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "correctpassword"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token"
        assert data["username"] == "testuser"

    def test_login_invalid_credentials(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("api_endpoints.routers.auth.verify_password", return_value=False):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "wrongpassword"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"


# ───────────────────────────── Menu ─────────────────────────────


class TestMenuRouter:
    def test_menu_list(self, client, mock_db):
        menu_mock = MagicMock(spec=Menu)
        menu_mock.id = 1
        menu_mock.image_url = "https://example.com/img.jpg"
        menu_mock.price = 9.99
        menu_mock.popularity_score = 80
        menu_mock.available = True
        menu_mock.item_ref.item_name = "Pizza"
        menu_mock.category.category_name = "Main"
        menu_mock.customization_options = []

        cat_mock = MagicMock(spec=Category)
        cat_mock.id = 1
        cat_mock.category_name = "Main"

        avg_subq = MagicMock()
        avg_subq.label.return_value = 4.5

        menu_query = MagicMock()
        menu_query.filter.return_value.order_by.return_value.all.return_value = [
            (menu_mock, 4.5)
        ]

        cat_query = MagicMock()
        cat_query.all.return_value = [cat_mock]

        mock_db.query.side_effect = [avg_subq, menu_query, cat_query]

        response = client.get("/menu/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["item_name"] == "Pizza"

    def test_menu_detail_found(self, client, mock_db):
        menu_mock = MagicMock(spec=Menu)
        menu_mock.id = 1
        menu_mock.image_url = "https://example.com/img.jpg"
        menu_mock.price = 9.99
        menu_mock.popularity_score = 80
        menu_mock.available = True
        menu_mock.item_ref.item_name = "Pizza"
        menu_mock.category.category_name = "Main"
        menu_mock.customization_options = []

        mock_db.query.return_value.filter.return_value.first.return_value = menu_mock

        response = client.get("/menu/1")

        assert response.status_code == 200
        data = response.json()
        assert data["item_name"] == "Pizza"

    def test_menu_detail_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/menu/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Menu item not found"


# ───────────────────────────── Cart ─────────────────────────────


class TestCartRouter:
    def test_view_cart(self, client, mock_db, mock_user):
        cart_mock = MagicMock(spec=Cart)
        cart_mock.id = 1

        ci_mock = MagicMock(spec=CartItem)
        ci_mock.id = 1
        ci_mock.menu_id = 1
        ci_mock.option_id = None
        ci_mock.quantity = 2
        ci_mock.options_text = ""
        ci_mock.menu.price = 10.0
        ci_mock.menu.item_ref.item_name = "Burger"

        cart_mock.items = [ci_mock]

        mock_db.query.return_value.filter.return_value.first.return_value = cart_mock

        response = client.get("/cart/")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["item_name"] == "Burger"
        assert data["total"] == 20.0

    def test_add_to_cart(self, client, mock_db, mock_user):
        menu_mock = MagicMock(spec=Menu)
        menu_mock.id = 1

        cart_mock = MagicMock(spec=Cart)
        cart_mock.id = 1

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            menu_mock,
            cart_mock,
            None,
        ]

        response = client.post(
            "/cart/add/1",
            json={"menu_id": 1, "option_ids": [], "quantity": 2},
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Item added to cart"
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_add_to_cart_item_not_found(self, client, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post(
            "/cart/add/999",
            json={"menu_id": 999, "option_ids": [], "quantity": 1},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Menu item not found"

    def test_remove_from_cart(self, client, mock_db, mock_user):
        cart_mock = MagicMock(spec=Cart)
        cart_mock.id = 1

        ci_mock = MagicMock(spec=CartItem)
        ci_mock.id = 1

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            cart_mock,
            ci_mock,
        ]

        response = client.delete("/cart/remove/1")

        assert response.status_code == 200
        assert response.json()["message"] == "Item removed from cart"
        assert mock_db.delete.called
        assert mock_db.commit.called


# ───────────────────────────── Order ─────────────────────────────


class TestOrderRouter:
    def test_checkout_empty_cart(self, client, mock_db, mock_user):
        cart_mock = MagicMock(spec=Cart)
        cart_mock.items = []
        mock_db.query.return_value.filter.return_value.first.return_value = cart_mock

        response = client.get("/orders/checkout")

        assert response.status_code == 400
        assert response.json()["detail"] == "Cart is empty"

    def test_place_order(self, client, mock_db, mock_user):
        inv_mock = MagicMock(spec=Inventory)
        inv_mock.id = 1
        inv_mock.ordered = 0

        cart_mock = MagicMock(spec=Cart)
        cart_mock.id = 1

        ci_mock = MagicMock(spec=CartItem)
        ci_mock.menu_id = 1
        ci_mock.option_id = None
        ci_mock.quantity = 2
        ci_mock.options_text = ""
        ci_mock.menu.price = 12.99
        ci_mock.menu.item_ref.item_name = "Burger"
        ci_mock.menu.item_id = 1

        cart_mock.items = [ci_mock]

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            cart_mock,
            None,
            inv_mock,
        ]

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
        assert response.json()["message"] == "Order placed successfully"
        assert mock_db.add.called
        assert mock_db.commit.called


# ───────────────────────────── Reservation ─────────────────────────────


class TestReservationRouter:
    def test_make_reservation(self, client, mock_db, mock_user):
        fixed_now = datetime(2025, 6, 15, 12, 0, 0)

        with patch("api_endpoints.routers.reservation.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now

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
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_make_reservation_past_date(self, client, mock_db, mock_user):
        fixed_now = datetime(2025, 6, 15, 12, 0, 0)

        with patch("api_endpoints.routers.reservation.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now

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
        response = client.get("/profile/")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"

    def test_edit_profile(self, client, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

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
        assert mock_user.first_name == "Updated"
        assert mock_user.last_name == "Name"
        assert mock_user.email == "updated@example.com"
        assert mock_user.phone == "0987654321"
        assert mock_db.commit.called

    def test_change_password(self, client, mock_db, mock_user):
        with patch(
            "api_endpoints.routers.profile.verify_password", return_value=True
        ), patch(
            "api_endpoints.routers.profile.hash_password",
            return_value="new_hashed_pw",
        ), patch(
            "api_endpoints.routers.profile.validate_password",
        ):
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
        assert mock_user.password == "new_hashed_pw"
        assert mock_db.commit.called


# ───────────────────────────── Review ─────────────────────────────


class TestReviewRouter:
    def test_add_review(self, client, mock_db, mock_user):
        menu_mock = MagicMock(spec=Menu)
        menu_mock.id = 1

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            menu_mock,
            None,
        ]

        response = client.post(
            "/reviews/add/1",
            json={"rating": 5, "comment": "Excellent!"},
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Review added successfully"
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_add_review_duplicate(self, client, mock_db, mock_user):
        menu_mock = MagicMock(spec=Menu)
        menu_mock.id = 1

        existing_review = MagicMock(spec=Review)
        existing_review.id = 1

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            menu_mock,
            existing_review,
        ]

        response = client.post(
            "/reviews/add/1",
            json={"rating": 4, "comment": "Good"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "You already reviewed this item"

    def test_delete_review(self, client, mock_db, mock_user):
        review_mock = MagicMock(spec=Review)
        review_mock.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = (
            review_mock
        )

        response = client.delete("/reviews/1/delete")

        assert response.status_code == 200
        assert response.json()["message"] == "Review deleted successfully"
        assert mock_db.delete.called
        assert mock_db.commit.called


# ───────────────────────────── Payment ─────────────────────────────


class TestPaymentRouter:
    def test_list_payment_methods(self, client, mock_db, mock_user):
        pm_mock = MagicMock(spec=PaymentMethod)
        pm_mock.id = 1
        pm_mock.method_type = "credit_card"
        pm_mock.is_default = True

        mock_db.query.return_value.filter.return_value.all.return_value = [pm_mock]

        response = client.get("/payment-methods/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["method_type"] == "credit_card"
        assert data[0]["is_default"] is True

    def test_add_payment_method(self, client, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

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
        assert mock_db.add.called
        assert mock_db.commit.called
