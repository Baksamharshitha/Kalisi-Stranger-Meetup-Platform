import 'package:flutter/material.dart';
import '../constants/colors.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/character_insight_modal.dart';

class ProgressiveRevealScreen extends StatefulWidget {
  final String? bookingId;

  const ProgressiveRevealScreen({super.key, this.bookingId});

  @override
  State<ProgressiveRevealScreen> createState() => _ProgressiveRevealScreenState();
}

class _ProgressiveRevealScreenState extends State<ProgressiveRevealScreen> {
  TableReveal? _reveal;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadRevealData();
  }

  Future<void> _loadRevealData() async {
    if (widget.bookingId == null) {
      _setDefaultReveal();
      return;
    }

    setState(() => _isLoading = true);
    try {
      final reveal = await ApiService.instance.getTableReveal(widget.bookingId!);
      if (mounted) {
        setState(() {
          _reveal = reveal;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        _setDefaultReveal();
        setState(() => _isLoading = false);
      }
    }
  }

  void _setDefaultReveal() {
    _reveal = TableReveal(
      bookingId: widget.bookingId ?? 'sample_b1',
      revealStage: 'fully_revealed',
      dateStr: 'Sat, 11/28/2026',
      timeWindow: '19:00 - 22:00',
      city: ApiService.instance.currentCity,
      neighborhood: 'Anna Nagar',
      tableNumber: 1,
      restaurantName: 'Chamber of Potions Anna Nagar',
      restaurantAddress: 'C10, Ravilla Towers, Anna Nagar 3rd Main Rd, Chennai, Tamil Nadu 600040',
      cuisine: 'Italian / Continental',
      groupSummary: 'A curated mix of Clark Kent (3), Stark (2), and Phoebe (1)',
      characterInsights: [
        CharacterInsight(
          archetype: 'Clark Kent',
          count: 3,
          vibeDescription: 'The grounded anchor. Warm, attentive, and puts everyone at ease.',
          conversationStarter: 'Ask them about their favorite low-key spot in the city.',
        ),
        CharacterInsight(
          archetype: 'Stark',
          count: 2,
          vibeDescription: 'The charismatic spark. Quick-witted, high energy, and brings effortless laughter.',
          conversationStarter: 'Ask what ambitious passion project they\'d fund with unlimited capital.',
        ),
        CharacterInsight(
          archetype: 'Phoebe',
          count: 1,
          vibeDescription: 'The creative storyteller. Quirky, authentic, and delightfully unexpected.',
          conversationStarter: 'Ask for the most surreal or serendipitous encounter they have ever had.',
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final reveal = _reveal;

    return Scaffold(
      backgroundColor: KalisiColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: KalisiColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Event Details',
          style: TextStyle(color: KalisiColors.textPrimary, fontSize: 18, fontWeight: FontWeight.w800),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: KalisiColors.textPrimary),
            onPressed: _loadRevealData,
          ),
        ],
      ),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator(color: KalisiColors.primaryGold))
            : SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header Badge & Date
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: KalisiColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: KalisiColors.cardBorder),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Date & Time',
                            style: TextStyle(color: KalisiColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            reveal?.dateStr ?? 'Saturday Dinner',
                            style: const TextStyle(color: KalisiColors.textPrimary, fontSize: 20, fontWeight: FontWeight.w800),
                          ),
                          Text(
                            reveal?.timeWindow ?? '19:00 - 22:00',
                            style: const TextStyle(color: KalisiColors.primaryGold, fontSize: 15, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Table Information Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: KalisiColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: KalisiColors.primaryGold.withValues(alpha: 0.5)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.restaurant, color: KalisiColors.primaryGold, size: 24),
                          const SizedBox(width: 14),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Table Information',
                                style: TextStyle(color: KalisiColors.textSecondary, fontSize: 12),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Table Number: ${reveal?.tableNumber ?? 1}',
                                style: const TextStyle(color: KalisiColors.textPrimary, fontSize: 18, fontWeight: FontWeight.w800),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Restaurant Details Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: KalisiColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: KalisiColors.cardBorder),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Restaurant & Venue',
                            style: TextStyle(color: KalisiColors.textSecondary, fontSize: 12),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            reveal?.restaurantName ?? 'Secret Handpicked Venue',
                            style: const TextStyle(color: KalisiColors.textPrimary, fontSize: 18, fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 10),
                          Text(
                            reveal?.restaurantAddress ?? 'Address unlocked on event morning.',
                            style: const TextStyle(color: KalisiColors.textSecondary, fontSize: 13, height: 1.4),
                          ),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: KalisiColors.surfaceLight,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  'Cuisine: ${reveal?.cuisine ?? "Eclectic"}',
                                  style: const TextStyle(color: KalisiColors.textPrimary, fontSize: 12, fontWeight: FontWeight.w600),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: KalisiColors.surfaceLight,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  'City: ${reveal?.city ?? ApiService.instance.currentCity}',
                                  style: const TextStyle(color: KalisiColors.textSecondary, fontSize: 12),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Group Summary / Teaser Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: KalisiColors.surface,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: KalisiColors.purpleAccent.withValues(alpha: 0.5)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.groups, color: KalisiColors.purpleAccent, size: 20),
                              SizedBox(width: 8),
                              Text(
                                'Group Chemistry & Vibe',
                                style: TextStyle(color: KalisiColors.purpleAccent, fontSize: 14, fontWeight: FontWeight.w800),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            reveal?.groupSummary ?? 'A curated table matched by Kalisi Vibe DNA',
                            style: const TextStyle(
                              color: KalisiColors.textPrimary,
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              height: 1.3,
                            ),
                          ),
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            height: 48,
                            child: OutlinedButton(
                              onPressed: () {
                                showModalBottomSheet(
                                  context: context,
                                  backgroundColor: Colors.transparent,
                                  isScrollControlled: true,
                                  builder: (_) => CharacterInsightModal(
                                    insights: reveal?.characterInsights,
                                  ),
                                );
                              },
                              style: OutlinedButton.styleFrom(
                                foregroundColor: KalisiColors.primaryGold,
                                side: const BorderSide(color: KalisiColors.primaryGold, width: 1.2),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                              ),
                              child: const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.auto_awesome, color: KalisiColors.primaryGold, size: 18),
                                  SizedBox(width: 8),
                                  Text(
                                    'View Character Insights',
                                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
      ),
    );
  }
}
