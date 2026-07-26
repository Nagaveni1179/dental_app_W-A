import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'session.dart';

class DentistConsultations extends StatefulWidget {
  const DentistConsultations({super.key});

  @override
  State<DentistConsultations> createState() => _DentistConsultationsState();
}

class _DentistConsultationsState extends State<DentistConsultations> {
  late Future<List<dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getAllConsultations();
  }

  void _refresh() =>
      setState(() => _future = ApiService.getAllConsultations());

  void _reply(int id, String name) {
    final controller = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: kCard,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(
            20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Reply to $name', style: kH2),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              maxLines: 4,
              decoration: kInput('Type your response...', Icons.edit_outlined),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: () async {
                  await ApiService.replyConsultation(
                      id, Session.userId, controller.text.trim());
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
                child: const Text('Send Reply'),
              ),
            ),
          ],
        ),
      ),
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
        title: const Text('Consultations', style: kH2),
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
                child: Text('No consultations yet', style: kSub));
          }
          return RefreshIndicator(
            color: kPrimary,
            onRefresh: () async => _refresh(),
            child: ListView.separated(
              padding: kPagePad,
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (_, i) {
                final c = items[i] as Map<String, dynamic>;
                final pending = (c['status'] ?? 'Pending') == 'Pending';
                final name = c['patient_name'] ?? 'Patient';
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: kCardDeco,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 18,
                            backgroundColor: kPrimary.withOpacity(0.12),
                            child: Text(
                                name.toString().isNotEmpty ? name[0] : '?',
                                style: const TextStyle(
                                    color: kPrimary,
                                    fontWeight: FontWeight.w700)),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(name,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: kText)),
                          ),
                          Text(c['created_at'] ?? '', style: kSub),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Text(c['message'] ?? '', style: kBody),
                      if ((c['reply'] ?? '').toString().isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                              color: kBg,
                              borderRadius: BorderRadius.circular(10)),
                          child: Text('You: ${c['reply']}',
                              style: kSub.copyWith(color: kText)),
                        ),
                      ],
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: (pending ? kWarning : kSuccess)
                                  .withOpacity(0.14),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(c['status'] ?? 'Pending',
                                style: TextStyle(
                                    color: pending ? kWarning : kSuccess,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 11.5)),
                          ),
                          const Spacer(),
                          if (pending)
                            TextButton(
                              onPressed: () => _reply(c['id'], name),
                              child: const Text('Reply',
                                  style: TextStyle(
                                      color: kPrimary,
                                      fontWeight: FontWeight.w700)),
                            ),
                        ],
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
