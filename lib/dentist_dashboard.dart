import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'session.dart';
import 'api_service.dart';
import 'dentist_patients.dart';
import 'dentist_consultations.dart';

class DentistDashboard extends StatefulWidget {
  const DentistDashboard({super.key});

  @override
  State<DentistDashboard> createState() => _DentistDashboardState();
}

class _DentistDashboardState extends State<DentistDashboard> {
  late Future<Map<String, int>> _future;

  @override
  void initState() {
    super.initState();
    _future = _loadStats();
  }

  Future<Map<String, int>> _loadStats() async {
    final patients = await ApiService.getDentistPatients();
    final pending = await ApiService.getAllConsultations(status: 'Pending');
    final appts = await ApiService.getAllAppointments();
    final today = appts.where((a) => (a['status'] ?? '') == 'Pending').length;
    final highRisk =
        patients.where((p) => (p['risk'] ?? '') == 'High').length;
    return {
      'patients': patients.length,
      'pending': pending.length,
      'today': today,
      'highRisk': highRisk,
    };
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
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Welcome back,',
                          style: kSub.copyWith(fontSize: 14)),
                      Text(
                          'Dr. ${Session.name.isEmpty ? 'Dentist' : Session.name}',
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
                  child: const Icon(Icons.medical_information, color: kPrimary),
                ),
              ],
            ),
            const SizedBox(height: 22),
            FutureBuilder<Map<String, int>>(
              future: _future,
              builder: (context, snap) {
                final s = snap.data ??
                    {'patients': 0, 'pending': 0, 'today': 0, 'highRisk': 0};
                return Column(
                  children: [
                    Row(
                      children: [
                        _stat('Patients', '${s['patients']}',
                            Icons.people_rounded, kPrimary),
                        const SizedBox(width: 12),
                        _stat('Pending', '${s['pending']}',
                            Icons.forum_rounded, kWarning),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        _stat('Requests', '${s['today']}',
                            Icons.event_rounded, kSuccess),
                        const SizedBox(width: 12),
                        _stat('High Risk', '${s['highRisk']}',
                            Icons.warning_amber_rounded, kDanger),
                      ],
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            const Text('Quick Access', style: kH2),
            const SizedBox(height: 14),
            _tile(context, 'Patient Records', 'View scans, pain & predictions',
                Icons.folder_shared_rounded, const DentistPatients()),
            const SizedBox(height: 12),
            _tile(context, 'Consultation Requests', 'Reply to patients',
                Icons.forum_rounded, const DentistConsultations()),
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
