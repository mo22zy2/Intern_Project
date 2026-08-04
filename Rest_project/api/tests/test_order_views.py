from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Inventory,
    Category,
    Menu,
    MenuCustomizationOption,
    Payment,
    PaymentMethod,
    ReservationSystem,
)

User = get_user_model()


class TestCheckoutView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.inventory = Inventory.objects.create(
            item_name="Burger", item_count=10, ordered=0
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=12.99
        )
        self.option = MenuCustomizationOption.objects.create(
            menu=self.menu, option_name="Extra Cheese", extra_price=1.50
        )

        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            menu=self.menu,
            option=self.option,
            quantity=2,
        )

        self.payment_method = PaymentMethod.objects.create(
            user=self.user, method_type="Credit Card", is_default=True
        )

        self.checkout_url = reverse("checkout")
        self.view_cart_url = reverse("view_cart")
        self.login_url = reverse("login")

    def test_checkout_shows_cart_items(self):
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Burger")
        self.assertContains(response, "EGP14.49")
        self.assertContains(response, "EGP28.98")

    def test_checkout_empty_cart_redirects(self):
        self.cart.delete()
        response = self.client.get(self.checkout_url)
        self.assertRedirects(response, self.view_cart_url)

    def test_checkout_requires_login(self):
        self.client.logout()
        response = self.client.get(self.checkout_url)
        expected = f"{self.login_url}?next={self.checkout_url}"
        self.assertRedirects(response, expected)


class TestPlaceOrder(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.inventory = Inventory.objects.create(
            item_name="Burger", item_count=10, ordered=0
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=12.99
        )
        self.option = MenuCustomizationOption.objects.create(
            menu=self.menu, option_name="Extra Cheese", extra_price=1.50
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            menu=self.menu,
            option=self.option,
            quantity=2,
        )

        self.place_order_url = reverse("place_order")
        self.order_history_url = reverse("order_history")
        self.checkout_url = reverse("checkout")

    def test_place_order_delivery_creates_order(self):
        response = self.client.post(self.place_order_url, {
            "delivery_type": "delivery",
            "delivery_address": "123 Main St, Cairo",
            "payment_type": "cash",
        })
        self.assertRedirects(response, self.order_history_url)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.delivery_type, "delivery")
        self.assertEqual(order.delivery_address, "123 Main St, Cairo")
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_price, 28.98)

    def test_place_order_creates_order_items(self):
        self.client.post(self.place_order_url, {
            "delivery_type": "delivery",
            "delivery_address": "123 Main St, Cairo",
            "payment_type": "cash",
        })
        self.assertEqual(OrderItem.objects.count(), 1)
        order = Order.objects.first()
        order_item = OrderItem.objects.first()
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.menu, self.menu)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, 14.49)
        self.assertEqual(order_item.options_text, "Extra Cheese")

    def test_place_order_updates_inventory(self):
        self.client.post(self.place_order_url, {
            "delivery_type": "delivery",
            "delivery_address": "123 Main St, Cairo",
            "payment_type": "cash",
        })
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.ordered, 2)

    def test_place_order_creates_payment(self):
        self.client.post(self.place_order_url, {
            "delivery_type": "delivery",
            "delivery_address": "123 Main St, Cairo",
            "payment_type": "cash",
        })
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.first()
        self.assertEqual(payment.amount, 28.98)
        self.assertEqual(payment.status, "confirmed")

    def test_place_order_clears_cart(self):
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)
        self.client.post(self.place_order_url, {
            "delivery_type": "delivery",
            "delivery_address": "123 Main St, Cairo",
            "payment_type": "cash",
        })
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_place_order_missing_address(self):
        response = self.client.post(self.place_order_url, {
            "delivery_type": "delivery",
            "delivery_address": "",
            "payment_type": "cash",
        })
        self.assertRedirects(response, self.checkout_url)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_place_order_pickup_creates_reservation(self):
        future_date = (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = self.client.post(self.place_order_url, {
            "delivery_type": "dine_in",
            "payment_type": "cash",
            "reservation_date": future_date,
            "reservation_time": "19:00",
            "seats": "4",
        })
        self.assertRedirects(response, self.order_history_url)
        self.assertEqual(ReservationSystem.objects.count(), 1)
        reservation = ReservationSystem.objects.first()
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.seats, 4)
        self.assertEqual(reservation.status, "pending")
        order = Order.objects.first()
        self.assertIsNotNone(order.reservation)
        self.assertEqual(order.reservation, reservation)
        self.assertEqual(order.delivery_type, "dine_in")
        self.assertEqual(order.delivery_address, "")


class TestOrderDetail(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="otherpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.inventory = Inventory.objects.create(
            item_name="Burger", item_count=10, ordered=0
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=12.99
        )
        self.order = Order.objects.create(
            user=self.user,
            delivery_type="delivery",
            delivery_address="123 Main St",
            total_price=25.98,
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            menu=self.menu,
            quantity=2,
            unit_price=12.99,
        )
        self.detail_url = reverse("order_detail", args=[self.order.id])

    def test_order_detail_shows_order(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "123 Main St")
        self.assertContains(response, "EGP25.98")
        self.assertContains(response, "Burger")

    def test_order_detail_not_owner_404(self):
        self.client.logout()
        self.client.login(username="otheruser", password="otherpass123")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 404)


class TestOrderHistory(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        self.inventory = Inventory.objects.create(
            item_name="Burger", item_count=10, ordered=0
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=12.99
        )
        self.history_url = reverse("order_history")

    def test_order_history_lists_orders(self):
        Order.objects.create(
            user=self.user,
            delivery_type="delivery",
            delivery_address="123 Main St",
            total_price=25.98,
        )
        Order.objects.create(
            user=self.user,
            delivery_type="dine_in",
            total_price=15.99,
        )
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "25.98")
        self.assertContains(response, "15.99")

    def test_order_history_empty(self):
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "haven't placed any orders yet")
