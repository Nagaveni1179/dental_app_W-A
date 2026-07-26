import 'package:flutter/material.dart';
import 'api_service.dart';
import 'session.dart';
import 'signup_screen.dart';
import 'patient_home.dart';
import 'dentist_home.dart';
import 'admin_home.dart';

// ============================================================================
// SHARED THEME CONSTANTS (imported by every other screen)
// ============================================================================
const Color kPrimary = Color(0xFF00838F);
const Color kPrimaryDark = Color(0xFF006064);
const Color kAccent = Color(0xFF26C6DA);
const Color kBg = Color(0xFFF3F8FA);
const Color kCard = Colors.white;
const Color kText = Color(0xFF12303A);
const Color kTextLight = Color(0xFF6B8189);
const Color kBorder = Color(0xFFE0EAEE);
const Color kSuccess = Color(0xFF2E9E6B);
const Color kWarning = Color(0xFFE6A23C);
const Color kDanger = Color(0xFFD9534F);

const double kRadius = 16.0;
const EdgeInsets kPagePad = EdgeInsets.all(20);

const TextStyle kH1 = TextStyle(
    fontSize: 26, fontWeight: FontWeight.w700, color: kText, height: 1.2);
const TextStyle kH2 = TextStyle(
    fontSize: 19, fontWeight: FontWeight.w700, color: kText);
const TextStyle kBody = TextStyle(fontSize: 14.5, color: kText, height: 1.45);
const TextStyle kSub = TextStyle(fontSize: 13, color: kTextLight);

BoxDecoration kCardDeco = BoxDecoration(
  color: kCard,
  borderRadius: BorderRadius.circular(kRadius),
  border: Border.all(color: kBorder),
  boxShadow: const [
    BoxShadow(color: Color(0x0A0F2C33), blurRadius: 14, offset: Offset(0, 6))
  ],
);

InputDecoration kInput(String hint, IconData icon) => InputDecoration(
      hintText: hint,
      prefixIcon: Icon(icon, color: kPrimary, size: 20),
      hintStyle: const TextStyle(color: kTextLight, fontSize: 14),
      filled: true,
      fillColor: kBg,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: kBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: kPrimary, width: 1.6),
      ),
    );

// ============================================================================
// LOGIN SCREEN
// ============================================================================
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _loading = false;
  bool _obscure = true;

  // Frontend-only admin credentials (not stored in backend).
  static const String _adminEmail = 'admin@gmail.com';
  static const String _adminPassword = 'admin123';

  Future<void> _login() async {
    if (_email.text.trim().isEmpty || _password.text.isEmpty) {
      _snack('Please enter email and password');
      return;
    }

    // Admin is handled entirely on the frontend.
    if (_email.text.trim() == _adminEmail &&
        _password.text == _adminPassword) {
      Session.setUser(
        id: 0,
        userName: 'Administrator',
        userEmail: _adminEmail,
        userRole: 'admin',
      );
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const AdminHome()),
      );
      return;
    }

    setState(() => _loading = true);
    final res = await ApiService.login(_email.text.trim(), _password.text);
    setState(() => _loading = false);

    if (res['user'] != null) {
      final u = res['user'];
      Session.setUser(
        id: u['id'] ?? 0,
        userName: u['name'] ?? '',
        userEmail: u['email'] ?? '',
        userRole: u['role'] ?? 'patient',
        userPhone: u['phone'] ?? '',
        userAge: u['age'] ?? 0,
        userGender: u['gender'] ?? '',
      );
      if (!mounted) return;
      final home = Session.role == 'dentist'
          ? const DentistHome()
          : const PatientHome();
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => home),
      );
    } else {
      _snack(res['error'] ?? 'Login failed');
    }
  }

  void _snack(String m) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text(m), backgroundColor: kPrimaryDark));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 20),
              Container(
                height: 84,
                width: 84,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                      colors: [kPrimary, kAccent],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.medical_services_rounded,
                    color: Colors.white, size: 42),
              ),
              const SizedBox(height: 22),
              const Center(child: Text('Dental Insight', style: kH1)),
              const SizedBox(height: 6),
              const Center(
                child: Text('AI-powered oral health assessment',
                    style: kSub, textAlign: TextAlign.center),
              ),
              const SizedBox(height: 36),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: kInput('Email address', Icons.email_outlined),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _password,
                obscureText: _obscure,
                decoration:
                    kInput('Password', Icons.lock_outline).copyWith(
                  suffixIcon: IconButton(
                    icon: Icon(
                        _obscure
                            ? Icons.visibility_off_outlined
                            : Icons.visibility_outlined,
                        color: kTextLight,
                        size: 20),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),
              const SizedBox(height: 26),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _loading ? null : _login,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: kPrimary,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                  ),
                  child: _loading
                      ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2.4))
                      : const Text('Log In',
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.w600)),
                ),
              ),
              const SizedBox(height: 18),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text("Don't have an account? ", style: kSub),
                  GestureDetector(
                    onTap: () => Navigator.push(context,
                        MaterialPageRoute(builder: (_) => const SignupScreen())),
                    child: const Text('Sign Up',
                        style: TextStyle(
                            color: kPrimary, fontWeight: FontWeight.w700)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
