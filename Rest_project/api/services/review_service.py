def _imports():
    from ..models import Review
    return Review,


def get_user_reviews(user):
    Review, = _imports()
    return Review.objects.filter(user=user).select_related("menu__item", "menu__category").order_by("-created_at")


def add_review(user, menu, rating, comment=""):
    Review, = _imports()
    if Review.objects.filter(user=user, menu=menu).exists():
        raise ValueError("You already reviewed this item")

    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    return Review.objects.create(
        user=user,
        menu=menu,
        rating=rating,
        comment=comment,
    )


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
    Review, = _imports()
    try:
        return Review.objects.get(id=review_id, user=user)
    except ObjectDoesNotExist:
        return None
