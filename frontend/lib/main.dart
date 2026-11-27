import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'constants/colors.dart';
import 'screens/welcome_screen.dart';
import 'screens/main_home_screen.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.initialize();
  final prefs = await SharedPreferences.getInstance();
  // Open MainHomeScreen by default.
  // Only show WelcomeScreen (Get started / Already have an account) if the user explicitly logged out!
  final isLoggedOut = prefs.getBool('is_logged_out') ?? false;
  runApp(KalisiApp(startWithWelcome: isLoggedOut));
}

class KalisiApp extends StatelessWidget {
  final bool startWithWelcome;

  const KalisiApp({super.key, this.startWithWelcome = false});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kalisi',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: KalisiColors.background,
        primaryColor: KalisiColors.primaryGold,
        colorScheme: const ColorScheme.dark(
          primary: KalisiColors.primaryGold,
          secondary: KalisiColors.purpleAccent,
          surface: KalisiColors.surface,
        ),
        fontFamily: 'Roboto',
      ),
      home: startWithWelcome ? const WelcomeScreen() : const MainHomeScreen(),
    );
  }
}
