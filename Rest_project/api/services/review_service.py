def _imports():
    from ..models import Review, OrderItem
    return Review, OrderItem


def get_user_reviews(user):
    Review, _ = _imports()
    return Review.objects.filter(user=user).select_related("menu__item", "menu__category").order_by("-created_at")


def add_review(user, menu, rating, comment=""):
    from django.db import IntegrityError
    Review, OrderItem = _imports()
    if not OrderItem.objects.filter(order__user=user, menu=menu).exists():
        raise ValueError("You can only review items you have ordered.")

    if Review.objects.filter(user=user, menu=menu).exists():
        raise ValueError("You already reviewed this item")

    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    try:
        return Review.objects.create(
            user=user,
            menu=menu,
            rating=rating,
            comment=comment,
        )
    except IntegrityError:
        raise ValueError("You already reviewed this item")


def update_review(review, rating, comment=""):
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    review.rating = rating
    review.comment = comment
    review.save()


def delete_review(review):
    review.delete()


def get_review(user, review_id):
    from django.core.exceptions import ObjectDoesNotExist
    Review, _ = _imports()
    try:
        return Review.objects.get(id=review_id, user=user)
    except ObjectDoesNotExist:
        return None
