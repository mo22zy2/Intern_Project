from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.utils.translation import gettext as _
from ..models import Review, Menu


@login_required(login_url="login")
def add_review(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)

    if request.method != "POST":
        return redirect("menu_detail", item_id=menu_id)

    if Review.objects.filter(user=request.user, menu=menu).exists():
        messages.error(request, _("You already reviewed this item."))
        return redirect("menu_detail", item_id=menu_id)

    try:
        rating = int(request.POST.get("rating", 0))
    except (ValueError, TypeError):
        rating = 0

    if rating < 1 or rating > 5:
        messages.error(request, _("Rating must be between 1 and 5."))
        return redirect("menu_detail", item_id=menu_id)

    comment = request.POST.get("comment", "").strip()

    Review.objects.create(
        user=request.user,
        menu=menu,
        rating=rating,
        comment=comment,
    )

    messages.success(request, _("Review submitted."))
    return redirect("menu_detail", item_id=menu_id)


@login_required(login_url="login")
def my_reviews(request):
    reviews = Review.objects.filter(user=request.user).select_related("menu__item", "menu__category").order_by("-created_at")
    return render(request, "reviews/my_reviews.html", {"reviews": reviews})


@login_required(login_url="login")
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating", 0))
        except (ValueError, TypeError):
            rating = 0

        if rating < 1 or rating > 5:
            messages.error(request, _("Rating must be between 1 and 5."))
            return redirect("my_reviews")

        review.rating = rating
        review.comment = request.POST.get("comment", "").strip()
        review.save()

        messages.success(request, _("Review updated."))
        return redirect("my_reviews")

    return render(request, "reviews/edit_review.html", {"review": review})


@login_required(login_url="login")
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == "POST":
        review.delete()
        messages.success(request, _("Review deleted."))

    return redirect("my_reviews")
