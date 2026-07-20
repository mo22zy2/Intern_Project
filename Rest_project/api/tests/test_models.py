from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from api.models import Category, Inventory, Menu, UserSettings, \
    MenuCustomizationOption, Cart, CartItem, Order, OrderItem, \
    ReservationSystem, Review, PaymentMethod, Payment


class UserModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            phone="123456789",
            birth="1990-01-15",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.phone, "123456789")
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")

    def test_user_str(self):
        self.assertEqual(str(self.user), self.user.username)

    def test_user_birth_field(self):
        self.assertEqual(str(self.user.birth), "1990-01-15")

    def test_user_birth_nullable(self):
        user2 = get_user_model().objects.create_user(
            username="nobirth", password="testpass123"
        )
        self.assertIsNone(user2.birth)

    def test_user_phone_blank(self):
        user2 = get_user_model().objects.create_user(
            username="nophone", password="testpass123"
        )
        self.assertEqual(user2.phone, "")

    def test_user_created_at_auto(self):
        self.assertIsNotNone(self.user.created_at)

    def test_user_unique_username(self):
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(
                username="testuser",
                password="testpass123"
            )


class UserSettingsModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.settings = UserSettings.objects.create(
            user=self.user, dark_mode=True, locale="fr"
        )

    def test_user_settings_creation(self):
        self.assertTrue(self.settings.dark_mode)
        self.assertEqual(self.settings.locale, "fr")
        self.assertEqual(self.settings.user, self.user)

    def test_user_settings_defaults(self):
        user2 = get_user_model().objects.create_user(
            username="user2", password="testpass123"
        )
        settings2 = UserSettings.objects.create(user=user2)
        self.assertFalse(settings2.dark_mode)
        self.assertEqual(settings2.locale, "en")

    def test_user_settings_one_to_one(self):
        with self.assertRaises(Exception):
            UserSettings.objects.create(user=self.user)

    def test_user_settings_cascade_delete(self):
        self.user.delete()
        self.assertEqual(UserSettings.objects.count(), 0)


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name="Main Course")

    def test_category_creation(self):
        self.assertEqual(self.category.category_name, "Main Course")

    def test_category_unique_name(self):
        with self.assertRaises(Exception):
            Category.objects.create(category_name="Main Course")

    def test_category_str(self):
        self.assertEqual(str(self.category), self.category.category_name)


class InventoryModelTest(TestCase):
    def setUp(self):
        self.item = Inventory.objects.create(
            item_name="Chicken Breast", item_count=50, ordered=10
        )

    def test_inventory_creation(self):
        self.assertEqual(self.item.item_name, "Chicken Breast")
        self.assertEqual(self.item.item_count, 50)
        self.assertEqual(self.item.ordered, 10)

    def test_inventory_defaults(self):
        item2 = Inventory.objects.create(item_name="Tomato")
        self.assertEqual(item2.item_count, 0)
        self.assertEqual(item2.ordered, 0)

    def test_inventory_unique_item_name(self):
        with self.assertRaises(Exception):
            Inventory.objects.create(item_name="Chicken Breast")


class MenuModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(category_name="Main Course")
        self.inventory = Inventory.objects.create(
            item_name="Chicken Breast", item_count=50, ordered=10
        )
        self.menu = Menu.objects.create(
            item=self.inventory, category=self.category, price=15.99,
            available=True
        )

    def test_menu_creation(self):
        self.assertEqual(self.menu.price, 15.99)
        self.assertTrue(self.menu.available)
        self.assertEqual(self.menu.popularity_score, 0)

    def test_menu_defaults(self):
        menu2 = Menu.objects.create(
            item=self.inventory, category=self.category, price=9.99
        )
        self.assertTrue(menu2.available)
        self.assertEqual(menu2.popularity_score, 0)
        self.assertEqual(
            menu2.image_url,
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZFcnA0ic2J7aKFnIbiQe_162HCFpokxlijmoaPNz07Q&s=10"
        )

    def test_menu_category_relation(self):
        self.assertEqual(self.menu.category.category_name, "Main Course")

    def test_menu_inventory_relation(self):
        self.assertEqual(self.menu.item.item_name, "Chicken Breast")

    def test_menu_created_at_auto(self):
        self.assertIsNotNone(self.menu.created_at)

    def test_menu_category_delete_cascade(self):
        self.category.delete()
        self.assertEqual(Menu.objects.count(), 0)

    def test_menu_inventory_delete_cascade(self):
        self.inventory.delete()
        self.assertEqual(Menu.objects.count(), 0)


class MenuCustomizationOptionModelTest(TestCase):
    def setUp(self):
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.option = MenuCustomizationOption.objects.create(
            menu=self.menu, option_name="Extra Cheese", extra_price=2.50
        )

    def test_option_creation(self):
        self.assertEqual(self.option.option_name, "Extra Cheese")
        self.assertEqual(self.option.extra_price, 2.50)
        self.assertEqual(self.option.menu, self.menu)

    def test_option_default_extra_price(self):
        option2 = MenuCustomizationOption.objects.create(
            menu=self.menu, option_name="No Onions"
        )
        self.assertEqual(option2.extra_price, 0)

    def test_option_menu_delete_cascade(self):
        self.menu.delete()
        self.assertEqual(MenuCustomizationOption.objects.count(), 0)


class CartModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)

    def test_cart_one_to_one(self):
        with self.assertRaises(Exception):
            Cart.objects.create(user=self.user)

    def test_cart_updated_at_auto(self):
        self.assertIsNotNone(self.cart.updated_at)

    def test_cart_user_delete_cascade(self):
        self.user.delete()
        self.assertEqual(Cart.objects.count(), 0)


class CartItemModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.cart = Cart.objects.create(user=self.user)

        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.cart_item = CartItem.objects.create(
            cart=self.cart, menu=self.menu, quantity=2
        )

    def test_cart_item_creation(self):
        self.assertEqual(self.cart_item.quantity, 2)
        self.assertEqual(self.cart_item.menu, self.menu)
        self.assertEqual(self.cart_item.cart, self.cart)

    def test_cart_item_default_quantity(self):
        item2 = CartItem.objects.create(cart=self.cart, menu=self.menu)
        self.assertEqual(item2.quantity, 1)

    def test_cart_item_default_options_text(self):
        self.assertEqual(self.cart_item.options_text, "")

    def test_cart_item_null_option(self):
        self.assertIsNone(self.cart_item.option)

    def test_cart_item_cart_delete_cascade(self):
        self.cart.delete()
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cart_item_menu_delete_cascade(self):
        self.menu.delete()
        self.assertEqual(CartItem.objects.count(), 0)


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.order = Order.objects.create(
            user=self.user, delivery_address="123 Main St", total_price=31.98
        )

    def test_order_creation(self):
        self.assertEqual(self.order.total_price, 31.98)
        self.assertEqual(self.order.status, "pending")
        self.assertEqual(self.order.user, self.user)

    def test_order_default_delivery_type(self):
        self.assertEqual(self.order.delivery_type, "delivery")

    def test_order_default_delivery_address(self):
        self.assertEqual(self.order.delivery_address, "123 Main St")

    def test_order_qr_data_null(self):
        self.assertIsNone(self.order.qr_data)

    def test_order_reservation_null(self):
        self.assertIsNone(self.order.reservation)

    def test_order_created_at_auto(self):
        self.assertIsNotNone(self.order.created_at)

    def test_order_user_delete_cascade(self):
        self.user.delete()
        self.assertEqual(Order.objects.count(), 0)


class OrderItemModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.order = Order.objects.create(
            user=self.user, delivery_address="123 Main St", total_price=31.98
        )
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, menu=self.menu, quantity=2, unit_price=15.99
        )

    def test_order_item_creation(self):
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.unit_price, 15.99)
        self.assertEqual(self.order_item.menu, self.menu)
        self.assertEqual(self.order_item.order, self.order)

    def test_order_item_null_option(self):
        self.assertIsNone(self.order_item.option)

    def test_order_item_default_options_text(self):
        self.assertEqual(self.order_item.options_text, "")

    def test_order_item_order_delete_cascade(self):
        self.order.delete()
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_order_item_menu_delete_cascade(self):
        self.menu.delete()
        self.assertEqual(OrderItem.objects.count(), 0)


class ReservationSystemModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.reservation = ReservationSystem.objects.create(
            user=self.user, reservation_date="2025-12-25",
            reservation_time="19:00", seats=4
        )

    def test_reservation_creation(self):
        self.assertEqual(self.reservation.seats, 4)
        self.assertEqual(self.reservation.user, self.user)
        self.assertEqual(str(self.reservation.reservation_date), "2025-12-25")
        self.assertIsNotNone(self.reservation.reservation_time)

    def test_reservation_default_status(self):
        self.assertEqual(self.reservation.status, "pending")

    def test_reservation_created_at_auto(self):
        self.assertIsNotNone(self.reservation.created_at)

    def test_reservation_user_delete_cascade(self):
        self.user.delete()
        self.assertEqual(ReservationSystem.objects.count(), 0)


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        category = Category.objects.create(category_name="Main Course")
        inventory = Inventory.objects.create(item_name="Chicken Breast")
        self.menu = Menu.objects.create(
            item=inventory, category=category, price=15.99
        )
        self.review = Review.objects.create(
            user=self.user, menu=self.menu, rating=5,
            comment="Delicious!"
        )

    def test_review_creation(self):
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, "Delicious!")
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.menu, self.menu)

    def test_review_created_at_auto(self):
        self.assertIsNotNone(self.review.created_at)

    def test_review_comment_blank(self):
        inventory2 = Inventory.objects.create(item_name="Steak")
        menu2 = Menu.objects.create(
            item=inventory2, category=self.menu.category, price=25.99
        )
        review2 = Review.objects.create(
            user=self.user, menu=menu2, rating=3
        )
        self.assertEqual(review2.comment, "")

    def test_review_unique_together(self):
        with self.assertRaises(Exception):
            Review.objects.create(
                user=self.user, menu=self.menu, rating=4
            )

    def test_review_related_name(self):
        self.assertIn(self.review, self.menu.reviews.all())

    def test_review_user_delete_cascade(self):
        self.user.delete()
        self.assertEqual(Review.objects.count(), 0)

    def test_review_menu_delete_cascade(self):
        self.menu.delete()
        self.assertEqual(Review.objects.count(), 0)


class PaymentMethodModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user, method_type="Credit Card", is_default=True
        )

    def test_payment_method_creation(self):
        self.assertEqual(self.payment_method.method_type, "Credit Card")
        self.assertTrue(self.payment_method.is_default)
        self.assertEqual(self.payment_method.user, self.user)

    def test_payment_method_default_is_default(self):
        method2 = PaymentMethod.objects.create(
            user=self.user, method_type="PayPal"
        )
        self.assertFalse(method2.is_default)

    def test_payment_method_user_delete_cascade(self):
        self.user.delete()
        self.assertEqual(PaymentMethod.objects.count(), 0)


class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        self.order = Order.objects.create(
            user=self.user, delivery_address="123 Main St", total_price=31.98
        )
        self.payment_method = PaymentMethod.objects.create(
            user=self.user, method_type="Credit Card", is_default=True
        )
        self.payment = Payment.objects.create(
            order=self.order, payment_method=self.payment_method,
            amount=31.98, status="completed"
        )

    def test_payment_creation(self):
        self.assertEqual(self.payment.amount, 31.98)
        self.assertEqual(self.payment.status, "completed")
        self.assertEqual(self.payment.order, self.order)
        self.assertEqual(self.payment.payment_method, self.payment_method)

    def test_payment_default_status(self):
        order2 = Order.objects.create(
            user=self.user, delivery_address="456 Oak St", total_price=15.99
        )
        payment2 = Payment.objects.create(
            order=order2, payment_method=self.payment_method, amount=15.99
        )
        self.assertEqual(payment2.status, "pending")

    def test_payment_paid_at_null(self):
        self.assertIsNone(self.payment.paid_at)

    def test_payment_one_to_one_order(self):
        with self.assertRaises(Exception):
            Payment.objects.create(
                order=self.order, payment_method=self.payment_method,
                amount=31.98
            )

    def test_payment_order_delete_cascade(self):
        self.order.delete()
        self.assertEqual(Payment.objects.count(), 0)

    def test_payment_method_delete_cascade(self):
        self.payment_method.delete()
        self.assertEqual(Payment.objects.count(), 0)
