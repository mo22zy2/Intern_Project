import 'menu_option.dart';

class MenuModel {
  final String id;
  final String image;
  final String category;
  final String name;
  final double price;
  final double rating;
  final int popularity;
  final bool available;
  final List<MenuOption> options;

  const MenuModel({
    required this.id,
    required this.image,
    required this.category,
    required this.name,
    required this.price,
    required this.rating,
    required this.popularity,
    required this.available,
    required this.options,
  });

  factory MenuModel.fromJson(Map<String, dynamic> json) {
    return MenuModel(
      id: json["id"].toString(),
      image: json["image_url"] as String? ?? "",
      category: json["category_name"] as String? ?? "",
      name: json["item_name"] as String? ?? "",
      price: (json["price"] as num).toDouble(),
      rating: (json["avg_rating"] as num?)?.toDouble() ?? 0,
      popularity: json["popularity_score"] as int? ?? 0,
      available: json["available"] as bool? ?? true,
      options: (json["customization_options"] as List<dynamic>?)
              ?.map(
                (e) => MenuOption.fromJson(e as Map<String, dynamic>),
              )
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() => {
        "id": id,
        "image_url": image,
        "category_name": category,
        "item_name": name,
        "price": price,
        "avg_rating": rating,
        "popularity_score": popularity,
        "available": available,
        "customization_options": options.map((o) => o.toJson()).toList(),
      };
}
