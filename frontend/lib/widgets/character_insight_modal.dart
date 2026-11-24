import 'package:flutter/material.dart';
import '../constants/colors.dart';
import '../models/models.dart';

class CharacterInsightModal extends StatelessWidget {
  final List<CharacterInsight>? insights;

  const CharacterInsightModal({super.key, this.insights});

  Color _getArchetypeColor(String archetype) {
    if (archetype.contains('Stark')) return KalisiColors.primaryGold;
    if (archetype.contains('Phoebe')) return KalisiColors.purpleAccent;
    if (archetype.contains('Sherlock')) return Colors.tealAccent;
    if (archetype.contains('Yoda')) return Colors.lightGreenAccent;
    return KalisiColors.neonGlow;
  }

  @override
  Widget build(BuildContext context) {
    final list = insights != null && insights!.isNotEmpty
        ? insights!
        : [
            CharacterInsight(
              archetype: 'Clark Kent',
              count: 3,
              vibeDescription: 'The grounded anchor. Warm, attentive, and puts everyone at ease.',
              conversationStarter: 'Ask them about their favorite low-key spot in the city or their calmest Sunday memory.',
            ),
            CharacterInsight(
              archetype: 'Stark',
              count: 2,
              vibeDescription: 'The charismatic spark. Quick-witted, high energy, and brings effortless laughter.',
              conversationStarter: 'Ask what ambitious, slightly crazy passion project they\'d fund with unlimited capital.',
            ),
            CharacterInsight(
              archetype: 'Phoebe',
              count: 1,
              vibeDescription: 'The creative storyteller. Quirky, authentic, and delightfully unexpected.',
              conversationStarter: 'Ask for the most surreal or serendipitous encounter they have ever had.',
            ),
          ];

    return Container(
      decoration: const BoxDecoration(
        color: KalisiColors.surface,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(28),
          topRight: Radius.circular(28),
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 48,
              height: 4,
              decoration: BoxDecoration(
                color: KalisiColors.cardBorder,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 18),
          const Row(
            children: [
              Icon(Icons.auto_awesome, color: KalisiColors.primaryGold, size: 22),
              SizedBox(width: 10),
              Text(
                'Table Character Insights',
                style: TextStyle(
                  color: KalisiColors.textPrimary,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Here is the conversational DNA of your 5-stranger table tonight:',
            style: TextStyle(color: KalisiColors.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 20),
          ...list.map((item) {
            final color = _getArchetypeColor(item.archetype);
            return Container(
              margin: const EdgeInsets.only(bottom: 14),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: KalisiColors.surfaceLight,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: color.withValues(alpha: 0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${item.archetype} (${item.count} Attendees)',
                    style: TextStyle(
                      color: color,
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.vibeDescription,
                    style: const TextStyle(color: KalisiColors.textPrimary, fontSize: 13, height: 1.3),
                  ),
                  const Divider(color: KalisiColors.cardBorder, height: 18),
                  Text(
                    'Icebreaker: "${item.conversationStarter}"',
                    style: const TextStyle(
                      color: KalisiColors.primaryGold,
                      fontSize: 12,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            );
          }),
          const SizedBox(height: 10),
        ],
      ),
    );
  }
}
