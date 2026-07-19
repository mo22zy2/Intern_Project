from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    dark_mode = models.BooleanField(default=False)
    locale = models.CharField(max_length=10, default="en")


class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.category_name


class Inventory(models.Model):
    item_name = models.CharField(max_length=100, unique=True)
    item_count = models.IntegerField(default=0)
    ordered = models.IntegerField(default=0)


class Menu(models.Model):
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500, null=False, default="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZFcnA0ic2J7aKFnIbiQe_162HCFpokxlijmoaPNz07Q&s=10")
    price = models.FloatField()
    popularity_score = models.IntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MenuCustomizationOption(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    option_name = models.CharField(max_length=100)
    extra_price = models.FloatField(default=0)


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    option = models.ForeignKey(
        MenuCustomizationOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    quantity = models.IntegerField(default=1)
    options_text = models.CharField(max_length=500, blank=True, default="")


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_type = models.CharField(max_length=20, default="delivery")
    delivery_address = models.TextField(blank=True, default="")
    reservation = models.ForeignKey("ReservationSystem", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default="confirmed")
    total_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    qr_data = models.TextField(blank=True, null=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    option = models.ForeignKey(
        MenuCustomizationOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    options_text = models.CharField(max_length=500, blank=True, default="")


class ReservationSystem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    seats = models.IntegerField()
    status = models.CharField(max_length=20, default="confirmed")
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "menu")


class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method_type = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    amount = models.FloatField()
    status = models.CharField(max_length=20, default="pending")
    paid_at = models.DateTimeField(null=True, blank=True)
