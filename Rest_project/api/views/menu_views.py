from django.shortcuts import render, get_object_or_404
from django.db.models import Avg
from ..models import Menu, Category, MenuCustomizationOption, Review


def menu_list(request):
    categories = Category.objects.all()
    category_id = request.GET.get("category")
    search = request.GET.get("search")
    sort = request.GET.get("sort", "")

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

    selected_category = None
    if category_id and category_id.isdigit():
        selected_category = int(category_id)

    context = {
        "categories": categories,
        "items": items,
        "selected_category": selected_category,
        "search": search or "",
        "sort": sort,
    }
    return render(request, "menu/menu_list.html", context)


def menu_detail(request, item_id):
    item = get_object_or_404(
        Menu.objects.select_related("item", "category"),
        id=item_id,
        available=True,
    )
    options = MenuCustomizationOption.objects.filter(menu=item)
    reviews = Review.objects.filter(menu=item).select_related("user").order_by("-created_at")
    avg_rating = Review.objects.filter(menu=item).aggregate(Avg("rating"))["rating__avg"]
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(menu=item, user=request.user).first()
    return render(request, "menu/menu_detail.html", {
        "item": item,
        "options": options,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "user_review": user_review,
    })