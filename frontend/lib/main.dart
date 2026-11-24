import 'package:flutter/material.dart';
import 'constants/colors.dart';
import 'screens/welcome_screen.dart';

void main() {
  runApp(const KalisiApp());
}

class KalisiApp extends StatelessWidget {
  const KalisiApp({super.key});

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
      home: const WelcomeScreen(),
    );
  }
}
