from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from api.models import Category, Inventory, Menu, MenuCustomizationOption, Cart, CartItem
from api.services import cart_service


class BaseCartTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )
        self.category = Category.objects.create(category_name="Main Course")
        self.inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=15.99
        )
        self.menu2 = Menu.objects.create(
            item=Inventory.objects.create(item_name="Beef Steak"),
            category=self.category,
            price=25.00,
        )
        self.option = MenuCustomizationOption.objects.create(
            menu=self.menu, option_name="Extra Cheese", extra_price=2.50
        )


class TestAddToCart(BaseCartTest):
    def test_add_item_creates_cart_item(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("menu_detail", args=[self.menu.id])
        )
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.menu, self.menu)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.options_text, "")
        self.assertIsNone(item.option)

    def test_add_item_increments_existing(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 2},
        )
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.quantity, 3)

    def test_add_item_increments_existing_with_options(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1, "options": [self.option.id]},
        )
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 2, "options": [self.option.id]},
        )
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.options_text, "Extra Cheese")

    def test_add_item_diff_options_create_separate_items(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1, "options": [self.option.id]},
        )
        self.assertEqual(CartItem.objects.count(), 2)

    def test_add_item_with_options(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1, "options": [self.option.id]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("menu_detail", args=[self.menu.id])
        )
        item = CartItem.objects.first()
        self.assertEqual(item.options_text, "Extra Cheese")
        self.assertIsNone(item.option)
        self.assertEqual(item.menu, self.menu)

    def test_add_item_defaults_quantity_to_one(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(reverse("add_to_cart", args=[self.menu.id]))
        item = CartItem.objects.first()
        self.assertEqual(item.quantity, 1)

    def test_add_item_creates_cart_if_not_exists(self):
        self.client.login(username="testuser", password="testpass")
        self.assertEqual(Cart.objects.count(), 0)
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(Cart.objects.first().user, self.user)

    def test_add_item_redirects_unauthenticated(self):
        response = self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_add_item_creates_cart_with_correct_user(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        cart = Cart.objects.first()
        self.assertEqual(cart.user, self.user)


class TestViewCart(BaseCartTest):
    def test_view_cart_creates_cart_when_missing(self):
        self.client.login(username="testuser", password="testpass")
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 0)
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

    def test_cart_updated_at_changes_on_add(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 1},
        )
        cart = Cart.objects.get(user=self.user)
        updated_before = cart.updated_at
        self.client.post(
            reverse("add_to_cart", args=[self.menu.id]),
            {"quantity": 2},
        )
        cart.refresh_from_db()
        self.assertGreaterEqual(cart.updated_at, updated_before)

    def test_subtotal_basic_calculation(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, menu=self.menu, quantity=2)
        CartItem.objects.create(cart=cart, menu=self.menu2, quantity=1)
        items = CartItem.objects.filter(cart=cart).select_related("menu")
        subtotal = 0
        for ci in items:
            subtotal += ci.menu.price * ci.quantity
        self.assertAlmostEqual(subtotal, 56.98, places=2)

    def test_subtotal_with_options_text(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart, menu=self.menu, quantity=2,
            options_text="Extra Cheese",
        )
        items = CartItem.objects.filter(cart=cart).select_related(
            "menu__item", "menu__category", "option"
        )
        subtotal = 0
        for ci in items:
            base_cost = ci.menu.price
            extra = 0
            if ci.options_text and ci.option is None:
                option_names = [
                    name.strip()
                    for name in ci.options_text.split(",")
                    if name.strip()
                ]
                extra_prices = MenuCustomizationOption.objects.filter(
                    menu=ci.menu, option_name__in=option_names
                ).values_list("extra_price", flat=True)
                extra = sum(extra_prices)
            elif ci.option:
                extra = ci.option.extra_price
            subtotal += (base_cost + extra) * ci.quantity
        self.assertAlmostEqual(subtotal, 36.98, places=2)

    def test_subtotal_with_option_fk(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart, menu=self.menu, quantity=3,
            option=self.option,
        )
        items = CartItem.objects.filter(cart=cart).select_related(
            "menu__item", "menu__category", "option"
        )
        subtotal = 0
        for ci in items:
            base_cost = ci.menu.price
            extra = ci.option.extra_price if ci.option else 0
            subtotal += (base_cost + extra) * ci.quantity
        self.assertAlmostEqual(subtotal, 55.47, places=2)

    def test_view_cart_redirects_unauthenticated(self):
        response = self.client.get(reverse("view_cart"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class TestUpdateCartItem(BaseCartTest):
    def setUp(self):
        super().setUp()
        self.client.login(username="testuser", password="testpass")
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, menu=self.menu, quantity=2
        )

    def test_update_quantity(self):
        response = self.client.post(
            reverse("update_cart_item", args=[self.cart_item.id]),
            {"quantity": 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("view_cart"))
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 5)

    def test_update_rejects_zero_quantity(self):
        with self.assertRaises(ValueError):
            cart_service.update_cart_item_quantity(self.cart, self.cart_item.id, 0)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    def test_update_defaults_quantity_to_one(self):
        response = self.client.post(
            reverse("update_cart_item", args=[self.cart_item.id]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("view_cart"))
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 1)

    def test_update_rejects_negative_quantity(self):
        with self.assertRaises(ValueError):
            cart_service.update_cart_item_quantity(self.cart, self.cart_item.id, -1)
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 2)

    def test_update_redirects_unauthenticated(self):
        self.client.logout()
        response = self.client.post(
            reverse("update_cart_item", args=[self.cart_item.id]),
            {"quantity": 3},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class TestAddToCartAndCheckout(BaseCartTest):
    def test_add_and_checkout_redirect(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("checkout"))
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.menu, self.menu)
        self.assertEqual(item.quantity, 1)

    def test_add_and_checkout_with_options(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
            {"quantity": 2, "options": [self.option.id]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("checkout"))
        item = CartItem.objects.first()
        self.assertEqual(item.options_text, "Extra Cheese")
        self.assertEqual(item.quantity, 2)

    def test_add_and_checkout_increments_existing_item(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
            {"quantity": 2},
        )
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.first().quantity, 3)

    def test_add_and_checkout_defaults_quantity(self):
        self.client.login(username="testuser", password="testpass")
        self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
        )
        self.assertEqual(CartItem.objects.first().quantity, 1)

    def test_add_and_checkout_redirects_unauthenticated(self):
        response = self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_add_and_checkout_creates_cart(self):
        self.client.login(username="testuser", password="testpass")
        self.assertEqual(Cart.objects.count(), 0)
        self.client.post(
            reverse("add_to_cart_and_checkout", args=[self.menu.id]),
            {"quantity": 1},
        )
        self.assertEqual(Cart.objects.count(), 1)


class TestRemoveFromCart(BaseCartTest):
    def setUp(self):
        super().setUp()
        self.client.login(username="testuser", password="testpass")
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, menu=self.menu, quantity=1
        )

    def test_remove_item(self):
        response = self.client.post(
            reverse("remove_from_cart", args=[self.cart_item.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("view_cart"))
        self.assertEqual(CartItem.objects.count(), 0)

    def test_remove_item_only_deletes_specified(self):
        cart_item2 = CartItem.objects.create(
            cart=self.cart, menu=self.menu, quantity=3
        )
        response = self.client.post(
            reverse("remove_from_cart", args=[self.cart_item.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("view_cart"))
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.first().id, cart_item2.id)

    def test_remove_item_redirects_unauthenticated(self):
        self.client.logout()
        response = self.client.post(
            reverse("remove_from_cart", args=[self.cart_item.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_remove_preserves_cart(self):
        response = self.client.post(
            reverse("remove_from_cart", args=[self.cart_item.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)


