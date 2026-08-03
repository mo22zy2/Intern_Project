import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/cart_item.dart';
import '../../menu/models/menu_model.dart';
import '../../menu/models/menu_option.dart';

class CartProvider extends ChangeNotifier {
  static const _storageKey = "cart_items";
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  final List<CartItem> _items = [];

  List<CartItem> get items => List.unmodifiable(_items);

  int get itemCount =>
      _items.fold(0, (sum, item) => sum + item.quantity);

  double get subtotal =>
      _items.fold(0, (sum, item) => sum + item.totalPrice);

  double get total => subtotal;

  Future<void> loadFromStorage() async {
    try {
      final raw = await _storage.read(key: _storageKey);
      if (raw == null) return;
      final list = jsonDecode(raw) as List<dynamic>;
      _items.clear();
      for (final e in list) {
        _items.add(CartItem.fromJson(e as Map<String, dynamic>));
      }
      notifyListeners();
    } catch (_) {
    }
  }

  Future<void> _saveToStorage() async {
    try {
      final data = jsonEncode(_items.map((i) => i.toJson()).toList());
      await _storage.write(key: _storageKey, value: data);
    } catch (_) {
    }
  }

  void addItem(
    MenuModel menu, {
    List<MenuOption> options = const [],
    int quantity = 1,
  }) {
    final index = _items.indexWhere(
      (item) =>
          item.menu.id == menu.id &&
          _sameOptions(item.options, options),
    );

    if (index != -1) {
      _items[index].quantity += quantity;
    } else {
      _items.add(
        CartItem(
          menu: menu,
          options: options,
          quantity: quantity,
        ),
      );
    }

    notifyListeners();
    _saveToStorage();
  }

  void increase(CartItem item) {
    item.quantity++;
    notifyListeners();
    _saveToStorage();
  }

  void decrease(CartItem item) {
    if (item.quantity > 1) {
      item.quantity--;
    } else {
      _items.remove(item);
    }

    notifyListeners();
    _saveToStorage();
  }

  void remove(CartItem item) {
    _items.remove(item);
    notifyListeners();
    _saveToStorage();
  }

  void clear() {
    _items.clear();
    notifyListeners();
    _saveToStorage();
  }

  bool _sameOptions(
    List<MenuOption> a,
    List<MenuOption> b,
  ) {
    if (a.length != b.length) return false;

    final idsA = a.map((e) => e.name).toList()..sort();
    final idsB = b.map((e) => e.name).toList()..sort();

    for (int i = 0; i < idsA.length; i++) {
      if (idsA[i] != idsB[i]) return false;
    }

    return true;
  }
}
