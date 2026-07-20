from django.shortcuts import render, get_object_or_404
from ..services import menu_service


def menu_list(request):
    categories = menu_service.get_all_categories()
    category_id = request.GET.get("category")
    search = request.GET.get("search")
    sort = request.GET.get("sort", "")

    items = menu_service.get_available_menu_items(
        category_id=category_id,
        search=search,
        sort=sort,
    )

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
    detail = menu_service.get_menu_detail(item_id, user=request.user)
    if not detail:
        from django.http import Http404
        raise Http404("Menu item not found")
    return render(request, "menu/menu_detail.html", {
        "item": detail["item"],
        "options": detail["options"],
        "reviews": detail["reviews"],
        "avg_rating": detail["avg_rating"],
        "user_review": detail["user_review"],
    })