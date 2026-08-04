from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from api.models import UserSettings


@patch("django.test.client.store_rendered_templates", lambda *a, **kw: None)
class TestRegisterView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("register")
        self.valid_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
            "phone": "123456789",
            "birth": "2000-01-15",
        }

    def test_register_page_GET_renders_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_register_success_creates_user_and_settings_and_logs_in(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("menu"))

        user = get_user_model().objects.get(username="newuser")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.phone, "123456789")
        self.assertIsNotNone(user.birth)

        self.assertTrue(UserSettings.objects.filter(user=user).exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_missing_fields_returns_error(self):
        data = self.valid_data.copy()
        data.pop("last_name")
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("required" in str(m).lower() for m in messages))
        self.assertFalse(
            get_user_model().objects.filter(username="newuser").exists()
        )

    def test_register_duplicate_username_returns_error(self):
        get_user_model().objects.create_user(
            username="newuser", password="SomePass1!", email="other@example.com"
        )
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any("username is taken" in str(m).lower() for m in messages)
        )

    def test_register_duplicate_email_returns_error(self):
        get_user_model().objects.create_user(
            username="otheruser", password="SomePass1!", email="new@example.com"
        )
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any("already registered" in str(m).lower() for m in messages)
        )

    def test_register_password_mismatch_returns_error(self):
        data = self.valid_data.copy()
        data["confirm_password"] = "DifferentPass456!"
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any("do not match" in str(m).lower() for m in messages)
        )
        self.assertFalse(
            get_user_model().objects.filter(username="newuser").exists()
        )


@patch("django.test.client.store_rendered_templates", lambda *a, **kw: None)
class TestLoginView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("login")
        self.password = "TestPass123!"
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password=self.password,
        )

    def test_login_page_GET_renders_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_login_success_authenticates_and_redirects(self):
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("menu"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_credentials_shows_error(self):
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any("invalid" in str(m).lower() for m in messages)
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)


@patch("django.test.client.store_rendered_templates", lambda *a, **kw: None)
class TestLogoutView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("logout")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )

    def test_logout_logs_out_and_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_GET_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
