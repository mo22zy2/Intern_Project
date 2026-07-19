from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import PaymentMethod


@login_required(login_url="login")
def payment_methods(request):
    methods = PaymentMethod.objects.filter(user=request.user)
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

    digits = "".join(c for c in card_number if c.isdigit())
    if len(digits) < 13:
        messages.error(request, _("Invalid card number."))
        return redirect("payment_methods")

    last_four = digits[-4:]
    method_type = f"•••• {last_four}"

    if make_default:
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)

    PaymentMethod.objects.create(
        user=request.user,
        method_type=method_type,
        is_default=make_default,
    )

    messages.success(request, _("Card saved."))
    return redirect("payment_methods")


@login_required(login_url="login")
def delete_payment_method(request, method_id):
    method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    if request.method == "POST":
        method.delete()
        messages.success(request, _("Card removed."))

    return redirect("payment_methods")


@login_required(login_url="login")
def set_default_payment_method(request, method_id):
    method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    if request.method == "POST":
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)
        method.is_default = True
        method.save()
        messages.success(request, _("Default card updated."))

    return redirect("payment_methods")
