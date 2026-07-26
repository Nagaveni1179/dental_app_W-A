import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'session.dart';
import 'anesthesia_screen.dart';
import 'reports_screen.dart';
import 'scan_screen.dart';
import 'pain_screen.dart';

class HomeTab extends StatelessWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Hello,', style: kSub.copyWith(fontSize: 14)),
                      Text(
                          Session.name.isEmpty ? 'Patient' : Session.name,
                          style: kH1),
                    ],
                  ),
                ),
                Container(
                  height: 48,
                  width: 48,
                  decoration: BoxDecoration(
                      color: kPrimary.withOpacity(0.12),
                      shape: BoxShape.circle),
                  child: const Icon(Icons.person, color: kPrimary),
                ),
              ],
            ),
            const SizedBox(height: 22),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                    colors: [kPrimary, kAccent],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight),
                borderRadius: BorderRadius.circular(kRadius),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('AI Oral Screening',
                      style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  Text('Snap a photo of your teeth to detect issues instantly.',
                      style: TextStyle(
                          color: Colors.white.withOpacity(0.9), fontSize: 13)),
                  const SizedBox(height: 14),
                  GestureDetector(
                    onTap: () => Navigator.push(context,
                        MaterialPageRoute(builder: (_) => const ScanScreen())),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 9),
                      decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(30)),
                      child: const Text('Start Scan',
                          style: TextStyle(
                              color: kPrimaryDark,
                              fontWeight: FontWeight.w700,
                              fontSize: 13)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const Text('Quick Actions', style: kH2),
            const SizedBox(height: 14),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 14,
              crossAxisSpacing: 14,
              childAspectRatio: 1.22,
              children: [
                _action(context, 'Oral Scan', Icons.camera_alt_rounded,
                    kPrimary, const ScanScreen()),
                _action(context, 'Pain Score', Icons.healing_rounded,
                    kWarning, const PainScreen()),
                _action(context, 'Anesthesia\nPredict',
                    Icons.vaccines_rounded, kDanger, const AnesthesiaScreen()),
                _action(context, 'My Reports', Icons.description_rounded,
                    kSuccess, const ReportsScreen()),
              ],
            ),
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: kCardDeco,
              child: Row(
                children: [
                  Container(
                    height: 44,
                    width: 44,
                    decoration: BoxDecoration(
                        color: kAccent.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(12)),
                    child: const Icon(Icons.tips_and_updates_outlined,
                        color: kPrimary),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Text(
                        'Tip: Brush twice daily and replace your toothbrush every 3 months.',
                        style: kBody),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _action(BuildContext context, String label, IconData icon,
      Color color, Widget page) {
    return GestureDetector(
      onTap: () => Navigator.push(
          context, MaterialPageRoute(builder: (_) => page)),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: kCardDeco,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Container(
              height: 42,
              width: 42,
              decoration: BoxDecoration(
                  color: color.withOpacity(0.14),
                  borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: color, size: 22),
            ),
            Flexible(
              child: Text(label,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      color: kText,
                      fontSize: 14.5)),
            ),
          ],
        ),
      ),
    );
  }
}
