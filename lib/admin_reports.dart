import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';

class AdminReports extends StatefulWidget {
  const AdminReports({super.key});

  @override
  State<AdminReports> createState() => _AdminReportsState();
}

class _AdminReportsState extends State<AdminReports> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getAdminStats();
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
        title: const Text('System Reports', style: kH2),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: kPrimary));
          }
          final s = snap.data ?? {};
          return SingleChildScrollView(
            padding: kPagePad,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Summary', style: kH2),
                const SizedBox(height: 14),
                _summaryRow('Total Patients', '${s['patients'] ?? 0}',
                    Icons.people_rounded),
                _summaryRow('Total Dentists', '${s['dentists'] ?? 0}',
                    Icons.medical_information),
                _summaryRow('Oral Scans', '${s['total_scans'] ?? 0}',
                    Icons.camera_alt_rounded),
                _summaryRow('Anesthesia Predictions',
                    '${s['anesthesia_predictions'] ?? 0}',
                    Icons.vaccines_rounded),
                _summaryRow('Consultations', '${s['consultations'] ?? 0}',
                    Icons.forum_rounded),
                _summaryRow('Appointments', '${s['appointments'] ?? 0}',
                    Icons.event_rounded),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _summaryRow(String label, String value, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: kCardDeco,
      child: Row(
        children: [
          Container(
            height: 42,
            width: 42,
            decoration: BoxDecoration(
                color: kPrimary.withOpacity(0.12),
                borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: kPrimary, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(child: Text(label, style: kBody)),
          Text(value,
              style: const TextStyle(
                  fontWeight: FontWeight.w800, color: kText, fontSize: 18)),
        ],
      ),
    );
  }
}
