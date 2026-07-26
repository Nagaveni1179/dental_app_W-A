import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'session.dart';
import 'patient_home.dart';
import 'dentist_home.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _age = TextEditingController();
  final _password = TextEditingController();

  String _gender = 'Male';
  String _role = 'patient';
  bool _loading = false;
  bool _obscure = true;

  Future<void> _signup() async {
    if (_name.text.trim().isEmpty ||
        _email.text.trim().isEmpty ||
        _password.text.isEmpty) {
      _snack('Please fill name, email and password');
      return;
    }
    setState(() => _loading = true);
    final res = await ApiService.signup({
      'name': _name.text.trim(),
      'email': _email.text.trim(),
      'phone': _phone.text.trim(),
      'age': int.tryParse(_age.text.trim()) ?? 0,
      'gender': _gender,
      'role': _role,
      'password': _password.text,
    });
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
      _snack(res['error'] ?? 'Sign up failed');
    }
  }

  void _snack(String m) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text(m), backgroundColor: kPrimaryDark));

  Widget _label(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 6, top: 14, left: 2),
        child: Text(t,
            style: const TextStyle(
                fontWeight: FontWeight.w600, color: kText, fontSize: 13.5)),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        title: const Text('Create Account',
            style: TextStyle(fontWeight: FontWeight.w700)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 4, 24, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _label('Full Name'),
            TextField(
                controller: _name,
                decoration: kInput('Your name', Icons.person_outline)),
            _label('Email'),
            TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: kInput('Email address', Icons.email_outlined)),
            _label('Phone'),
            TextField(
                controller: _phone,
                keyboardType: TextInputType.phone,
                decoration: kInput('Phone number', Icons.phone_outlined)),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _label('Age'),
                      TextField(
                          controller: _age,
                          keyboardType: TextInputType.number,
                          decoration: kInput('Age', Icons.cake_outlined)),
                    ],
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _label('Gender'),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                            color: kBg,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: kBorder)),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _gender,
                            isExpanded: true,
                            items: const ['Male', 'Female', 'Other']
                                .map((g) => DropdownMenuItem(
                                    value: g, child: Text(g)))
                                .toList(),
                            onChanged: (v) =>
                                setState(() => _gender = v ?? 'Male'),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            _label('Register as'),
            Row(
              children: [
                _roleChip('Patient', 'patient', Icons.person),
                const SizedBox(width: 10),
                _roleChip('Dentist', 'dentist', Icons.medical_information),
              ],
            ),
            _label('Password'),
            TextField(
              controller: _password,
              obscureText: _obscure,
              decoration: kInput('Create a password', Icons.lock_outline)
                  .copyWith(
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
            const SizedBox(height: 28),
            SizedBox(
              height: 52,
              child: ElevatedButton(
                onPressed: _loading ? null : _signup,
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
                    : const Text('Sign Up',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w600)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _roleChip(String label, String value, IconData icon) {
    final selected = _role == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _role = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: selected ? kPrimary.withOpacity(0.10) : kBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: selected ? kPrimary : kBorder,
                width: selected ? 1.6 : 1),
          ),
          child: Column(
            children: [
              Icon(icon, color: selected ? kPrimary : kTextLight, size: 22),
              const SizedBox(height: 6),
              Text(label,
                  style: TextStyle(
                      color: selected ? kPrimary : kTextLight,
                      fontWeight: FontWeight.w600,
                      fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }
}
