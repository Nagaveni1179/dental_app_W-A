import 'package:flutter/material.dart';
import 'splash_screen.dart';
import 'login_screen.dart';

void main() => runApp(const DentalInsightApp());

class DentalInsightApp extends StatelessWidget {
  const DentalInsightApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dental Insight',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        scaffoldBackgroundColor: kBg,
        colorScheme: ColorScheme.fromSeed(seedColor: kPrimary),
        fontFamily: 'Roboto',
        useMaterial3: true,
      ),
      home: const SplashScreen(),
    );
  }
}
