from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from api.models import UserSettings, Review, PaymentMethod, Category, Inventory, Menu, Order, OrderItem


class TestProfileView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("profile")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
            phone="123456789",
            birth="1990-01-15",
        )

    def test_profile_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_profile_renders_template(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/profile.html")

    def test_profile_creates_settings_if_missing(self):
        self.client.login(username="testuser", password="TestPass123!")
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())
        self.client.get(self.url)
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())

    def test_profile_context_contains_settings_reviews_payments(self):
        self.client.login(username="testuser", password="TestPass123!")
        settings = UserSettings.objects.create(user=self.user)
        response = self.client.get(self.url)
        self.assertIn("settings", response.context)
        self.assertIn("reviews", response.context)
        self.assertIn("payment_methods", response.context)
        self.assertEqual(response.context["settings"], settings)


class TestEditProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("edit_profile")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            last_name="User",
            phone="123456789",
            birth="1990-01-15",
        )

    def test_edit_profile_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_edit_profile_GET_renders_template(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/profile.html")

    def test_edit_profile_GET_has_editing_in_context(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertTrue(response.context["editing"])

    def test_edit_profile_updates_fields(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "phone": "987654321",
            "birth": "1995-05-20",
            "dark_mode": "on",
            "locale": "fr",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.phone, "987654321")
        self.assertEqual(str(self.user.birth), "1995-05-20")
        settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings.dark_mode)
        self.assertEqual(settings.locale, "fr")

    def test_edit_profile_validates_email_uniqueness(self):
        get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="TestPass123!",
        )
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "first_name": "Test",
            "last_name": "User",
            "email": "other@example.com",
            "phone": "123456789",
            "birth": "1990-01-15",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile/profile.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already in use" in str(m).lower() for m in messages))

    def test_edit_profile_same_email_is_allowed(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "123456789",
            "birth": "1990-01-15",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))

    def test_edit_profile_missing_fields_returns_error(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "first_name": "",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "",
            "birth": "1990-01-15",
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages))

    def test_edit_profile_updates_settings_without_dark_mode(self):
        self.client.login(username="testuser", password="TestPass123!")
        self.client.post(self.url, {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "123456789",
            "birth": "1990-01-15",
        })
        settings = UserSettings.objects.get(user=self.user)
        self.assertFalse(settings.dark_mode)

    def test_edit_profile_GET_creates_settings_if_missing(self):
        self.client.login(username="testuser", password="TestPass123!")
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())
        self.client.get(self.url)
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())

    def test_edit_profile_success_message(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "123456789",
            "birth": "1990-01-15",
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("profile updated" in str(m).lower() for m in messages))


class TestChangePassword(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("change_password")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPass123!",
        )

    def test_change_password_requires_login(self):
        response = self.client.post(self.url, {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_change_password_GET_redirects(self):
        self.client.login(username="testuser", password="OldPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))

    def test_change_password_success(self):
        self.client.login(username="testuser", password="OldPass123!")
        response = self.client.post(self.url, {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("password changed" in str(m).lower() for m in messages))

    def test_change_password_wrong_old_password(self):
        self.client.login(username="testuser", password="OldPass123!")
        response = self.client.post(self.url, {
            "old_password": "WrongPass!",
            "new_password": "NewPass456!",
            "confirm_password": "NewPass456!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("current password is incorrect" in str(m).lower() for m in messages))

    def test_change_password_mismatch(self):
        self.client.login(username="testuser", password="OldPass123!")
        response = self.client.post(self.url, {
            "old_password": "OldPass123!",
            "new_password": "NewPass456!",
            "confirm_password": "Different789!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("do not match" in str(m).lower() for m in messages))

    def test_change_password_weak_password(self):
        self.client.login(username="testuser", password="OldPass123!")
        response = self.client.post(self.url, {
            "old_password": "OldPass123!",
            "new_password": "weak",
            "confirm_password": "weak",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))


class TestAddReview(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        order = Order.objects.create(user=self.user, total_price=15.99, status="confirmed")
        OrderItem.objects.create(order=order, menu=self.menu, quantity=1, unit_price=15.99)
        self.url = reverse("add_review", args=[self.menu.id])

    def test_add_review_requires_login(self):
        response = self.client.post(self.url, {"rating": 5, "comment": "Great!"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_add_review_GET_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))

    def test_add_review_success(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 5, "comment": "Delicious!"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Delicious!")
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.menu, self.menu)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("review submitted" in str(m).lower() for m in messages))

    def test_add_review_prevents_duplicate(self):
        self.client.login(username="testuser", password="TestPass123!")
        self.client.post(self.url, {"rating": 5, "comment": "Great!"})
        response = self.client.post(self.url, {"rating": 3, "comment": "Second try"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(Review.objects.count(), 1)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already reviewed" in str(m).lower() for m in messages))

    def test_add_review_rating_below_1(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 0, "comment": "Bad"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(Review.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("between 1 and 5" in str(m).lower() for m in messages))

    def test_add_review_rating_above_5(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 6, "comment": "Too high"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(Review.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("between 1 and 5" in str(m).lower() for m in messages))

    def test_add_review_invalid_rating_non_numeric(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": "abc", "comment": "hmm"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(Review.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("between 1 and 5" in str(m).lower() for m in messages))

    def test_add_review_empty_comment_is_valid(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 4, "comment": ""})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(Review.objects.count(), 1)

    def test_add_review_404_for_invalid_menu(self):
        self.client.login(username="testuser", password="TestPass123!")
        url = reverse("add_review", args=[9999])
        response = self.client.post(url, {"rating": 5, "comment": "Nope"})
        self.assertEqual(response.status_code, 404)


class TestMyReviews(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("my_reviews")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.review = Review.objects.create(
            user=self.user, menu=self.menu, rating=4, comment="Good"
        )

    def test_my_reviews_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_my_reviews_renders_template(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/my_reviews.html")

    def test_my_reviews_context_contains_user_reviews(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertIn("reviews", response.context)
        self.assertEqual(list(response.context["reviews"]), [self.review])

    def test_my_reviews_only_shows_own_reviews(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="TestPass123!"
        )
        Review.objects.create(
            user=other_user, menu=self.menu, rating=5, comment="Other's"
        )
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["reviews"]), 1)


class TestEditReview(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.review = Review.objects.create(
            user=self.user, menu=self.menu, rating=3, comment="Okay"
        )
        self.url = reverse("edit_review", args=[self.review.id])

    def test_edit_review_requires_login(self):
        response = self.client.post(self.url, {"rating": 5, "comment": "Updated"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_edit_review_GET_renders_template(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reviews/edit_review.html")

    def test_edit_review_GET_shows_review_in_context(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.context["review"], self.review)

    def test_edit_review_updates_review(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 5, "comment": "Excellent!"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_reviews"))
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, "Excellent!")
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("review updated" in str(m).lower() for m in messages))

    def test_edit_review_rating_below_1(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 0, "comment": "Bad"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_reviews"))
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

    def test_edit_review_rating_above_5(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 7, "comment": "Too high"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_reviews"))
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

    def test_edit_review_cannot_edit_others_review(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="TestPass123!"
        )
        self.client.login(username="other", password="TestPass123!")
        response = self.client.post(self.url, {"rating": 5, "comment": "Hacked"})
        self.assertEqual(response.status_code, 404)

    def test_edit_review_404_for_invalid_id(self):
        self.client.login(username="testuser", password="TestPass123!")
        url = reverse("edit_review", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestDeleteReview(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.review = Review.objects.create(
            user=self.user, menu=self.menu, rating=4, comment="Good"
        )
        self.url = reverse("delete_review", args=[self.review.id])

    def test_delete_review_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_delete_review_GET_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_reviews"))
        self.assertEqual(Review.objects.count(), 1)

    def test_delete_review_deletes(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_reviews"))
        self.assertEqual(Review.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("review deleted" in str(m).lower() for m in messages))

    def test_delete_review_cannot_delete_others_review(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="TestPass123!"
        )
        self.client.login(username="other", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Review.objects.count(), 1)

    def test_delete_review_404_for_invalid_id(self):
        self.client.login(username="testuser", password="TestPass123!")
        url = reverse("delete_review", args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class TestPaymentMethods(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("payment_methods")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        self.method = PaymentMethod.objects.create(
            user=self.user, method_type="•••• 1234", is_default=True
        )

    def test_payment_methods_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_payment_methods_renders_template(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "payment/payment_methods.html")

    def test_payment_methods_context_contains_methods(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertIn("methods", response.context)
        self.assertEqual(list(response.context["methods"]), [self.method])

    def test_payment_methods_only_shows_own_methods(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="TestPass123!"
        )
        PaymentMethod.objects.create(
            user=other_user, method_type="•••• 5678"
        )
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["methods"]), 1)


class TestAddPaymentMethod(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("add_payment_method")
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )

    def test_add_payment_method_requires_login(self):
        response = self.client.post(self.url, {
            "card_number": "4111111111111111",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_add_payment_method_GET_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))

    def test_add_payment_method_success(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "card_number": "4111111111111111",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.assertEqual(PaymentMethod.objects.count(), 1)
        method = PaymentMethod.objects.first()
        self.assertEqual(method.method_type, "•••• 1111")
        self.assertFalse(method.is_default)

    def test_add_payment_method_sets_default(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "card_number": "4111111111111111",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
            "is_default": "on",
        })
        self.assertEqual(response.status_code, 302)
        method = PaymentMethod.objects.first()
        self.assertTrue(method.is_default)

    def test_add_payment_method_unmarks_old_default(self):
        self.client.login(username="testuser", password="TestPass123!")
        PaymentMethod.objects.create(
            user=self.user, method_type="•••• 0000", is_default=True
        )
        self.client.post(self.url, {
            "card_number": "4111111111111111",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
            "is_default": "on",
        })
        old = PaymentMethod.objects.get(method_type="•••• 0000")
        self.assertFalse(old.is_default)
        new = PaymentMethod.objects.get(method_type="•••• 1111")
        self.assertTrue(new.is_default)

    def test_add_payment_method_validates_card_number_min_length(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "card_number": "1234",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.assertEqual(PaymentMethod.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid card number" in str(m).lower() for m in messages))

    def test_add_payment_method_accepts_card_with_spaces(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "card_number": "4111 1111 1111 1111",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PaymentMethod.objects.count(), 1)
        method = PaymentMethod.objects.first()
        self.assertEqual(method.method_type, "•••• 1111")

    def test_add_payment_method_missing_fields(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "card_number": "4111111111111111",
            "cardholder_name": "",
            "expiry": "12/28",
            "cvv": "123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.assertEqual(PaymentMethod.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages))

    def test_add_payment_method_success_message(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url, {
            "card_number": "4111111111111111",
            "cardholder_name": "Test User",
            "expiry": "12/28",
            "cvv": "123",
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("card saved" in str(m).lower() for m in messages))


class TestDeletePaymentMethod(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        self.method = PaymentMethod.objects.create(
            user=self.user, method_type="•••• 1234", is_default=True
        )
        self.url = reverse("delete_payment_method", args=[self.method.id])

    def test_delete_payment_method_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_delete_payment_method_GET_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.assertEqual(PaymentMethod.objects.count(), 1)

    def test_delete_payment_method_deletes(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.assertEqual(PaymentMethod.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("card removed" in str(m).lower() for m in messages))

    def test_delete_payment_method_cannot_delete_others(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="TestPass123!"
        )
        self.client.login(username="other", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PaymentMethod.objects.count(), 1)

    def test_delete_payment_method_404_for_invalid_id(self):
        self.client.login(username="testuser", password="TestPass123!")
        url = reverse("delete_payment_method", args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class TestSetDefaultPaymentMethod(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )
        self.method1 = PaymentMethod.objects.create(
            user=self.user, method_type="•••• 1111", is_default=True
        )
        self.method2 = PaymentMethod.objects.create(
            user=self.user, method_type="•••• 2222", is_default=False
        )
        self.url = reverse("set_default_payment_method", args=[self.method2.id])

    def test_set_default_requires_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + self.url)

    def test_set_default_GET_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.method1.refresh_from_db()
        self.assertTrue(self.method1.is_default)
        self.method2.refresh_from_db()
        self.assertFalse(self.method2.is_default)

    def test_set_default_sets_new_default(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("payment_methods"))
        self.method1.refresh_from_db()
        self.method2.refresh_from_db()
        self.assertFalse(self.method1.is_default)
        self.assertTrue(self.method2.is_default)

    def test_set_default_success_message(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("default card updated" in str(m).lower() for m in messages))

    def test_set_default_cannot_set_others_method(self):
        other_user = get_user_model().objects.create_user(
            username="other", password="TestPass123!"
        )
        self.client.login(username="other", password="TestPass123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.method1.refresh_from_db()
        self.assertTrue(self.method1.is_default)

    def test_set_default_404_for_invalid_id(self):
        self.client.login(username="testuser", password="TestPass123!")
        url = reverse("set_default_payment_method", args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
