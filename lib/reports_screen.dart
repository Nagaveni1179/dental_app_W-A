import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'session.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final scans = await ApiService.getPatientScans(Session.userId);
    final pains = await ApiService.getPatientPain(Session.userId);
    final List<Map<String, dynamic>> combined = [];
    for (final s in scans) {
      combined.add({
        'type': 'scan',
        'title':
        'Oral Scan${s['condition'] != null && s['condition'] != '' ? ' – ${s['condition']}' : ''}',
        'date': s['created_at'] ?? '',
        'summary': s['summary'] ?? s['analysis'] ?? '',
        'analysis': s['analysis'] ?? '',
        'image_url': s['image_url'] ?? '',
        'review_status': s['review_status'] ?? 'Pending',
        'dentist_name': s['dentist_name'] ?? '',
        'dentist_note': s['dentist_note'] ?? '',
      });
    }
    for (final p in pains) {
      combined.add({
        'type': 'pain',
        'title': 'Pain Assessment',
        'date': p['created_at'] ?? '',
        'summary': 'Severity score ${p['score']}/100 (${p['severity']}).',
        'analysis': p['advice'] ?? '',
        'score': p['score'] ?? 0,
        'severity': p['severity'] ?? '',
        'review_status': '',
        'dentist_note': '',
      });
    }
    return combined;
  }

  IconData _icon(String t) =>
      t == 'pain' ? Icons.healing_rounded : Icons.camera_alt_rounded;

  void _open(Map<String, dynamic> r) {
    Navigator.push(
        context, MaterialPageRoute(builder: (_) => _ReportDetail(report: r)));
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
        title: const Text('My Reports', style: kH2),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: kPrimary));
          }
          final reports = snap.data ?? [];
          if (reports.isEmpty) {
            return const Center(child: Text('No reports yet', style: kSub));
          }
          return RefreshIndicator(
            color: kPrimary,
            onRefresh: () async => setState(() => _future = _load()),
            child: ListView.separated(
              padding: kPagePad,
              itemCount: reports.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (_, i) {
                final r = reports[i];
                final reviewed = r['review_status'] == 'Reviewed';
                return GestureDetector(
                  onTap: () => _open(r),
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: kCardDeco,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              height: 44,
                              width: 44,
                              decoration: BoxDecoration(
                                  color: kPrimary.withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(12)),
                              child: Icon(_icon(r['type']), color: kPrimary),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(r['title'],
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                          color: kText,
                                          fontSize: 15)),
                                  const SizedBox(height: 3),
                                  Text(r['date'], style: kSub),
                                ],
                              ),
                            ),
                            if (r['type'] == 'scan')
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 9, vertical: 4),
                                decoration: BoxDecoration(
                                  color: (reviewed ? kSuccess : kWarning)
                                      .withOpacity(0.14),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Text(reviewed ? 'Reviewed' : 'Pending',
                                    style: TextStyle(
                                        color: reviewed ? kSuccess : kWarning,
                                        fontWeight: FontWeight.w700,
                                        fontSize: 11)),
                              ),
                          ],
                        ),
                        if ((r['summary'] as String).isNotEmpty) ...[
                          const SizedBox(height: 12),
                          Text(r['summary'],
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: kBody),
                        ],
                        if ((r['dentist_note'] ?? '').toString().isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Row(
                            children: const [
                              Icon(Icons.verified_outlined,
                                  size: 15, color: kSuccess),
                              SizedBox(width: 5),
                              Text('Dentist recommendation available',
                                  style: TextStyle(
                                      color: kSuccess,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600)),
                            ],
                          ),
                        ],
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: const [
                            Text('View full report',
                                style: TextStyle(
                                    color: kPrimary,
                                    fontSize: 12.5,
                                    fontWeight: FontWeight.w700)),
                            Icon(Icons.chevron_right,
                                color: kPrimary, size: 18),
                          ],
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

// ── FULL REPORT DETAIL ──────────────────────────────────────
class _ReportDetail extends StatelessWidget {
  final Map<String, dynamic> report;
  const _ReportDetail({required this.report});

  @override
  Widget build(BuildContext context) {
    final r = report;
    final isScan = r['type'] == 'scan';
    final note = (r['dentist_note'] ?? '').toString();
    final analysis = (r['analysis'] ?? '').toString();
    final imageUrl = (r['image_url'] ?? '').toString();

    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kBg,
        elevation: 0,
        foregroundColor: kText,
        centerTitle: false,
        title: const Text('Report Detail', style: kH2),
      ),
      body: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(r['title'], style: kH2),
            const SizedBox(height: 4),
            Text(r['date'], style: kSub),
            const SizedBox(height: 18),

            // Oral image (scans only)
            if (isScan && imageUrl.isNotEmpty) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(kRadius),
                child: Image.network(
                  imageUrl,
                  height: 220,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    height: 220,
                    decoration: BoxDecoration(
                        color: kCard,
                        borderRadius: BorderRadius.circular(kRadius),
                        border: Border.all(color: kBorder)),
                    child: const Center(
                        child: Icon(Icons.image_not_supported_outlined,
                            color: kTextLight)),
                  ),
                ),
              ),
              const SizedBox(height: 18),
            ],

            // Pain score block (pain only)
            if (!isScan) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: kCardDeco,
                child: Column(
                  children: [
                    Text('${r['score'] ?? 0}',
                        style: const TextStyle(
                            fontSize: 40,
                            fontWeight: FontWeight.w800,
                            color: kPrimary)),
                    Text('out of 100  •  ${r['severity'] ?? ''}', style: kSub),
                  ],
                ),
              ),
              const SizedBox(height: 18),
            ],

            // AI analysis / advice
            _sectionTitle(isScan ? 'AI Analysis' : 'Advice'),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: kCardDeco,
              child: Text(
                  analysis.isNotEmpty
                      ? analysis
                      : (r['summary'] ?? 'No details.'),
                  style: kBody),
            ),

            // Dentist recommendation
            if (note.isNotEmpty) ...[
              const SizedBox(height: 18),
              _sectionTitle('Dentist Recommendation'),
              const SizedBox(height: 10),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: kSuccess.withOpacity(0.07),
                  borderRadius: BorderRadius.circular(kRadius),
                  border: Border.all(color: kSuccess.withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.verified, color: kSuccess, size: 18),
                        const SizedBox(width: 6),
                        Text(
                            (r['dentist_name'] ?? 'Your dentist').toString(),
                            style: const TextStyle(
                                fontWeight: FontWeight.w700,
                                color: kText,
                                fontSize: 14)),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(note, style: kBody),
                  ],
                ),
              ),
            ] else if (isScan) ...[
              const SizedBox(height: 18),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: kCardDeco,
                child: Row(
                  children: const [
                    Icon(Icons.hourglass_empty, color: kWarning, size: 18),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                          'Awaiting dentist review. You will see their recommendation here.',
                          style: kSub),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String t) => Text(t, style: kH2);
}