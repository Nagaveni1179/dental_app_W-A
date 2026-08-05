import 'dart:convert';
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
  String _filter = 'All'; // 'All', 'Consulted', 'Not Consulted'

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() {
    String? status;
    if (_filter == 'Consulted') status = 'Reviewed';
    if (_filter == 'Not Consulted') status = 'Pending';
    
    setState(() {
      _future = ApiService.getAllScans(status: status);
    });
  }

  void _setFilter(String f) {
    setState(() => _filter = f);
    _loadData();
  }

  void _consult(int scanId, String name) {
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
            Text('Consult with $name', style: kH2),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              maxLines: 4,
              decoration: kInput("Doctor's Notes & Consultation", Icons.edit_outlined),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: () async {
                  await ApiService.reviewScan(
                      scanId, 
                      dentistId: Session.userId, 
                      dentistName: Session.name.isNotEmpty ? Session.name : 'Dr. Dentist',
                      dentistNote: controller.text.trim());
                  if (ctx.mounted) Navigator.pop(ctx);
                  _loadData();
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: kPrimary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text('Submit Consultation'),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _imageThumbnail(String url) {
    if (url.isEmpty) return Container(width: 80, height: 80, color: kBg);
    if (url.startsWith('data:image')) {
      try {
        return Image.memory(
          base64Decode(url.split(',').last),
          width: 80,
          height: 80,
          fit: BoxFit.cover,
        );
      } catch (e) {
        return Container(width: 80, height: 80, color: kBg);
      }
    }
    return Image.network(
      url,
      width: 80,
      height: 80,
      fit: BoxFit.cover,
      errorBuilder: (_,__,___) => Container(width: 80, height: 80, color: kBg),
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
      body: Column(
        children: [
          // Filters
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _filterChip('All'),
                const SizedBox(width: 8),
                _filterChip('Not Consulted'),
                const SizedBox(width: 8),
                _filterChip('Consulted'),
              ],
            ),
          ),
          
          Expanded(
            child: FutureBuilder<List<dynamic>>(
              future: _future,
              builder: (context, snap) {
                if (snap.connectionState == ConnectionState.waiting) {
                  return const Center(
                      child: CircularProgressIndicator(color: kPrimary));
                }
                final items = snap.data ?? [];
                if (items.isEmpty) {
                  return const Center(
                      child: Text('No scans found', style: kSub));
                }
                return RefreshIndicator(
                  color: kPrimary,
                  onRefresh: () async => _loadData(),
                  child: ListView.separated(
                    padding: kPagePad,
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (_, i) {
                      final s = items[i] as Map<String, dynamic>;
                      final isPending = (s['review_status'] ?? 'Pending') == 'Pending';
                      final name = s['patient_name'] ?? 'Patient';
                      
                      return Container(
                        padding: const EdgeInsets.all(16),
                        decoration: kCardDeco,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    name,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 16,
                                        color: kText),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 10, vertical: 5),
                                  decoration: BoxDecoration(
                                    color: (isPending ? kWarning : kSuccess)
                                        .withOpacity(0.14),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(isPending ? 'Not Consulted' : 'Consulted',
                                      style: TextStyle(
                                          color: isPending ? kWarning : kSuccess,
                                          fontWeight: FontWeight.w700,
                                          fontSize: 11.5)),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(s['created_at'] ?? '', style: kSub.copyWith(fontSize: 12)),
                            const Divider(height: 24, color: kBorder),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: _imageThumbnail(s['image_url'] ?? ''),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('AI Prediction', style: kSub.copyWith(fontWeight: FontWeight.w600)),
                                      const SizedBox(height: 4),
                                      Text(
                                        s['summary'] ?? s['analysis'] ?? 'No prediction available', 
                                        maxLines: 3, 
                                        overflow: TextOverflow.ellipsis,
                                        style: kBody.copyWith(fontSize: 13),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            if (isPending)
                              SizedBox(
                                width: double.infinity,
                                child: ElevatedButton(
                                  onPressed: () => _consult(s['id'], name),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: kPrimary,
                                    foregroundColor: Colors.white,
                                    elevation: 0,
                                    shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(10)),
                                  ),
                                  child: const Text('Consult'),
                                ),
                              ),
                            if (!isPending && s['dentist_note'] != null && s['dentist_note'].toString().isNotEmpty)
                               Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: kBg,
                                  borderRadius: BorderRadius.circular(8)
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('Your Consultation:', style: TextStyle(fontWeight: FontWeight.w600, color: kText, fontSize: 13)),
                                    const SizedBox(height: 4),
                                    Text(s['dentist_note'], style: kSub.copyWith(color: kText)),
                                  ]
                                )
                              )
                          ],
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label) {
    final selected = _filter == label;
    return GestureDetector(
      onTap: () => _setFilter(label),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? kPrimary : kBg,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? kPrimary : kBorder),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.white : kTextLight,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            fontSize: 13,
          ),
        ),
      ),
    );
  }
}
