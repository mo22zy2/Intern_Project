def _imports():
    from ..models import PaymentMethod, Payment
    return PaymentMethod, Payment


def get_user_payment_methods(user):
    PaymentMethod, _ = _imports()
    return PaymentMethod.objects.filter(user=user)


def add_payment_method(user, card_number, make_default=False):
    PaymentMethod, _ = _imports()
    digits = "".join(c for c in card_number if c.isdigit())
    if len(digits) < 13:
        raise ValueError("Invalid card number")
    last_four = digits[-4:]
    method_type = f"\u2022\u2022\u2022\u2022 {last_four}"

    if make_default:
        PaymentMethod.objects.filter(user=user).update(is_default=False)

    return PaymentMethod.objects.create(
        user=user,
        method_type=method_type,
        is_default=make_default,
    )


def delete_payment_method(user, method_id):
    PaymentMethod, _ = _imports()
    method = PaymentMethod.objects.get(id=method_id, user=user)
    method.delete()


def set_default_payment_method(user, method_id):
    PaymentMethod, _ = _imports()
    method = PaymentMethod.objects.get(id=method_id, user=user)
    PaymentMethod.objects.filter(user=user).update(is_default=False)
    method.is_default = True
    method.save()


def get_or_create_cash_method(user):
    PaymentMethod, _ = _imports()
    method, _ = PaymentMethod.objects.get_or_create(
        user=user,
        method_type="Cash on Restaurant",
    )
    return method


def create_or_get_card_method(user, card_number):
    PaymentMethod, _ = _imports()
    digits = "".join(c for c in card_number if c.isdigit())
    if len(digits) < 13:
        raise ValueError("Invalid card number")
    last_four = digits[-4:]
    method_type = f"\u2022\u2022\u2022\u2022 {last_four}"
    return PaymentMethod.objects.create(
        user=user,
        method_type=method_type,
    )


def create_payment(order, payment_method, amount, status="completed", paid_at=None):
    from django.utils import timezone
    _, Payment = _imports()
    if amount is not None and amount <= 0:
        raise ValueError("Invalid amount")
    return Payment.objects.create(
        order=order,
        payment_method=payment_method,
        amount=amount,
        status=status,
        paid_at=paid_at or timezone.now() if status == "completed" else None,
    )


def get_user_payments(user):
    _, Payment = _imports()
    return Payment.objects.filter(order__user=user).select_related("order").order_by("-paid_at")
