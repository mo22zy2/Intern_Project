import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import 'payment_service.dart';

class PaymentMethodsPage extends StatefulWidget {
  const PaymentMethodsPage({super.key});

  @override
  State<PaymentMethodsPage> createState() => _PaymentMethodsPageState();
}

class _PaymentMethodsPageState extends State<PaymentMethodsPage> {
  final PaymentService _service = PaymentService();
  List<Map<String, dynamic>>? _methods;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final data = await _service.getMethods();
      if (mounted) setState(() => _methods = data);
    } catch (_) {
      if (mounted) setState(() => _methods = []);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _delete(int id) async {
    try {
      await _service.deleteMethod(id);
      _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to delete payment method")),
        );
      }
    }
  }

  Future<void> _setDefault(int id) async {
    try {
      await _service.setDefault(id);
      _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to set default")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "PAYMENT METHODS",
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 2),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => const AddPaymentMethodPage(),
              ),
            ).then((_) => _load()),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _methods == null || _methods!.isEmpty
              ? const Center(
                  child: Text(
                    "No payment methods saved",
                    style: TextStyle(color: Colors.white54, fontSize: 18),
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(24),
                  itemCount: _methods!.length,
                  itemBuilder: (context, index) {
                    final m = _methods![index];
                    final isDefault =
                        m["is_default"] as bool? ?? false;
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: isDefault
                              ? AppColors.primary
                              : Colors.white12,
                        ),
                      ),
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(16),
                        leading: const Icon(
                          Icons.credit_card,
                          color: Colors.white70,
                        ),
                        title: Text(
                          m["method_type"] as String? ?? "Card",
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        subtitle: isDefault
                            ? const Text(
                                "Default",
                                style: TextStyle(
                                  color: AppColors.primary,
                                  fontSize: 12,
                                ),
                              )
                            : null,
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (!isDefault)
                              TextButton(
                                onPressed: () =>
                                    _setDefault(m["id"] as int),
                                child: const Text(
                                  "Set Default",
                                  style: TextStyle(
                                    color: AppColors.subtitle,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            IconButton(
                              icon: const Icon(
                                Icons.delete_outline,
                                size: 20,
                              ),
                              color: Colors.red,
                              onPressed: () =>
                                  _delete(m["id"] as int),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

class AddPaymentMethodPage extends StatefulWidget {
  const AddPaymentMethodPage({super.key});

  @override
  State<AddPaymentMethodPage> createState() =>
      _AddPaymentMethodPageState();
}

class _AddPaymentMethodPageState extends State<AddPaymentMethodPage> {
  final _formKey = GlobalKey<FormState>();
  final _cardNumberController = TextEditingController();
  final _cardholderController = TextEditingController();
  final _expiryController = TextEditingController();
  final _cvvController = TextEditingController();
  final PaymentService _service = PaymentService();
  bool _isDefault = false;
  bool _saving = false;

  @override
  void dispose() {
    _cardNumberController.dispose();
    _cardholderController.dispose();
    _expiryController.dispose();
    _cvvController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await _service.addMethod(
        cardNumber: _cardNumberController.text.trim(),
        cardholderName: _cardholderController.text.trim(),
        expiry: _expiryController.text.trim(),
        cvv: _cvvController.text.trim(),
        isDefault: _isDefault,
      );
      if (mounted) Navigator.of(context).pop();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to save card")),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "ADD CARD",
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 2),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 400),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _cardNumberController,
                  decoration: const InputDecoration(
                    labelText: "Card Number",
                    prefixIcon: Icon(Icons.credit_card),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (v) =>
                      v == null || v.trim().isEmpty
                          ? "Enter card number"
                          : null,
                ),
                const SizedBox(height: 20),
                TextFormField(
                  controller: _cardholderController,
                  decoration: const InputDecoration(
                    labelText: "Cardholder Name",
                    prefixIcon: Icon(Icons.person_outlined),
                  ),
                  validator: (v) =>
                      v == null || v.trim().isEmpty
                          ? "Enter cardholder name"
                          : null,
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _expiryController,
                        decoration: const InputDecoration(
                          labelText: "Expiry (MM/YY)",
                        ),
                        validator: (v) =>
                            v == null || v.trim().isEmpty
                                ? "Required"
                                : null,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextFormField(
                        controller: _cvvController,
                        decoration: const InputDecoration(
                          labelText: "CVV",
                        ),
                        keyboardType: TextInputType.number,
                        obscureText: true,
                        validator: (v) =>
                            v == null || v.trim().isEmpty
                                ? "Required"
                                : null,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                CheckboxListTile(
                  value: _isDefault,
                  onChanged: (v) =>
                      setState(() => _isDefault = v ?? false),
                  title: const Text(
                    "Set as default payment method",
                    style: TextStyle(color: Colors.white, fontSize: 14),
                  ),
                  contentPadding: EdgeInsets.zero,
                  checkboxShape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _saving ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding:
                          const EdgeInsets.symmetric(vertical: 16),
                    ),
                    child: _saving
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            "SAVE CARD",
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1,
                            ),
                          ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
