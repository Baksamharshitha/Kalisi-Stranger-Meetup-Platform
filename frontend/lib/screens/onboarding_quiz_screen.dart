import 'package:flutter/material.dart';
import '../constants/colors.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'main_home_screen.dart';

class OnboardingQuizScreen extends StatefulWidget {
  const OnboardingQuizScreen({super.key});

  @override
  State<OnboardingQuizScreen> createState() => _OnboardingQuizScreenState();
}

class _OnboardingQuizScreenState extends State<OnboardingQuizScreen> {
  int _currentStep = 0;
  final Map<String, dynamic> _answers = {};
  List<QuizQuestion> _questions = [];
  bool _isLoading = true;
  bool _isSubmitting = false;

  // Controllers for text & phone input
  final TextEditing4Controller _nameController = TextEditing4Controller();
  final TextEditing4Controller _phoneController = TextEditing4Controller();
  final TextEditing4Controller _otpController = TextEditing4Controller();

  bool _isOtpSent = false;
  bool _isOtpSending = false;
  String? _devOtp;
  String? _otpErrorMessage;

  @override
  void initState() {
    super.initState();
    _fetchQuiz();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
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

  void _nextStep() {
    if (_currentStep < _questions.length - 1) {
      setState(() => _currentStep++);
    }
  }

  void _prevStep() {
    if (_currentStep > 0) {
      setState(() => _currentStep--);
    } else {
      Navigator.pop(context);
    }
  }

  void _onSelectChoice(String questionId, String option) {
    setState(() {
      _answers[questionId] = option;
    });

    // Auto-advance on single choice after brief feedback
    Future.delayed(const Duration(milliseconds: 220), () {
      if (mounted) _nextStep();
    });
  }

  Future<void> _handleSendOtp() async {
    final phone = _phoneController.text.trim();
    if (phone.length < 10) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a valid 10-digit mobile number')),
      );
      return;
    }

    setState(() {
      _isOtpSending = true;
      _otpErrorMessage = null;
    });

    try {
      final res = await ApiService.instance.sendOtp(phone);
      if (mounted) {
        setState(() {
          _isOtpSent = true;
          _devOtp = res['dev_otp']?.toString() ?? '123456';
          _otpController.text = _devOtp!; // pre-fill dev code for quick testing
          _isOtpSending = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Verification code sent! (Dev code: $_devOtp)'),
            backgroundColor: KalisiColors.primaryGold,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isOtpSending = false;
          _otpErrorMessage = e.toString();
        });
      }
    }
  }

  Future<void> _handleCompleteOnboarding() async {
    final otp = _otpController.text.trim();
    final phone = _phoneController.text.trim();

    if (otp.length < 4) {
      setState(() => _otpErrorMessage = 'Please enter the 6-digit verification code');
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final fullName = (_answers['full_name'] as String?)?.trim() ?? _nameController.text.trim();
      final ageStr = (_answers['age'] as String?) ?? '24';
      int age = 24;
      if (ageStr.contains('-')) {
        age = int.tryParse(ageStr.split('-')[0]) ?? 24;
      } else {
        age = int.tryParse(ageStr) ?? 24;
      }
      final gender = (_answers['gender'] as String?) ?? 'Prefer not to say';
      final city = (_answers['city'] as String?) ?? 'Hyderabad';

      final res = await ApiService.instance.completeOnboarding(
        fullName: fullName.isNotEmpty ? fullName : 'Kalisi Member',
        age: age,
        gender: gender,
        city: city,
        phone: phone,
        otp: otp,
        answers: _answers,
      );

      if (!mounted) return;

      // Show Archetype Reveal Celebration Dialog
      _showVibeDNARevealDialog(
        archetype: res['archetype'] ?? 'Stark',
        title: res['title'] ?? 'The Charismatic Spark',
        superpower: res['superpower'] ?? 'Turns awkward silences into inside jokes.',
      );
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _otpErrorMessage = e.toString();
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Onboarding note: ${e.toString()}')),
        );
      }
    }
  }

  void _showVibeDNARevealDialog({
    required String archetype,
    required String title,
    required String superpower,
  }) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          padding: const EdgeInsets.all(26),
          decoration: BoxDecoration(
            color: const Color(0xFF181818),
            borderRadius: BorderRadius.circular(28),
            border: Border.all(color: KalisiColors.primaryGold, width: 1.5),
            boxShadow: [
              BoxShadow(
                color: KalisiColors.primaryGold.withValues(alpha: 0.3),
                blurRadius: 28,
                spreadRadius: 2,
              )
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: Color(0xFF282828),
                ),
                child: const Icon(Icons.auto_awesome, color: KalisiColors.primaryGold, size: 36),
              ),
              const SizedBox(height: 18),
              const Text(
                'VIBE DNA UNLOCKED',
                style: TextStyle(
                  color: KalisiColors.primaryGold,
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Archetype: $archetype',
                style: const TextStyle(color: KalisiColors.purpleAccent, fontSize: 14, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF222222),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  'Superpower: "$superpower"',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.35, fontStyle: FontStyle.italic),
                ),
              ),
              const SizedBox(height: 22),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(ctx);
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (_) => const MainHomeScreen()),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: KalisiColors.primaryGold,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
                  ),
                  child: const Text(
                    'Explore Dinner Meetups',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading || _questions.isEmpty) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: KalisiColors.primaryGold)),
      );
    }

    final currentQ = _questions[_currentStep];
    final progress = (_currentStep + 1) / _questions.length;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: _prevStep,
        ),
        title: Text(
          'Step ${_currentStep + 1} of ${_questions.length}',
          style: const TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w700),
        ),
        centerTitle: true,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 18),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E1E1E),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: KalisiColors.primaryGold.withValues(alpha: 0.3)),
                ),
                child: Text(
                  currentQ.category.toUpperCase(),
                  style: const TextStyle(color: KalisiColors.primaryGold, fontSize: 10, fontWeight: FontWeight.w900),
                ),
              ),
            ),
          )
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Progress Bar
            LinearProgressIndicator(
              value: progress,
              backgroundColor: const Color(0xFF222222),
              valueColor: const AlwaysStoppedAnimation<Color>(KalisiColors.primaryGold),
              minHeight: 3.5,
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Question Header
                    Text(
                      currentQ.question,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 26,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.3,
                        height: 1.25,
                      ),
                    ),
                    if (currentQ.subtitle.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        currentQ.subtitle,
                        style: const TextStyle(color: Colors.white60, fontSize: 14, height: 1.3),
                      ),
                    ],
                    const SizedBox(height: 28),

                    // Input Widget based on type
                    _buildQuestionInput(currentQ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionInput(QuizQuestion currentQ) {
    switch (currentQ.type) {
      case 'text':
        return _buildTextInput(currentQ);
      case 'age':
        return _buildAgeSelector(currentQ);
      case 'phone_otp':
        return _buildPhoneOtpInput(currentQ);
      case 'single_choice':
      default:
        return _buildSingleChoice(currentQ);
    }
  }

  // 1. Text Input (Q1: Full Name)
  Widget _buildTextInput(QuizQuestion currentQ) {
    return Column(
      children: [
        TextField(
          controller: _nameController,
          autofocus: true,
          style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700),
          decoration: InputDecoration(
            hintText: 'e.g. Rahul Sharma',
            hintStyle: const TextStyle(color: Colors.white38),
            filled: true,
            fillColor: const Color(0xFF161616),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18),
              borderSide: const BorderSide(color: Color(0xFF2E2E2E)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18),
              borderSide: const BorderSide(color: KalisiColors.primaryGold, width: 2),
            ),
            prefixIcon: const Icon(Icons.person, color: KalisiColors.primaryGold),
          ),
          onChanged: (val) => _answers[currentQ.id] = val,
        ),
        const SizedBox(height: 32),
        SizedBox(
          width: double.infinity,
          height: 54,
          child: ElevatedButton(
            onPressed: () {
              final val = _nameController.text.trim();
              if (val.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please enter your name to proceed')),
                );
                return;
              }
              _answers[currentQ.id] = val;
              _nextStep();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: KalisiColors.primaryGold,
              foregroundColor: Colors.black,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(27)),
            ),
            child: const Text('Next', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
          ),
        ),
      ],
    );
  }

  // 2. Age Selector (Q2: Age)
  Widget _buildAgeSelector(QuizQuestion currentQ) {
    final selected = _answers[currentQ.id] as String?;
    return Column(
      children: currentQ.options.map((option) {
        final isSelected = selected == option;
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: InkWell(
            onTap: () => _onSelectChoice(currentQ.id, option),
            borderRadius: BorderRadius.circular(18),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF222222) : const Color(0xFF141414),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: isSelected ? KalisiColors.primaryGold : const Color(0xFF262626),
                  width: isSelected ? 2 : 1,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '$option years old',
                    style: TextStyle(
                      color: isSelected ? KalisiColors.primaryGold : Colors.white,
                      fontSize: 17,
                      fontWeight: isSelected ? FontWeight.w900 : FontWeight.w600,
                    ),
                  ),
                  Icon(
                    isSelected ? Icons.check_circle : Icons.radio_button_unchecked,
                    color: isSelected ? KalisiColors.primaryGold : Colors.white38,
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  // 3. Single Choice Options (Q3 - Q19)
  Widget _buildSingleChoice(QuizQuestion currentQ) {
    final selected = _answers[currentQ.id] as String?;

    return Column(
      children: currentQ.options.map((option) {
        final isSelected = selected == option;
        return Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: InkWell(
            onTap: () => _onSelectChoice(currentQ.id, option),
            borderRadius: BorderRadius.circular(20),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF1C1A14) : const Color(0xFF141414),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: isSelected ? KalisiColors.primaryGold : const Color(0xFF252525),
                  width: isSelected ? 2 : 1,
                ),
                boxShadow: isSelected
                    ? [
                        BoxShadow(
                          color: KalisiColors.primaryGold.withValues(alpha: 0.2),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        )
                      ]
                    : [],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      option,
                      style: TextStyle(
                        color: isSelected ? KalisiColors.primaryGold : Colors.white,
                        fontSize: 16,
                        fontWeight: isSelected ? FontWeight.w800 : FontWeight.w500,
                        height: 1.3,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Icon(
                    isSelected ? Icons.check_circle : Icons.circle_outlined,
                    color: isSelected ? KalisiColors.primaryGold : Colors.white30,
                    size: 22,
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  // 4. Phone Number & OTP Verification (Q20)
  Widget _buildPhoneOtpInput(QuizQuestion currentQ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Mobile Number Field
        const Text(
          'Mobile Number',
          style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _phoneController,
          keyboardType: TextInputType.phone,
          enabled: !_isOtpSent,
          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800),
          decoration: InputDecoration(
            hintText: '98765 43210',
            hintStyle: const TextStyle(color: Colors.white38),
            prefixText: '+91 ',
            prefixStyle: const TextStyle(color: KalisiColors.primaryGold, fontSize: 18, fontWeight: FontWeight.w800),
            filled: true,
            fillColor: const Color(0xFF161616),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: const BorderSide(color: KalisiColors.primaryGold, width: 2),
            ),
            suffixIcon: _isOtpSent
                ? IconButton(
                    icon: const Icon(Icons.edit, color: KalisiColors.primaryGold),
                    onPressed: () => setState(() => _isOtpSent = false),
                  )
                : null,
          ),
        ),
        const SizedBox(height: 14),

        if (!_isOtpSent) ...[
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: _isOtpSending ? null : _handleSendOtp,
              style: ElevatedButton.styleFrom(
                backgroundColor: KalisiColors.primaryGold,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
              ),
              child: _isOtpSending
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                  : const Text('Send Verification Code', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
            ),
          ),
        ],

        // 6-digit OTP Input Section
        if (_isOtpSent) ...[
          const SizedBox(height: 14),
          const Text(
            'Enter 6-Digit Verification Code',
            style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _otpController,
            keyboardType: TextInputType.number,
            maxLength: 6,
            textAlign: TextAlign.center,
            style: const TextStyle(color: KalisiColors.primaryGold, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 8),
            decoration: InputDecoration(
              hintText: '123456',
              hintStyle: const TextStyle(color: Colors.white24, letterSpacing: 8),
              counterText: '',
              filled: true,
              fillColor: const Color(0xFF161616),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(color: KalisiColors.primaryGold, width: 2),
              ),
            ),
          ),
          if (_devOtp != null) ...[
            const SizedBox(height: 6),
            Text(
              'Demo Master OTP: $_devOtp',
              style: const TextStyle(color: Colors.greenAccent, fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 54,
            child: ElevatedButton(
              onPressed: _isSubmitting ? null : _handleCompleteOnboarding,
              style: ElevatedButton.styleFrom(
                backgroundColor: KalisiColors.primaryGold,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(27)),
              ),
              child: _isSubmitting
                  ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.black))
                  : const Text('Verify & Unlock Table', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: TextButton(
              onPressed: _handleSendOtp,
              child: const Text('Resend Code', style: TextStyle(color: Colors.white60, fontSize: 13)),
            ),
          ),
        ],

        if (_otpErrorMessage != null) ...[
          const SizedBox(height: 12),
          Text(_otpErrorMessage!, style: const TextStyle(color: Colors.redAccent, fontSize: 13)),
        ],
      ],
    );
  }
}

// Custom simple controller helper for Flutter
class TextEditing4Controller extends TextEditingController {
  TextEditing4Controller({super.text});
}
