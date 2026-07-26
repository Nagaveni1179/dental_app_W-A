import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'session.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  void _logout(BuildContext context) {
    Session.clear();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        centerTitle: false,
        title: const Text('Profile', style: kH2),
      ),
      body: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          children: [
            const SizedBox(height: 8),
            Container(
              height: 96,
              width: 96,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                    colors: [kPrimary, kAccent],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight),
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text(
                Session.name.isNotEmpty
                    ? Session.name[0].toUpperCase()
                    : 'P',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 38,
                    fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(height: 14),
            Text(Session.name.isEmpty ? 'Patient' : Session.name, style: kH2),
            const SizedBox(height: 4),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
              decoration: BoxDecoration(
                  color: kPrimary.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(20)),
              child: Text(Session.role.toUpperCase(),
                  style: const TextStyle(
                      color: kPrimary,
                      fontWeight: FontWeight.w700,
                      fontSize: 11.5)),
            ),
            const SizedBox(height: 26),
            Container(
              decoration: kCardDeco,
              child: Column(
                children: [
                  _row(Icons.email_outlined, 'Email',
                      Session.email.isEmpty ? '—' : Session.email),
                  _divider(),
                  _row(Icons.phone_outlined, 'Phone',
                      Session.phone.isEmpty ? '—' : Session.phone),
                  _divider(),
                  _row(Icons.cake_outlined, 'Age',
                      Session.age == 0 ? '—' : Session.age.toString()),
                  _divider(),
                  _row(Icons.wc_outlined, 'Gender',
                      Session.gender.isEmpty ? '—' : Session.gender),
                ],
              ),
            ),
            const SizedBox(height: 26),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: OutlinedButton.icon(
                onPressed: () => _logout(context),
                icon: const Icon(Icons.logout, color: kDanger),
                label: const Text('Log Out',
                    style: TextStyle(
                        color: kDanger, fontWeight: FontWeight.w700)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: kDanger),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(IconData icon, String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          children: [
            Icon(icon, color: kPrimary, size: 20),
            const SizedBox(width: 14),
            Text(label, style: kSub),
            const Spacer(),
            Flexible(
              child: Text(value,
                  textAlign: TextAlign.right,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, color: kText)),
            ),
          ],
        ),
      );

  Widget _divider() =>
      const Divider(height: 1, color: kBorder, indent: 16, endIndent: 16);
}
