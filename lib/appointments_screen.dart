import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'session.dart';

class AppointmentsScreen extends StatefulWidget {
  const AppointmentsScreen({super.key});

  @override
  State<AppointmentsScreen> createState() => _AppointmentsScreenState();
}

class _AppointmentsScreenState extends State<AppointmentsScreen> {
  late Future<List<dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getPatientAppointments(Session.userId);
  }

  void _refresh() {
    setState(() {
      _future = ApiService.getPatientAppointments(Session.userId);
    });
  }

  Future<void> _book() async {
    // Load dentists for the dropdown.
    final dentists = await ApiService.getUsers(role: 'dentist');
    if (!mounted) return;

    Map<String, dynamic>? dentist =
        dentists.isNotEmpty ? dentists.first as Map<String, dynamic> : null;
    DateTime date = DateTime.now().add(const Duration(days: 1));
    TimeOfDay time = const TimeOfDay(hour: 10, minute: 0);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: kCard,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheet) => Padding(
          padding: EdgeInsets.fromLTRB(
              20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Book Appointment', style: kH2),
              const SizedBox(height: 16),
              if (dentists.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text('No dentists available yet.', style: kSub),
                )
              else
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  decoration: BoxDecoration(
                      color: kBg,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: kBorder)),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<Map<String, dynamic>>(
                      value: dentist,
                      isExpanded: true,
                      items: dentists
                          .map((d) => DropdownMenuItem(
                              value: d as Map<String, dynamic>,
                              child: Text('Dr. ${d['name']}')))
                          .toList(),
                      onChanged: (v) => setSheet(() => dentist = v),
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        final d = await showDatePicker(
                          context: ctx,
                          initialDate: date,
                          firstDate: DateTime.now(),
                          lastDate:
                              DateTime.now().add(const Duration(days: 120)),
                        );
                        if (d != null) setSheet(() => date = d);
                      },
                      icon: const Icon(Icons.calendar_today, size: 16),
                      label: Text('${date.day}/${date.month}/${date.year}'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        final t = await showTimePicker(
                            context: ctx, initialTime: time);
                        if (t != null) setSheet(() => time = t);
                      },
                      icon: const Icon(Icons.access_time, size: 16),
                      label: Text(time.format(ctx)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              SizedBox(
                height: 50,
                child: ElevatedButton(
                  onPressed: dentist == null
                      ? null
                      : () async {
                          await ApiService.addAppointment({
                            'patient_id': Session.userId,
                            'patient_name': Session.name,
                            'dentist_id': dentist!['id'],
                            'dentist_name': 'Dr. ${dentist!['name']}',
                            'date': '${date.day}/${date.month}/${date.year}',
                            'time': time.format(ctx),
                          });
                          if (ctx.mounted) Navigator.pop(ctx);
                          _refresh();
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: kPrimary,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                  ),
                  child: const Text('Confirm Booking'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
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
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _book,
        backgroundColor: kPrimary,
        icon: const Icon(Icons.add),
        label: const Text('Book'),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator(color: kPrimary));
          }
          final items = snap.data ?? [];
          if (items.isEmpty) {
            return const Center(child: Text('No appointments yet', style: kSub));
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
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: kCardDeco,
                  child: Row(
                    children: [
                      Container(
                        height: 48,
                        width: 48,
                        decoration: BoxDecoration(
                            color: kPrimary.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(12)),
                        child: const Icon(Icons.medical_information,
                            color: kPrimary),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(a['dentist_name'] ?? '',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: kText,
                                    fontSize: 15)),
                            const SizedBox(height: 4),
                            Text('${a['date']}  •  ${a['time']}', style: kSub),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: _statusColor(a['status'] ?? 'Pending')
                              .withOpacity(0.14),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(a['status'] ?? 'Pending',
                            style: TextStyle(
                                color: _statusColor(a['status'] ?? 'Pending'),
                                fontWeight: FontWeight.w700,
                                fontSize: 11.5)),
                      ),
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
