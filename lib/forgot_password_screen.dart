import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _email = TextEditingController();
  final _newPassword = TextEditingController();
  final _confirmPassword = TextEditingController();

  bool _loading = false;
  bool _obscureNew = true;
  bool _obscureConfirm = true;

  Future<void> _reset() async {
    if (_email.text.trim().isEmpty) {
      _snack('Please enter your email');
      return;
    }
    if (_newPassword.text.isEmpty || _newPassword.text.length < 6) {
      _snack('Password must be at least 6 characters');
      return;
    }
    if (_newPassword.text != _confirmPassword.text) {
      _snack('Passwords do not match');
      return;
    }
    setState(() => _loading = true);
    final res = await ApiService.resetPassword(
      email: _email.text.trim(),
      newPassword: _newPassword.text,
    );
    setState(() => _loading = false);

    if (res['message'] != null) {
      _snack('Password reset successfully');
      if (!mounted) return;
      Navigator.pop(context);
    } else {
      _snack(res['error'] ?? 'Reset failed. Check your email.');
    }
  }

  void _snack(String m) => ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(m), backgroundColor: kPrimaryDark));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        title: const Text('Forgot Password',
            style: TextStyle(fontWeight: FontWeight.w700)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            Container(
              height: 72,
              width: 72,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: kPrimary.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child:
                  const Icon(Icons.lock_reset_rounded, color: kPrimary, size: 36),
            ),
            const SizedBox(height: 22),
            const Text('Reset your password', style: kH1),
            const SizedBox(height: 8),
            const Text(
                'Enter your registered email and a new password.',
                style: kSub),
            const SizedBox(height: 30),
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: kInput('Email address', Icons.email_outlined),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _newPassword,
              obscureText: _obscureNew,
              decoration: kInput('New password', Icons.lock_outline).copyWith(
                suffixIcon: IconButton(
                  icon: Icon(
                      _obscureNew
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: kTextLight,
                      size: 20),
                  onPressed: () => setState(() => _obscureNew = !_obscureNew),
                ),
              ),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _confirmPassword,
              obscureText: _obscureConfirm,
              decoration:
                  kInput('Confirm new password', Icons.lock_outline).copyWith(
                suffixIcon: IconButton(
                  icon: Icon(
                      _obscureConfirm
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: kTextLight,
                      size: 20),
                  onPressed: () =>
                      setState(() => _obscureConfirm = !_obscureConfirm),
                ),
              ),
            ),
            const SizedBox(height: 26),
            SizedBox(
              height: 52,
              child: ElevatedButton(
                onPressed: _loading ? null : _reset,
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
                    : const Text('Reset Password',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w600)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
