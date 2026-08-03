import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:rest_project/features/auth/provider/auth_provider.dart';
import 'package:rest_project/features/home/widgets/featured_section.dart';

import '../../core/widgets/app_navbar.dart';
import '../menu/models/menu_model.dart';
import 'home_service.dart';
import 'widgets/cta_section.dart';
import 'widgets/hero_section.dart';
import 'widgets/stats_section.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final HomeService _service = HomeService();
  int _menuItems = 0;
  int _categories = 0;
  List<MenuModel> popular = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final data = await _service.getHomeData();
      if (mounted) {
        setState(() {
          _menuItems =
              (data["total_menu_items"] as num?)?.toInt() ?? 0;
          _categories =
              (data["total_categories"] as num?)?.toInt() ?? 0;
          popular = _service.parsePopular(data);
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = "Could not load data. Showing defaults.";
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isAuthenticated = context.watch<AuthProvider>().isAuthenticated;
    return Scaffold(
      appBar: const AppNavbar(),
      body: SingleChildScrollView(
        child: Column(
          children: [
            HeroSection(isAuthenticated: isAuthenticated),
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.all(40),
                child: CircularProgressIndicator(),
              )
            else ...[
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.white54, fontSize: 14),
                  ),
                ),
              StatsSection(
                menuItems: _menuItems,
                categories: _categories,
              ),
              FeaturedSection(items: popular),
            ],
            CTASection(isAuthenticated: isAuthenticated),
          ],
        ),
      ),
    );
  }
}
