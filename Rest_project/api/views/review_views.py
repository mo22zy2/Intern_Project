from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import Menu, Review
from ..services import review_service


@login_required(login_url="login")
def add_review(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)

    if request.method != "POST":
        return redirect("menu_detail", item_id=menu_id)

    try:
        rating = int(request.POST.get("rating", 0))
    except (ValueError, TypeError):
        rating = 0

    try:
        review_service.add_review(
            user=request.user,
            menu=menu,
            rating=rating,
            comment=request.POST.get("comment", "").strip(),
        )
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("menu_detail", item_id=menu_id)

    messages.success(request, _("Review submitted."))
    return redirect("menu_detail", item_id=menu_id)


@login_required(login_url="login")
def my_reviews(request):
    reviews = review_service.get_user_reviews(request.user)
    return render(request, "reviews/my_reviews.html", {"reviews": reviews})


@login_required(login_url="login")
def edit_review(request, review_id):
    review = review_service.get_review(request.user, review_id)
    if not review:
        get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating", 0))
        except (ValueError, TypeError):
            rating = 0

        try:
            review_service.update_review(
                review,
                rating=rating,
                comment=request.POST.get("comment", "").strip(),
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("my_reviews")

        messages.success(request, _("Review updated."))
        return redirect("my_reviews")

    return render(request, "reviews/edit_review.html", {"review": review})


@login_required(login_url="login")
def delete_review(request, review_id):
    review = review_service.get_review(request.user, review_id)
    if not review:
        get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == "POST":
        review_service.delete_review(review)
        messages.success(request, _("Review deleted."))

    return redirect("my_reviews")
