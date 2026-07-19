import copy
from datetime import date, time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.context import BaseContext
from api.models import Category, Inventory, Menu, MenuCustomizationOption, Review, Order, ReservationSystem


def _patched_base_copy(self):
    duplicate = BaseContext.__new__(BaseContext)
    BaseContext.__init__(duplicate)
    duplicate.dicts = self.dicts[:]
    return duplicate


BaseContext.__copy__ = _patched_base_copy


class TestHomeView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.inventory = Inventory.objects.create(item_name="Grilled Chicken")
        for i in range(6):
            Menu.objects.create(
                item=self.inventory,
                category=self.category,
                price=10.0 + i,
                popularity_score=100 - i,
                available=True,
            )

    def test_home_renders_template(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_shows_featured_items(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(len(response.context["featured_items"]), 4)

    def test_home_authenticated_shows_orders_reservations(self):
        self.client.login(username="testuser", password="testpass123")
        Order.objects.create(user=self.user, total_price=25.0)
        ReservationSystem.objects.create(
            user=self.user,
            reservation_date=date.today(),
            reservation_time=time(19, 0),
            seats=2,
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(len(response.context["recent_orders"]), 1)
        self.assertEqual(len(response.context["upcoming_reservations"]), 1)
        self.assertEqual(response.context["total_orders"], 1)
        self.assertEqual(response.context["total_reservations"], 1)

    def test_home_unauthenticated_no_orders(self):
        response = self.client.get(reverse("home"))
        self.assertNotIn("recent_orders", response.context)
        self.assertNotIn("upcoming_reservations", response.context)
        self.assertNotIn("total_orders", response.context)
        self.assertNotIn("total_reservations", response.context)


class TestMenuListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.category1 = Category.objects.create(category_name="Main Course")
        self.category2 = Category.objects.create(category_name="Desserts")
        self.inv1 = Inventory.objects.create(item_name="Grilled Chicken")
        self.inv2 = Inventory.objects.create(item_name="Chocolate Cake")
        self.inv3 = Inventory.objects.create(item_name="Caesar Salad")
        self.item1 = Menu.objects.create(
            item=self.inv1, category=self.category1, price=15.0,
            popularity_score=50, available=True,
        )
        self.item2 = Menu.objects.create(
            item=self.inv2, category=self.category2, price=8.0,
            popularity_score=80, available=True,
        )
        self.item3 = Menu.objects.create(
            item=self.inv3, category=self.category1, price=12.0,
            popularity_score=30, available=False,
        )

    def test_menu_list_shows_items(self):
        response = self.client.get(reverse("menu"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "menu/menu_list.html")
        self.assertIn(self.item1, response.context["items"])
        self.assertIn(self.item2, response.context["items"])

    def test_menu_list_filter_by_category(self):
        response = self.client.get(reverse("menu"), {"category": self.category1.id})
        self.assertIn(self.item1, response.context["items"])
        self.assertNotIn(self.item2, response.context["items"])

    def test_menu_list_search(self):
        response = self.client.get(reverse("menu"), {"search": "Chocolate"})
        self.assertIn(self.item2, response.context["items"])
        self.assertNotIn(self.item1, response.context["items"])

    def test_menu_list_sort_by_price(self):
        response = self.client.get(reverse("menu"), {"sort": "price_low"})
        prices = [item.price for item in response.context["items"]]
        self.assertEqual(prices, sorted(prices))

    def test_menu_list_only_available_items(self):
        response = self.client.get(reverse("menu"))
        self.assertIn(self.item1, response.context["items"])
        self.assertNotIn(self.item3, response.context["items"])


class TestMenuDetailView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="reviewer", password="testpass123"
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.inventory = Inventory.objects.create(item_name="Grilled Chicken")
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=15.0,
            popularity_score=50, available=True,
        )
        self.unavailable_menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=20.0,
            available=False,
        )
        self.option = MenuCustomizationOption.objects.create(
            menu=self.menu, option_name="Extra Cheese", extra_price=2.5,
        )
        self.review = Review.objects.create(
            user=self.user, menu=self.menu, rating=5, comment="Delicious!",
        )

    def test_menu_detail_shows_item(self):
        response = self.client.get(reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "menu/menu_detail.html")
        self.assertEqual(response.context["item"], self.menu)

    def test_menu_detail_shows_options(self):
        response = self.client.get(reverse("menu_detail", args=[self.menu.id]))
        self.assertIn(self.option, response.context["options"])

    def test_menu_detail_shows_reviews(self):
        response = self.client.get(reverse("menu_detail", args=[self.menu.id]))
        self.assertIn(self.review, response.context["reviews"])
        self.assertEqual(response.context["avg_rating"], 5.0)
        self.assertIsNone(response.context["user_review"])

    def test_menu_detail_shows_user_review_when_authenticated(self):
        self.client.login(username="reviewer", password="testpass123")
        response = self.client.get(reverse("menu_detail", args=[self.menu.id]))
        self.assertEqual(response.context["user_review"], self.review)

    def test_menu_detail_404_for_unavailable(self):
        response = self.client.get(
            reverse("menu_detail", args=[self.unavailable_menu.id])
        )
        self.assertEqual(response.status_code, 404)
