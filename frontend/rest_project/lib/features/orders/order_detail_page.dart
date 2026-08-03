import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import 'order_service.dart';

class OrderDetailPage extends StatefulWidget {
  final int orderId;

  const OrderDetailPage({super.key, required this.orderId});

  @override
  State<OrderDetailPage> createState() => _OrderDetailPageState();
}

class _OrderDetailPageState extends State<OrderDetailPage> {
  final OrderService _service = OrderService();
  Map<String, dynamic>? _order;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadOrder();
  }

  Future<void> _loadOrder() async {
    try {
      final order = await _service.getOrderDetail(widget.orderId);
      if (mounted) setState(() => _order = order);
    } catch (_) {
      if (mounted) setState(() => _order = {});
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          "Order #${widget.orderId}",
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _order == null || _order!.isEmpty
              ? const Center(
                  child: Text(
                    "Order not found",
                    style: TextStyle(color: Colors.white54),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Status: ${(_order!["status"] as String?)?.toUpperCase() ?? "PENDING"}",
                        style: const TextStyle(
                          color: AppColors.secondary,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _order!["created_at"] as String? ?? "",
                        style: const TextStyle(color: AppColors.subtitle),
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        "Items",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ...(_order!["items"] as List<dynamic>? ?? [])
                          .map((item) {
                        final i = item as Map<String, dynamic>;
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  i["item_name"] as String? ?? "Item",
                                  style: const TextStyle(
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                              Text(
                                "${i["quantity"]}x  ${(i["unit_price"] as num?)?.toStringAsFixed(2) ?? "0.00"} EGP",
                                style: const TextStyle(
                                  color: Colors.white70,
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                      const Divider(height: 32),
                      Row(
                        mainAxisAlignment:
                            MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Total",
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            "${(_order!["total_price"] as num?)?.toStringAsFixed(2) ?? "0.00"} EGP",
                            style: const TextStyle(
                              color: AppColors.primary,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      if (_order!["delivery_type"] != null)
                        _infoRow(
                          "Delivery",
                          (_order!["delivery_type"] as String),
                        ),
                      if (_order!["delivery_address"] != null)
                        _infoRow(
                          "Address",
                          (_order!["delivery_address"] as String),
                        ),
                      if (_order!["payment"] != null)
                        _infoRow(
                          "Payment",
                          (_order!["payment"] as Map)["method_type"]
                                  as String? ??
                              "N/A",
                        ),
                    ],
                  ),
                ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.subtitle)),
          Text(
            value,
            style: const TextStyle(color: Colors.white),
          ),
        ],
      ),
    );
  }
}
