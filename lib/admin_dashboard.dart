import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'admin_users.dart';
import 'admin_reports.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getAdminStats();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 6),
            const Text('Admin Dashboard', style: kH1),
            const SizedBox(height: 4),
            const Text('System overview & management', style: kSub),
            const SizedBox(height: 22),
            FutureBuilder<Map<String, dynamic>>(
              future: _future,
              builder: (context, snap) {
                final s = snap.data ?? {};
                return Column(
                  children: [
                    Row(
                      children: [
                        _stat('Patients', '${s['patients'] ?? 0}',
                            Icons.people_rounded, kPrimary),
                        const SizedBox(width: 12),
                        _stat('Dentists', '${s['dentists'] ?? 0}',
                            Icons.medical_information, kAccent),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        _stat('Scans', '${s['total_scans'] ?? 0}',
                            Icons.camera_alt_rounded, kSuccess),
                        const SizedBox(width: 12),
                        _stat('Reports', '${s['total_reports'] ?? 0}',
                            Icons.description_rounded, kWarning),
                      ],
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            const Text('Management', style: kH2),
            const SizedBox(height: 14),
            _tile(context, 'Manage Users', 'Patients & dentists',
                Icons.group_rounded, const AdminUsers()),
            const SizedBox(height: 12),
            _tile(context, 'System Reports', 'Activity & usage stats',
                Icons.bar_chart_rounded, const AdminReports()),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: kCardDeco,
              child: Row(
                children: [
                  Container(
                    height: 44,
                    width: 44,
                    decoration: BoxDecoration(
                        color: kSuccess.withOpacity(0.14),
                        borderRadius: BorderRadius.circular(12)),
                    child:
                        const Icon(Icons.check_circle_outline, color: kSuccess),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Text('All systems operational. Database healthy.',
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

  Widget _stat(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: kCardDeco,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 40,
              width: 40,
              decoration: BoxDecoration(
                  color: color.withOpacity(0.14),
                  borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(height: 12),
            Text(value,
                style: const TextStyle(
                    fontSize: 24, fontWeight: FontWeight.w800, color: kText)),
            Text(label, style: kSub),
          ],
        ),
      ),
    );
  }

  Widget _tile(BuildContext context, String title, String sub, IconData icon,
      Widget page) {
    return GestureDetector(
      onTap: () =>
          Navigator.push(context, MaterialPageRoute(builder: (_) => page)),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: kCardDeco,
        child: Row(
          children: [
            Container(
              height: 46,
              width: 46,
              decoration: BoxDecoration(
                  color: kPrimary.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: kPrimary),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          color: kText,
                          fontSize: 15)),
                  const SizedBox(height: 3),
                  Text(sub, style: kSub),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: kTextLight),
          ],
        ),
      ),
    );
  }
}
