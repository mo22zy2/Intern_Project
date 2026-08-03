class MenuOption {
  final String name;
  final double extraPrice;

  const MenuOption({
    required this.name,
    required this.extraPrice,
  });

  factory MenuOption.fromJson(Map<String, dynamic> json) {
    return MenuOption(
      name: json["option_name"] as String? ?? "",
      extraPrice: (json["extra_price"] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        "option_name": name,
        "extra_price": extraPrice,
      };
}
