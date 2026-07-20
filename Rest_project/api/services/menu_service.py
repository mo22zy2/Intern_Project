def _imports():
    from django.db.models import Avg
    from ..models import Menu, Category, MenuCustomizationOption, Review
    return Avg, Menu, Category, MenuCustomizationOption, Review


def get_available_menu_items(category_id=None, search=None, sort=""):
    Avg, Menu, Category, MenuCustomizationOption, Review = _imports()
    items = Menu.objects.select_related("item", "category").filter(available=True)

    if category_id:
        items = items.filter(category_id=category_id)
    if search:
        items = items.filter(item__item_name__icontains=search)

    if sort == "price_low":
        items = items.order_by("price")
    elif sort == "price_high":
        items = items.order_by("-price")
    elif sort == "newest":
        items = items.order_by("-created_at")
    else:
        items = items.order_by("-popularity_score")

    items = items.annotate(avg_rating=Avg("reviews__rating"))
    return items


def get_menu_detail(item_id, user=None):
    from django.core.exceptions import ObjectDoesNotExist
    Avg, Menu, Category, MenuCustomizationOption, Review = _imports()
    try:
        item = Menu.objects.select_related("item", "category").get(id=item_id, available=True)
    except ObjectDoesNotExist:
        return None
    options = MenuCustomizationOption.objects.filter(menu=item)
    reviews = Review.objects.filter(menu=item).select_related("user").order_by("-created_at")
    avg_rating = Review.objects.filter(menu=item).aggregate(Avg("rating"))["rating__avg"]
    user_review = None
    if user and user.is_authenticated:
        user_review = Review.objects.filter(menu=item, user=user).first()
    return {
        "item": item,
        "options": options,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "user_review": user_review,
    }


def get_all_categories():
    _, _, Category, _, _ = _imports()
    return Category.objects.all()


def get_featured_items():
    Avg, Menu, _, _, _ = _imports()
    return Menu.objects.select_related("item", "category").filter(available=True).annotate(
        avg_rating=Avg("reviews__rating")
    ).order_by("-popularity_score")[:4]


def get_total_menu_items_count():
    _, Menu, _, _, _ = _imports()
    return Menu.objects.filter(available=True).count()


def get_total_categories_count():
    _, _, Category, _, _ = _imports()
    return Category.objects.count()


def get_menu_item_by_id(item_id):
    _, Menu, _, _, _ = _imports()
    return Menu.objects.select_related("item", "category").filter(id=item_id, available=True).first()
