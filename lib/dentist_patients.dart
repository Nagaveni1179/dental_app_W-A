import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'patient_detail.dart';

class DentistPatients extends StatefulWidget {
  const DentistPatients({super.key});

  @override
  State<DentistPatients> createState() => _DentistPatientsState();
}

class _DentistPatientsState extends State<DentistPatients> {
  late Future<List<dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getDentistPatients();
  }

  Color _riskColor(String r) =>
      r == 'High' ? kDanger : (r == 'Moderate' ? kWarning : kSuccess);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        centerTitle: false,
        title: const Text('Patients', style: kH2),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: kPrimary));
          }
          final patients = snap.data ?? [];
          if (patients.isEmpty) {
            return const Center(child: Text('No patients yet', style: kSub));
          }
          return RefreshIndicator(
            color: kPrimary,
            onRefresh: () async =>
                setState(() => _future = ApiService.getDentistPatients()),
            child: ListView.separated(
              padding: kPagePad,
              itemCount: patients.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (_, i) {
                final p = patients[i] as Map<String, dynamic>;
                final risk = p['risk'] ?? 'Low';
                return GestureDetector(
                  onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) =>
                              PatientDetail(patientId: p['id']))),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: kCardDeco,
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 24,
                          backgroundColor: kPrimary.withOpacity(0.12),
                          child: Text(
                              (p['name'] ?? '?').toString().isNotEmpty
                                  ? p['name'][0]
                                  : '?',
                              style: const TextStyle(
                                  color: kPrimary,
                                  fontWeight: FontWeight.w700)),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(p['name'] ?? '',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                      color: kText,
                                      fontSize: 15)),
                              const SizedBox(height: 3),
                              Text(
                                  '${p['age']} • ${p['gender']} • ${p['condition']}',
                                  style: kSub),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: _riskColor(risk).withOpacity(0.14),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(risk,
                              style: TextStyle(
                                  color: _riskColor(risk),
                                  fontWeight: FontWeight.w700,
                                  fontSize: 11.5)),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
