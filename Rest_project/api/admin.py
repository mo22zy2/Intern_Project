from django.contrib import admin
from .models import User, UserSettings, Category, Inventory, Menu, \
    MenuCustomizationOption, Cart, CartItem, Order, OrderItem, \
    ReservationSystem, PaymentMethod, Payment

admin.site.register(User)
admin.site.register(UserSettings)
admin.site.register(Category)
admin.site.register(Inventory)
admin.site.register(Menu)
admin.site.register(MenuCustomizationOption)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ReservationSystem)
admin.site.register(PaymentMethod)
admin.site.register(Payment)
