from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import HttpResponse
from ..services import admin_service, menu_service
from ..models import MenuCustomizationOption, ReservationSystem

staff_required = user_passes_test(lambda u: u.is_staff, login_url="login")


@staff_required
def admin_dashboard(request):
    stats = admin_service.get_dashboard_stats()
    revenue_data = admin_service.get_revenue_last_30_days()
    status_counts = admin_service.get_order_status_counts()
    top_items = admin_service.get_top_selling_items()
    recent_orders = admin_service.get_recent_orders()
    demographics = admin_service.get_user_demographics()

    max_revenue = max((r["total"] for r in revenue_data), default=0) or 1
    for r in revenue_data:
        r["pct"] = (r["total"] / max_revenue) * 100

    total_orders = sum(status_counts.values()) or 1
    donut_segments = []
    colors = {
        "pending": "#FFD23F",
        "confirmed": "#4CAF50",
        "cancelled": "#FF5050",
    }
    offset = 0
    for status, count in status_counts.items():
        pct = count / total_orders * 100
        color = colors.get(status, "#888")
        donut_segments.append({
            "color": color,
            "pct": pct,
            "offset": offset,
            "label": status.title(),
            "count": count,
        })
        offset += pct

    # User demographics donut
    total_users = demographics["total_users"] or 1
    user_segments = []
    user_colors = [
        ("Staff", demographics["staff_count"], "#FF5A36"),
        ("Regular", demographics["regular_count"], "#4CAF50"),
    ]
    u_offset = 0
    for label, count, color in user_colors:
        pct = count / total_users * 100
        user_segments.append({
            "color": color,
            "pct": pct,
            "offset": u_offset,
            "label": label,
            "count": count,
        })
        u_offset += pct

    # Line chart data for daily revenue trend
    line_data = []
    for i, r in enumerate(revenue_data):
        line_data.append({
            "date": r["date"],
            "total": r["total"],
            "pct": r["pct"],
        })

    return render(request, "dashboard/dashboard.html", {
        "stats": stats,
        "revenue_data": revenue_data,
        "status_counts": status_counts,
        "top_items": top_items,
        "recent_orders": recent_orders,
        "donut_segments": donut_segments,
        "demographics": demographics,
        "user_segments": user_segments,
        "line_data": line_data,
    })


@staff_required
def admin_orders(request):
    orders = admin_service.get_all_orders()
    return render(request, "dashboard/orders.html", {"orders": orders})


@staff_required
def admin_update_order(request, order_id):
    if request.method != "POST":
        return redirect("admin_orders")
    new_status = request.POST.get("status", "").strip()
    if not new_status:
        messages.error(request, _("Status is required."))
        return redirect("admin_orders")
    try:
        admin_service.update_order_status(order_id, new_status)
        messages.success(request, _("Order #{} status updated.").format(order_id))
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("admin_orders")


@staff_required
def admin_reservations(request):
    reservations = admin_service.get_all_reservations()
    return render(request, "dashboard/reservations.html", {"reservations": reservations})


@staff_required
def admin_update_reservation(request, reservation_id):
    if request.method != "POST":
        return redirect("admin_reservations")
    new_status = request.POST.get("status", "").strip()
    if not new_status:
        messages.error(request, _("Status is required."))
        return redirect("admin_reservations")
    try:
        admin_service.update_reservation_status(reservation_id, new_status)
        messages.success(request, _("Reservation #{} status updated.").format(reservation_id))
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("admin_reservations")


@staff_required
def admin_menu_list(request):
    items = admin_service.get_all_menu_items_admin()
    categories = menu_service.get_all_categories()
    return render(request, "dashboard/menu_list.html", {"items": items, "categories": categories})


@staff_required
def admin_menu_add(request):
    categories = menu_service.get_all_categories()
    if request.method == "POST":
        item_name = request.POST.get("item_name", "").strip()
        category_id = request.POST.get("category")
        price = request.POST.get("price")
        image_url = request.POST.get("image_url", "").strip()
        available = request.POST.get("available") == "on"
        stock_count = request.POST.get("stock_count", 0)

        if not item_name or not category_id or not price:
            messages.error(request, _("Item name, category, and price are required."))
            return render(request, "dashboard/menu_form.html", {"categories": categories})

        try:
            price = float(price)
            stock_count = int(stock_count) if stock_count else 0
        except (ValueError, TypeError):
            messages.error(request, _("Invalid price or stock count."))
            return render(request, "dashboard/menu_form.html", {"categories": categories})

        try:
            admin_service.add_menu_item(item_name, category_id, price, image_url, available, stock_count)
            messages.success(request, _("Menu item added."))
            return redirect("admin_menu_list")
        except ValueError as e:
            messages.error(request, str(e))

    return render(request, "dashboard/menu_form.html", {"categories": categories})


@staff_required
def admin_menu_delete(request, item_id):
    if request.method != "POST":
        return redirect("admin_menu_list")
    try:
        admin_service.delete_menu_item(item_id)
        messages.success(request, _("Menu item deleted."))
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("admin_menu_list")


@staff_required
def admin_menu_toggle(request, item_id):
    if request.method != "POST":
        return redirect("admin_menu_list")
    try:
        menu = admin_service.toggle_menu_availability(item_id)
        status = "available" if menu.available else "unavailable"
        messages.success(request, _("Item is now {}.").format(status))
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("admin_menu_list")


@staff_required
def admin_inventory(request):
    inventory = admin_service.get_all_inventory()
    if request.method == "POST":
        inv_id = request.POST.get("inventory_id")
        item_count = request.POST.get("item_count")
        try:
            admin_service.update_inventory_stock(inv_id, int(item_count))
            messages.success(request, _("Inventory updated."))
        except (ValueError, TypeError) as e:
            messages.error(request, str(e))
        return redirect("admin_inventory")
    return render(request, "dashboard/inventory.html", {"inventory": inventory})


@staff_required
def admin_categories(request):
    categories = admin_service.get_all_categories()
    return render(request, "dashboard/categories.html", {"categories": categories})


@staff_required
def admin_category_add(request):
    if request.method == "POST":
        name = request.POST.get("category_name", "").strip()
        if not name:
            messages.error(request, _("Category name is required."))
            return redirect("admin_categories")
        try:
            admin_service.add_category(name)
            messages.success(request, _("Category '{}' added.").format(name))
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("admin_categories")
    return redirect("admin_categories")


@staff_required
def admin_category_edit(request, category_id):
    if request.method == "POST":
        name = request.POST.get("category_name", "").strip()
        try:
            admin_service.update_category(category_id, name)
            messages.success(request, _("Category updated."))
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("admin_categories")
    return redirect("admin_categories")


@staff_required
def admin_category_delete(request, category_id):
    if request.method == "POST":
        try:
            admin_service.delete_category(category_id)
            messages.success(request, _("Category deleted."))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("admin_categories")


@staff_required
def admin_customizations(request, menu_id):
    try:
        menu, options = admin_service.get_customizations_for_menu(menu_id)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("admin_menu_list")
    return render(request, "dashboard/customizations.html", {
        "menu": menu,
        "options": options,
    })


@staff_required
def admin_customization_add(request, menu_id):
    if request.method == "POST":
        option_name = request.POST.get("option_name", "").strip()
        extra_price = request.POST.get("extra_price", 0)
        try:
            admin_service.add_customization(menu_id, option_name, extra_price)
            messages.success(request, _("Customization added."))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("admin_customizations", menu_id=menu_id)


@staff_required
def admin_customization_delete(request, customization_id):
    if request.method == "POST":
        opt = get_object_or_404(MenuCustomizationOption, id=customization_id)
        menu_id = opt.menu_id
        try:
            admin_service.delete_customization(customization_id)
            messages.success(request, _("Customization deleted."))
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("admin_customizations", menu_id=menu_id)
    return redirect("admin_menu_list")


@staff_required
def admin_users(request):
    users = admin_service.get_all_users()
    return render(request, "dashboard/users.html", {"users": users})


@staff_required
def admin_toggle_staff(request, user_id):
    if request.method == "POST":
        try:
            u = admin_service.toggle_user_staff(user_id)
            status = "staff" if u.is_staff else "regular"
            messages.success(request, _("User is now {}.").format(status))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("admin_users")


@staff_required
def admin_toggle_active(request, user_id):
    if request.method == "POST":
        try:
            u = admin_service.toggle_user_active(user_id)
            status = "active" if u.is_active else "banned"
            messages.success(request, _("User is now {}.").format(status))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("admin_users")


@staff_required
def admin_reports(request):
    report_type = request.GET.get("type", "sales")
    days = int(request.GET.get("days", 30))

    context = {"report_type": report_type, "days": days}

    if report_type == "sales":
        context["data"] = admin_service.get_sales_report(days)
    elif report_type == "inventory":
        context["data"] = admin_service.get_all_inventory()
        context["total_value"] = sum(
            inv.item_count * (getattr(inv, "price", 0) or 0)
            for inv in context["data"]
        )
    elif report_type == "feedback":
        context["data"] = admin_service.get_feedback_report(days)
    elif report_type == "reservations":
        context["data"] = admin_service.get_reservation_report(days)

    if request.GET.get("export") == "csv":
        import csv
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{report_type}_report.csv"'
        writer = csv.writer(response)
        if report_type == "sales":
            writer.writerow(["Date", "Orders", "Revenue"])
            for row in context["data"]["daily"]:
                writer.writerow([
                    row["date"].isoformat() if hasattr(row["date"], "isoformat") else row["date"],
                    row["count"],
                    f'{row["revenue"]:.2f}',
                ])
        elif report_type == "inventory":
            writer.writerow(["Item", "In Stock", "Times Ordered"])
            for inv in context["data"]:
                writer.writerow([inv.item_name, inv.item_count, inv.ordered])
        elif report_type == "feedback":
            writer.writerow(["User", "Item", "Rating", "Comment", "Date"])
            for r in context["data"].get("reviews", []):
                writer.writerow([
                    r.user.username,
                    r.menu.item.item_name if r.menu else "",
                    r.rating,
                    r.comment,
                    r.created_at.isoformat(),
                ])
        elif report_type == "reservations":
            writer.writerow(["User", "Date", "Time", "Seats", "Status"])
            for r in ReservationSystem.objects.select_related("user").order_by("-created_at"):
                writer.writerow([
                    r.user.username,
                    r.reservation_date,
                    r.reservation_time,
                    r.seats,
                    r.status,
                ])
        return response

    return render(request, "dashboard/reports.html", context)
