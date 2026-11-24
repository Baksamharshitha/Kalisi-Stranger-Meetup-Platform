import 'package:flutter/material.dart';
import '../constants/colors.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'customization_screen.dart';

class OnboardingQuizScreen extends StatefulWidget {
  const OnboardingQuizScreen({super.key});

  @override
  State<OnboardingQuizScreen> createState() => _OnboardingQuizScreenState();
}

class _OnboardingQuizScreenState extends State<OnboardingQuizScreen> {
  int _currentStep = 0;
  final Map<String, String> _selectedAnswers = {};
  List<QuizQuestion> _questions = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchQuiz();
  }

  Future<void> _fetchQuiz() async {
    try {
      final qList = await ApiService.instance.getQuizQuestions();
      if (mounted) {
        setState(() {
          _questions = qList;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _onSelectOption(String option) async {
    final currentQ = _questions[_currentStep];
    setState(() {
      _selectedAnswers[currentQ.id] = option;
    });

    if (_currentStep < _questions.length - 1) {
      Future.delayed(const Duration(milliseconds: 250), () {
        if (mounted) setState(() => _currentStep++);
      });
    } else {
      // Final question answered: Submit to backend API (/api/vibe-dna/submit)
      try {
        await ApiService.instance.submitQuiz(_selectedAnswers);
      } catch (_) {}

      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const CustomizationScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading || _questions.isEmpty) {
      return const Scaffold(
        backgroundColor: KalisiColors.background,
        body: Center(child: CircularProgressIndicator(color: KalisiColors.primaryGold)),
      );
    }

    final currentQ = _questions[_currentStep];
    final selected = _selectedAnswers[currentQ.id];

    return Scaffold(
      backgroundColor: KalisiColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: KalisiColors.textPrimary),
          onPressed: () {
            if (_currentStep > 0) {
              setState(() => _currentStep--);
            } else {
              Navigator.pop(context);
            }
          },
        ),
        title: const Text(
          'Onboarding',
          style: TextStyle(color: KalisiColors.textPrimary, fontSize: 16, fontWeight: FontWeight.w600),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progress Bar
              LinearProgressIndicator(
                value: (_currentStep + 1) / _questions.length,
                backgroundColor: KalisiColors.surfaceLight,
                valueColor: const AlwaysStoppedAnimation<Color>(KalisiColors.primaryGold),
                borderRadius: BorderRadius.circular(4),
                minHeight: 4,
              ),
              const SizedBox(height: 36),

              // Question Headline
              Text(
                currentQ.question,
                style: const TextStyle(
                  color: KalisiColors.textPrimary,
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  height: 1.35,
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Help us determine your "Dinner DNA" for optimal table chemistry.',
                style: TextStyle(
                  color: KalisiColors.textSecondary,
                  fontSize: 14,
                ),
              ),
              const Spacer(),

              // Glow Pill Selection Buttons
              ...List.generate(currentQ.options.length, (index) {
                final option = currentQ.options[index];
                final isSelected = selected == option;

                return Padding(
                  padding: const EdgeInsets.only(bottom: 16.0),
                  child: InkWell(
                    onTap: () => _onSelectOption(option),
                    borderRadius: BorderRadius.circular(30),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 20),
                      decoration: BoxDecoration(
                        color: isSelected ? KalisiColors.surfaceLight : KalisiColors.surface,
                        borderRadius: BorderRadius.circular(30),
                        border: Border.all(
                          color: isSelected ? KalisiColors.neonGlow : KalisiColors.cardBorder,
                          width: isSelected ? 2.0 : 1.2,
                        ),
                        boxShadow: isSelected
                            ? [
                                BoxShadow(
                                  color: KalisiColors.neonGlow.withValues(alpha: 0.35),
                                  blurRadius: 16,
                                  spreadRadius: 1,
                                ),
                              ]
                            : [],
                      ),
                      child: Text(
                        option,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: isSelected ? Colors.white : KalisiColors.textPrimary,
                          fontSize: 17,
                          fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                );
              }),
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}
