import '../../menu/models/menu_model.dart';
import '../../menu/models/menu_option.dart';

class CartItem {
  final MenuModel menu;
  final List<MenuOption> options;
  int quantity;

  CartItem({
    required this.menu,
    this.options = const [],
    this.quantity = 1,
  });

  double get optionsPrice =>
      options.fold(0, (sum, option) => sum + option.extraPrice);

  double get unitPrice => menu.price + optionsPrice;

  double get totalPrice => unitPrice * quantity;

  Map<String, dynamic> toOrderMap() {
    return {
      "menu_id": int.parse(menu.id),
      "quantity": quantity,
      "unit_price": unitPrice,
      "options_text": options.map((o) => o.name).join(", "),
    };
  }

  Map<String, dynamic> toJson() => {
        "menu": menu.toJson(),
        "options": options.map((o) => o.toJson()).toList(),
        "quantity": quantity,
      };

  factory CartItem.fromJson(Map<String, dynamic> json) {
    return CartItem(
      menu: MenuModel.fromJson(json["menu"] as Map<String, dynamic>),
      options: (json["options"] as List<dynamic>)
          .map((o) => MenuOption.fromJson(o as Map<String, dynamic>))
          .toList(),
      quantity: json["quantity"] as int,
    );
  }
}
