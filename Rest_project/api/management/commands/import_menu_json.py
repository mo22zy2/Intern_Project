import json

from django.core.management.base import BaseCommand, CommandError

from api.models import Category, Inventory, Menu, MenuCustomizationOption


class Command(BaseCommand):
    help = "Replace the menu with data from a JSON file (schema: categories + menu_items with extras)"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the menu JSON file")

    def handle(self, *args, **options):
        path = options["json_file"]
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise CommandError(f"Failed to read JSON file: {e}")

        categories = data.get("categories", [])
        menu_items = data.get("menu_items", [])
        if not categories or not menu_items:
            raise CommandError("JSON must contain non-empty 'categories' and 'menu_items'")

        MenuCustomizationOption.objects.all().delete()
        Menu.objects.all().delete()
        Category.objects.all().delete()
        Inventory.objects.all().delete()

        for category_name in categories:
            Category.objects.create(category_name=category_name)

        category_map = {c.category_name: c for c in Category.objects.all()}

        created = 0
        extras_created = 0
        for item in menu_items:
            item_name = item.get("item_name")
            category_name = item.get("category")
            price = item.get("price")
            if not item_name or category_name not in category_map or price is None:
                raise CommandError(f"Invalid menu item (missing name, unknown category, or no price): {item}")

            inventory = Inventory.objects.create(
                item_name=item_name,
                item_count=100,
            )
            menu = Menu.objects.create(
                item=inventory,
                category=category_map[category_name],
                image_url=item.get("image_url", ""),
                price=float(price),
                popularity_score=int(item.get("popularity_score", 0)),
                available=bool(item.get("available", True)),
            )
            created += 1

            for extra in item.get("extras", []):
                option_name = extra.get("option_name")
                if not option_name:
                    continue
                MenuCustomizationOption.objects.create(
                    menu=menu,
                    option_name=option_name,
                    extra_price=float(extra.get("extra_price", 0)),
                )
                extras_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done: {created} menu items, {extras_created} extras, {len(categories)} categories."
        ))
