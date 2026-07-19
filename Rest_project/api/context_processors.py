from django.conf import settings
from .models import Cart


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.cartitem_set.count()
    return {"cart_count": count}


def chat_api_url(request):
    return {"CHAT_API_URL": settings.CHAT_API_URL}
