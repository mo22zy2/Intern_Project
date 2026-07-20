from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import PaymentMethod
from ..services import payment_service


@login_required(login_url="login")
def payment_methods(request):
    methods = payment_service.get_user_payment_methods(request.user)
    return render(request, "payment/payment_methods.html", {"methods": methods})


@login_required(login_url="login")
def add_payment_method(request):
    if request.method != "POST":
        return redirect("payment_methods")

    card_number = request.POST.get("card_number", "").strip()
    cardholder_name = request.POST.get("cardholder_name", "").strip()
    expiry = request.POST.get("expiry", "").strip()
    cvv = request.POST.get("cvv", "").strip()
    make_default = request.POST.get("is_default") == "on"

    if not all([card_number, cardholder_name, expiry, cvv]):
        messages.error(request, _("All card fields are required."))
        return redirect("payment_methods")

    try:
        payment_service.add_payment_method(request.user, card_number, make_default)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("payment_methods")

    messages.success(request, _("Card saved."))
    return redirect("payment_methods")


@login_required(login_url="login")
def delete_payment_method(request, method_id):
    method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    if request.method == "POST":
        try:
            payment_service.delete_payment_method(request.user, method_id)
            messages.success(request, _("Card removed."))
        except PaymentMethod.DoesNotExist:
            pass

    return redirect("payment_methods")


@login_required(login_url="login")
def set_default_payment_method(request, method_id):
    method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    if request.method == "POST":
        try:
            payment_service.set_default_payment_method(request.user, method_id)
            messages.success(request, _("Default card updated."))
        except PaymentMethod.DoesNotExist:
            pass

    return redirect("payment_methods")
