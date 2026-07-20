from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate


def _imports():
    from ..models import User, Order, OrderItem, ReservationSystem, Menu, Category, Inventory, Payment
    return User, Order, OrderItem, ReservationSystem, Menu, Category, Inventory, Payment


def get_dashboard_stats():
    User, Order, OrderItem, ReservationSystem, Menu, Category, Inventory, Payment = _imports()
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Payment.objects.filter(status="completed").aggregate(s=Sum("amount"))["s"] or 0
    total_menu_items = Menu.objects.count()
    low_stock = Inventory.objects.filter(item_count__lt=10).count()
    total_reservations = ReservationSystem.objects.count()

    orders_today = Order.objects.filter(created_at__date=now.date()).count()
    revenue_today = Payment.objects.filter(
        status="completed", paid_at__date=now.date()
    ).aggregate(s=Sum("amount"))["s"] or 0

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_menu_items": total_menu_items,
        "low_stock": low_stock,
        "total_reservations": total_reservations,
        "orders_today": orders_today,
        "revenue_today": revenue_today,
    }


def get_revenue_last_30_days():
    _, _, _, _, _, _, _, Payment = _imports()
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    days = []
    for i in range(29, -1, -1):
        d = (now - timedelta(days=i)).date()
        days.append(d)
    data = (
        Payment.objects
        .filter(status="completed", paid_at__date__gte=thirty_days_ago.date())
        .annotate(date=TruncDate("paid_at"))
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )
    lookup = {row["date"]: row["total"] for row in data}
    result = []
    for d in days:
        result.append({"date": d.isoformat(), "total": float(lookup.get(d, 0))})
    return result


def get_order_status_counts():
    _, Order, _, _, _, _, _, _ = _imports()
    qs = Order.objects.values("status").annotate(count=Count("id")).order_by("status")
    return {row["status"]: row["count"] for row in qs}


def get_top_selling_items(limit=10):
    _, _, OrderItem, _, _, _, Inventory, _ = _imports()
    return list(
        Inventory.objects.filter(ordered__gt=0)
        .order_by("-ordered")[:limit]
        .values("item_name", "ordered")
    )


def get_recent_orders(limit=10):
    _, Order, _, _, _, _, _, _ = _imports()
    return Order.objects.select_related("user").order_by("-created_at")[:limit]


def get_all_orders():
    _, Order, _, _, _, _, _, _ = _imports()
    return Order.objects.select_related("user", "reservation").order_by("-created_at")


VALID_ORDER_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": [],
    "cancelled": [],
}


def update_order_status(order_id, new_status):
    _, Order, _, _, _, _, Inventory, _ = _imports()
    try:
        order = Order.objects.prefetch_related("orderitem_set__menu__item").get(id=order_id)
    except Order.DoesNotExist:
        raise ValueError("Order not found")
    allowed = VALID_ORDER_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot change order from '{order.status}' to '{new_status}'"
        )

    if new_status == "confirmed" and order.status == "pending":
        for item in order.orderitem_set.all():
            inv = item.menu.item
            inv.item_count = max(0, (inv.item_count or 0) - item.quantity)
            inv.save(update_fields=["item_count"])

    order.status = new_status
    order.save(update_fields=["status"])
    return order


def get_all_reservations():
    _, _, _, ReservationSystem, _, _, _, _ = _imports()
    return ReservationSystem.objects.select_related("user").order_by("-created_at")


def update_reservation_status(reservation_id, new_status):
    _, _, _, ReservationSystem, _, _, _, _ = _imports()
    try:
        reservation = ReservationSystem.objects.get(id=reservation_id)
    except ReservationSystem.DoesNotExist:
        raise ValueError("Reservation not found")
    if reservation.status not in ("pending",):
        raise ValueError(
            f"Cannot change reservation from '{reservation.status}'"
        )
    if new_status not in ("confirmed", "cancelled"):
        raise ValueError(f"Invalid status '{new_status}'")
    reservation.status = new_status
    reservation.save(update_fields=["status"])
    return reservation


def get_all_menu_items_admin():
    _, _, _, _, Menu, _, _, _ = _imports()
    return Menu.objects.select_related("item", "category").order_by("-created_at")


def add_menu_item(item_name, category_id, price, image_url, available, stock_count=0):
    _, _, _, _, Menu, Category, Inventory, _ = _imports()
    inventory, _ = Inventory.objects.get_or_create(item_name=item_name)
    inventory.item_count = stock_count
    inventory.save()
    category = Category.objects.get(id=category_id)
    return Menu.objects.create(
        item=inventory,
        category=category,
        price=price,
        image_url=image_url or "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQZFcnA0ic2J7aKFnIbiQe_162HCFpokxlijmoaPNz07Q&s=10",
        available=available,
    )


def delete_menu_item(item_id):
    _, _, _, _, Menu, _, _, _ = _imports()
    try:
        menu = Menu.objects.get(id=item_id)
        menu.delete()
    except Menu.DoesNotExist:
        raise ValueError("Menu item not found")


def toggle_menu_availability(item_id):
    _, _, _, _, Menu, _, _, _ = _imports()
    try:
        menu = Menu.objects.get(id=item_id)
        menu.available = not menu.available
        menu.save(update_fields=["available"])
        return menu
    except Menu.DoesNotExist:
        raise ValueError("Menu item not found")


def get_all_inventory():
    _, _, _, _, _, _, Inventory, _ = _imports()
    return Inventory.objects.order_by("item_name")


def update_inventory_stock(inventory_id, item_count):
    _, _, _, _, _, _, Inventory, _ = _imports()
    try:
        inv = Inventory.objects.get(id=inventory_id)
    except Inventory.DoesNotExist:
        raise ValueError("Inventory item not found")
    inv.item_count = item_count
    inv.save(update_fields=["item_count"])
    return inv


# ── Categories CRUD ──────────────────────────────────────────────

def get_all_categories():
    _, _, _, _, _, Category, _, _ = _imports()
    return Category.objects.order_by("category_name")


def add_category(category_name):
    _, _, _, _, _, Category, _, _ = _imports()
    name = category_name.strip()
    if not name:
        raise ValueError("Category name is required")
    if Category.objects.filter(category_name__iexact=name).exists():
        raise ValueError(f"Category '{name}' already exists")
    return Category.objects.create(category_name=name)


def update_category(category_id, category_name):
    _, _, _, _, _, Category, _, _ = _imports()
    name = category_name.strip()
    if not name:
        raise ValueError("Category name is required")
    try:
        cat = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise ValueError("Category not found")
    if Category.objects.filter(category_name__iexact=name).exclude(id=category_id).exists():
        raise ValueError(f"Category '{name}' already exists")
    cat.category_name = name
    cat.save(update_fields=["category_name"])
    return cat


def delete_category(category_id):
    _, _, _, _, Menu, Category, _, _ = _imports()
    try:
        cat = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        raise ValueError("Category not found")
    if Menu.objects.filter(category=cat).exists():
        raise ValueError("Cannot delete category with existing menu items")
    cat.delete()


# ── Customizations CRUD ─────────────────────────────────────────

def get_customizations_for_menu(menu_id):
    from ..models import MenuCustomizationOption
    _, _, _, _, Menu, _, _, _ = _imports()
    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        raise ValueError("Menu item not found")
    options = MenuCustomizationOption.objects.filter(menu=menu).order_by("option_name")
    return menu, options


def add_customization(menu_id, option_name, extra_price=0):
    from ..models import MenuCustomizationOption
    _, _, _, _, Menu, _, _, _ = _imports()
    try:
        menu = Menu.objects.get(id=menu_id)
    except Menu.DoesNotExist:
        raise ValueError("Menu item not found")
    name = option_name.strip()
    if not name:
        raise ValueError("Option name is required")
    try:
        extra_price = float(extra_price)
    except (ValueError, TypeError):
        raise ValueError("Invalid extra price")
    return MenuCustomizationOption.objects.create(
        menu=menu, option_name=name, extra_price=extra_price
    )


def delete_customization(customization_id):
    from ..models import MenuCustomizationOption
    try:
        opt = MenuCustomizationOption.objects.get(id=customization_id)
        opt.delete()
    except MenuCustomizationOption.DoesNotExist:
        raise ValueError("Customization option not found")


# ── User Management ──────────────────────────────────────────────

def get_all_users():
    User, _, _, _, _, _, _, _ = _imports()
    return User.objects.order_by("-date_joined")


def toggle_user_staff(user_id):
    User, _, _, _, _, _, _, _ = _imports()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError("User not found")
    u.is_staff = not u.is_staff
    u.save(update_fields=["is_staff"])
    return u


def toggle_user_active(user_id):
    User, _, _, _, _, _, _, _ = _imports()
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError("User not found")
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    return u


# ── Reports ──────────────────────────────────────────────────────

def get_sales_report(days=30):
    _, Order, OrderItem, _, _, _, _, Payment = _imports()
    now = timezone.now()
    since = now - timedelta(days=days)
    orders = Order.objects.filter(created_at__gte=since)
    total_orders = orders.count()
    total_revenue = Payment.objects.filter(
        status="completed", paid_at__gte=since
    ).aggregate(s=Sum("amount"))["s"] or 0
    by_status = (
        orders.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    daily = (
        orders.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            count=Count("id"),
            revenue=Sum("total_price"),
        )
        .order_by("date")
    )
    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "by_status": list(by_status),
        "daily": list(daily),
    }


def get_feedback_report(days=30):
    from ..models import Review
    now = timezone.now()
    since = now - timedelta(days=days)
    reviews = Review.objects.filter(created_at__gte=since).select_related("user", "menu__item")
    total = reviews.count()
    avg_rating = reviews.aggregate(a=Sum("rating"))["a"] or 0
    avg_rating = round(avg_rating / total, 1) if total else 0
    rating_dist = (
        reviews.values("rating")
        .annotate(count=Count("id"))
        .order_by("rating")
    )
    return {
        "total_reviews": total,
        "avg_rating": avg_rating,
        "rating_dist": list(rating_dist),
        "reviews": list(reviews.order_by("-created_at")[:20]),
    }


def get_reservation_report(days=30):
    _, _, _, ReservationSystem, _, _, _, _ = _imports()
    now = timezone.now()
    since = now - timedelta(days=days)
    reservations = ReservationSystem.objects.filter(created_at__gte=since)
    total = reservations.count()
    by_status = (
        reservations.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    return {
        "total_reservations": total,
        "by_status": list(by_status),
    }


def get_user_demographics():
    User, _, _, _, _, _, _, _ = _imports()
    total = User.objects.count()
    staff_count = User.objects.filter(is_staff=True).count()
    active_count = User.objects.filter(is_active=True).count()
    return {
        "total_users": total,
        "staff_count": staff_count,
        "active_count": active_count,
        "regular_count": total - staff_count,
    }
