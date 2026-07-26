import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';

class DentistAppointments extends StatefulWidget {
  const DentistAppointments({super.key});

  @override
  State<DentistAppointments> createState() => _DentistAppointmentsState();
}

class _DentistAppointmentsState extends State<DentistAppointments> {
  late Future<List<dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getAllAppointments();
  }

  void _refresh() =>
      setState(() => _future = ApiService.getAllAppointments());

  Future<void> _setStatus(int id, String status) async {
    await ApiService.updateAppointmentStatus(id, status);
    _refresh();
  }

  Color _statusColor(String s) =>
      s == 'Confirmed' ? kSuccess : (s == 'Declined' ? kDanger : kWarning);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        centerTitle: false,
        title: const Text('Appointments', style: kH2),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: kPrimary));
          }
          final items = snap.data ?? [];
          if (items.isEmpty) {
            return const Center(
                child: Text('No appointments yet', style: kSub));
          }
          return RefreshIndicator(
            color: kPrimary,
            onRefresh: () async => _refresh(),
            child: ListView.separated(
              padding: kPagePad,
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (_, i) {
                final a = items[i] as Map<String, dynamic>;
                final status = a['status'] ?? 'Pending';
                final pending = status == 'Pending';
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: kCardDeco,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            height: 46,
                            width: 46,
                            decoration: BoxDecoration(
                                color: kPrimary.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(12)),
                            child: const Icon(Icons.person, color: kPrimary),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(a['patient_name'] ?? '',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: kText,
                                        fontSize: 15)),
                                const SizedBox(height: 4),
                                Text('${a['date']}  •  ${a['time']}',
                                    style: kSub),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: _statusColor(status).withOpacity(0.14),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(status,
                                style: TextStyle(
                                    color: _statusColor(status),
                                    fontWeight: FontWeight.w700,
                                    fontSize: 11.5)),
                          ),
                        ],
                      ),
                      if (pending) ...[
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton(
                                onPressed: () =>
                                    _setStatus(a['id'], 'Declined'),
                                style: OutlinedButton.styleFrom(
                                  side: const BorderSide(color: kDanger),
                                  shape: RoundedRectangleBorder(
                                      borderRadius:
                                          BorderRadius.circular(10)),
                                ),
                                child: const Text('Decline',
                                    style: TextStyle(color: kDanger)),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: ElevatedButton(
                                onPressed: () =>
                                    _setStatus(a['id'], 'Confirmed'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: kPrimary,
                                  foregroundColor: Colors.white,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                      borderRadius:
                                          BorderRadius.circular(10)),
                                ),
                                child: const Text('Confirm'),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
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
