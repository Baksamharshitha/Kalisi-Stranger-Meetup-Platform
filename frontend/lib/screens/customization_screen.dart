import 'package:flutter/material.dart';
import '../constants/colors.dart';
import '../services/api_service.dart';
import 'main_home_screen.dart';

class CustomizationScreen extends StatefulWidget {
  const CustomizationScreen({super.key});

  @override
  State<CustomizationScreen> createState() => _CustomizationScreenState();
}

class _CustomizationScreenState extends State<CustomizationScreen> {
  int _currentStep = 1; // 1: Preferences, 2: Review & Confirm
  String _selectedBudget = 'Mid-Range';
  final String _selectedDietary = 'No dietary restrictions';
  final String _selectedLanguage = 'English';
  bool _isSubmitting = false;

  final List<Map<String, String>> _budgetTiers = [
    {
      'title': 'Budget-Friendly',
      'subtitle': 'Under ₹800 per person',
      'key': 'Budget-Friendly',
    },
    {
      'title': 'Mid-Range',
      'subtitle': '₹800 - ₹1,500 per person',
      'key': 'Mid-Range',
    },
    {
      'title': 'Premium',
      'subtitle': 'Above ₹1,500 per person',
      'key': 'Premium',
    },
  ];

  Future<void> _handleConfirm() async {
    setState(() => _isSubmitting = true);
    try {
      String tierKey = 'mid_range';
      if (_selectedBudget == 'Budget-Friendly') tierKey = 'budget';
      if (_selectedBudget == 'Premium') tierKey = 'premium';

      // Save via Backend Preferences API (/api/preferences/update)
      await ApiService.instance.updatePreferences(
        budgetTier: tierKey,
        dietary: _selectedDietary,
        language: _selectedLanguage,
      );
    } catch (_) {}

    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const MainHomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KalisiColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: KalisiColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Step ${_currentStep + 1} of 3',
          style: const TextStyle(color: KalisiColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progress Bar
              LinearProgressIndicator(
                value: (_currentStep + 1) / 3,
                backgroundColor: KalisiColors.surfaceLight,
                valueColor: const AlwaysStoppedAnimation<Color>(KalisiColors.purpleAccent),
                borderRadius: BorderRadius.circular(4),
                minHeight: 4,
              ),
              const SizedBox(height: 24),

              if (_currentStep == 1) ...[
                // Title
                RichText(
                  text: const TextSpan(
                    text: 'Customize Your\n',
                    style: TextStyle(
                      color: KalisiColors.textPrimary,
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                      height: 1.25,
                    ),
                    children: [
                      TextSpan(
                        text: 'Dining Experience',
                        style: TextStyle(color: KalisiColors.primaryGold),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Tell us about your preferences so we can match you perfectly',
                  style: TextStyle(color: KalisiColors.textSecondary, fontSize: 14),
                ),
                const SizedBox(height: 28),

                // Budget Section Header
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: const BoxDecoration(
                        color: KalisiColors.surfaceLight,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.account_balance_wallet, color: KalisiColors.primaryGold, size: 18),
                    ),
                    const SizedBox(width: 12),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Budget Range',
                          style: TextStyle(color: KalisiColors.textPrimary, fontSize: 16, fontWeight: FontWeight.w700),
                        ),
                        Text(
                          'What are you comfortable spending?',
                          style: TextStyle(color: KalisiColors.textSecondary, fontSize: 12),
                        ),
                      ],
                    ),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: KalisiColors.primaryGold.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        'REQUIRED',
                        style: TextStyle(color: KalisiColors.primaryGold, fontSize: 10, fontWeight: FontWeight.w800),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),

                // Budget Options
                Expanded(
                  child: ListView(
                    children: [
                      ..._budgetTiers.map((tier) {
                        final isSelected = _selectedBudget == tier['key'];
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12.0),
                          child: InkWell(
                            onTap: () => setState(() => _selectedBudget = tier['key']!),
                            borderRadius: BorderRadius.circular(16),
                            child: Container(
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: KalisiColors.surface,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: isSelected ? KalisiColors.purpleAccent : KalisiColors.cardBorder,
                                  width: isSelected ? 2.0 : 1.0,
                                ),
                              ),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          tier['title']!,
                                          style: TextStyle(
                                            color: isSelected ? KalisiColors.purpleAccent : KalisiColors.textPrimary,
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          tier['subtitle']!,
                                          style: const TextStyle(
                                            color: KalisiColors.textSecondary,
                                            fontSize: 13,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Icon(
                                    isSelected ? Icons.check_circle : Icons.radio_button_unchecked,
                                    color: isSelected ? KalisiColors.purpleAccent : KalisiColors.textMuted,
                                    size: 22,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      }),
                    ],
                  ),
                ),
              ] else ...[
                // Review & Confirm (Step 3)
                const Text(
                  'Review & Confirm',
                  style: TextStyle(color: KalisiColors.textPrimary, fontSize: 26, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Double check your preferences before booking your dinner',
                  style: TextStyle(color: KalisiColors.textSecondary, fontSize: 14),
                ),
                const SizedBox(height: 28),

                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: KalisiColors.surface,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: KalisiColors.primaryGold.withValues(alpha: 0.4)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Your Preferences',
                        style: TextStyle(color: KalisiColors.purpleAccent, fontSize: 17, fontWeight: FontWeight.w800),
                      ),
                      const Divider(color: KalisiColors.cardBorder, height: 28),
                      _buildReviewRow('Budget Tier', _selectedBudget),
                      const SizedBox(height: 14),
                      _buildReviewRow('Dietary Requirements', _selectedDietary),
                      const SizedBox(height: 14),
                      _buildReviewRow('Language Preference', _selectedLanguage),
                    ],
                  ),
                ),
                const Spacer(),
              ],

              // Bottom Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isSubmitting
                      ? null
                      : () {
                          if (_currentStep == 1) {
                            setState(() => _currentStep = 2);
                          } else {
                            _handleConfirm();
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: KalisiColors.primaryGold,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                      : Text(
                          _currentStep == 1 ? 'Continue' : 'Confirm & Continue',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                        ),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildReviewRow(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: KalisiColors.textSecondary, fontSize: 12)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: KalisiColors.textPrimary, fontSize: 15, fontWeight: FontWeight.w700)),
      ],
    );
  }
}
