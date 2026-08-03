import '../models/menu_model.dart';
import '../models/menu_option.dart';

const List<MenuModel> dummyMenu = [
  MenuModel(
    id: "1",
    image:
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd",
    category: "Burger",
    name: "Classic Burger",
    price: 120,
    rating: 4.8,
    popularity: 250,
    available: true,
    options: const [
      MenuOption(
        name: "Extra Cheese",
        extraPrice: 15,
      ),
      MenuOption(
        name: "Extra Bacon",
        extraPrice: 30,
      ),
      MenuOption(
        name: "Spicy Sauce",
        extraPrice: 10,
      ),
    ],
  ),

  MenuModel(
    id: "2",
    image:
        "https://images.unsplash.com/photo-1513104890138-7c749659a591",
    category: "Pizza",
    name: "Pepperoni Pizza",
    price: 170,
    rating: 4.9,
    popularity: 310,
    available: true,
    options: const [
      MenuOption(
        name: "Extra Cheese",
        extraPrice: 20,
      ),
      MenuOption(
        name: "Stuffed Crust",
        extraPrice: 35,
      ),
      MenuOption(
        name: "Olives",
        extraPrice: 15,
      ),
    ],
  ),
];