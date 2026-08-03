import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/app_navbar.dart';
import 'data/dummy_data.dart';
import 'models/menu_model.dart';
import 'services/menu_service.dart';
import 'widgets/menu_card.dart';
import 'widgets/menu_filter_bar.dart';
import 'widgets/menu_search_bar.dart';

class MenuPage extends StatefulWidget {
  const MenuPage({super.key});

  @override
  State<MenuPage> createState() => _MenuPageState();
}

class _MenuPageState extends State<MenuPage> {
  final MenuService _menuService = MenuService();
  final TextEditingController _searchController = TextEditingController();

  List<MenuModel> _items = [];
  List<Map<String, dynamic>> _categories = [];
  bool _isLoading = true;
  String? _error;

  String? _searchQuery;
  int? _selectedCategoryId;
  String _selectedSort = "Popular";
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _loadMenu();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> _loadMenu() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await _menuService.getMenu(
        search: _searchQuery,
        categoryId: _selectedCategoryId,
        sort: _selectedSort,
      );
      if (mounted) {
        setState(() {
          _items = _menuService.parseItems(data);
          _categories = _menuService.parseCategories(data);
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _items = dummyMenu;
          _isLoading = false;
          _error = "Could not connect to server. Showing sample data.";
        });
      }
    }
  }

  void _onSearchChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), () {
      _searchQuery = value.isEmpty ? null : value;
      _loadMenu();
    });
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;

    int columns;

    if (width >= 1200) {
      columns = 4;
    } else if (width >= 900) {
      columns = 3;
    } else if (width >= 600) {
      columns = 2;
    } else {
      columns = 1;
    }

    return Scaffold(
      appBar: const AppNavbar(),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(
          horizontal: 24,
          vertical: 40,
        ),
        child: Column(
          children: [
            const Text(
              "OUR MENU",
              style: TextStyle(
                color: Colors.white,
                fontSize: 42,
                fontWeight: FontWeight.bold,
                letterSpacing: 3,
              ),
            ),
            const SizedBox(height: 40),
            MenuSearchBar(
              controller: _searchController,
              onChanged: _onSearchChanged,
            ),
            const SizedBox(height: 20),
            MenuFilterBar(
              categories: _categories,
              selectedCategoryId: _selectedCategoryId,
              selectedSort: _selectedSort,
              onCategoryChanged: (id) {
                setState(() => _selectedCategoryId = id);
                _loadMenu();
              },
              onSortChanged: (sort) {
                setState(() => _selectedSort = sort ?? "Popular");
                _loadMenu();
              },
            ),
            const SizedBox(height: 40),
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.all(40),
                child: CircularProgressIndicator(),
              )
            else if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: Text(
                  _error!,
                  style: const TextStyle(
                    color: AppColors.subtitle,
                    fontSize: 14,
                  ),
                ),
              ),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _items.length,
              gridDelegate:
                  SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: columns,
                crossAxisSpacing: 20,
                mainAxisSpacing: 20,
                childAspectRatio: .67,
              ),
              itemBuilder: (context, index) {
                return MenuCard(
                  item: _items[index],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
