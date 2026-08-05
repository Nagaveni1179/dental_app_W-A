import 'dart:convert';
import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'api_service.dart';
import 'session.dart';

class PatientDetail extends StatefulWidget {
  final int patientId;
  const PatientDetail({super.key, required this.patientId});

  @override
  State<PatientDetail> createState() => _PatientDetailState();
}

class _PatientDetailState extends State<PatientDetail> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService.getDentistPatientDetail(widget.patientId);
  }

  Color _scoreColor(int s) =>
      s >= 70 ? kDanger : (s >= 40 ? kWarning : kSuccess);
  String _scoreLabel(int s) =>
      s >= 70 ? 'Severe' : (s >= 40 ? 'Moderate' : 'Mild');

  void _sendRecommendation() async {
    // Attach the recommendation to the patient's latest scan.
    final scans = await ApiService.getPatientScans(widget.patientId);
    if (!mounted) return;
    if (scans.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('This patient has no scan to attach a note to yet'),
          backgroundColor: kPrimaryDark));
      return;
    }
    final int scanId = scans.first['id'];
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
            const Text('Send Recommendation', style: kH2),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              maxLines: 4,
              decoration:
              kInput('Your note for the patient...', Icons.edit_outlined),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: () async {
                  if (controller.text.trim().isEmpty) return;
                  await ApiService.reviewScan(
                    scanId,
                    dentistId: Session.userId,
                    dentistName: 'Dr. ${Session.name}',
                    dentistNote: controller.text.trim(),
                  );
                  if (ctx.mounted) Navigator.pop(ctx);
                  if (!mounted) return;
                  setState(() => _future =
                      ApiService.getDentistPatientDetail(widget.patientId));
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                      content: Text('Recommendation sent to patient'),
                      backgroundColor: kPrimaryDark));
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: kPrimary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text('Send'),
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
        title: const Text('Patient Detail', style: kH2),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: kPrimary));
          }
          final p = snap.data ?? {};
          if (p.isEmpty || p['error'] != null) {
            return const Center(
                child: Text('Could not load patient', style: kSub));
          }
          final int pain = p['painScore'] ?? 0;
          return SingleChildScrollView(
            padding: kPagePad,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: kCardDeco,
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: kPrimary.withOpacity(0.12),
                        child: Text(
                            (p['name'] ?? '?').toString().isNotEmpty
                                ? p['name'][0]
                                : '?',
                            style: const TextStyle(
                                color: kPrimary,
                                fontWeight: FontWeight.w700,
                                fontSize: 22)),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(p['name'] ?? '',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: kText,
                                    fontSize: 17)),
                            const SizedBox(height: 4),
                            Text('${p['age']} yrs • ${p['gender']}',
                                style: kSub),
                            Text('Last visit: ${p['lastVisit']}', style: kSub),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _sectionTitle('Oral Image', Icons.image_outlined),
                const SizedBox(height: 10),
                _imageCard(p['imageUrl'] ?? ''),
                const SizedBox(height: 18),
                _sectionTitle('Pain Severity', Icons.healing_rounded),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: kCardDeco,
                  child: Column(
                    children: [
                      Text('$pain',
                          style: TextStyle(
                              fontSize: 40,
                              fontWeight: FontWeight.w800,
                              color: _scoreColor(pain))),
                      Text('out of 100  •  ${_scoreLabel(pain)}', style: kSub),
                      const SizedBox(height: 12),
                      LinearProgressIndicator(
                        value: pain / 100,
                        minHeight: 8,
                        backgroundColor: kBorder,
                        color: _scoreColor(pain),
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _sectionTitle('Oral Scan Analysis', Icons.camera_alt_rounded),
                const SizedBox(height: 10),
                _textCard(p['scan'] ?? 'No scan available.'),
                const SizedBox(height: 18),
                _sectionTitle('Anesthesia Prediction', Icons.vaccines_rounded),
                const SizedBox(height: 10),
                _textCard(p['anesthesia'] ?? 'No prediction available.'),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed: () => _sendRecommendation(),
                    icon: const Icon(Icons.send_rounded),
                    label: const Text('Send Recommendation'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: kPrimary,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _sectionTitle(String t, IconData icon) => Row(
    children: [
      Icon(icon, color: kPrimary, size: 20),
      const SizedBox(width: 8),
      Text(t, style: kH2),
    ],
  );

  Widget _textCard(String text) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: kCardDeco,
    child: Text(text, style: kBody),
  );

  Widget _imageCard(String url) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(kRadius),
      child: Container(
        height: 220,
        width: double.infinity,
        decoration: BoxDecoration(
          color: kCard,
          borderRadius: BorderRadius.circular(kRadius),
          border: Border.all(color: kBorder),
        ),
        child: url.isEmpty
            ? _imagePlaceholder()
            : url.startsWith('data:image')
                ? Image.memory(
                    base64Decode(url.split(',').last),
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _imagePlaceholder(),
                  )
                : Image.network(
                    url,
                    fit: BoxFit.cover,
                    loadingBuilder: (context, child, progress) => progress == null
                        ? child
                        : const Center(
                            child: CircularProgressIndicator(color: kPrimary)),
                    errorBuilder: (_, __, ___) => _imagePlaceholder(),
                  ),
      ),
    );
  }

  Widget _imagePlaceholder() => Column(
    mainAxisAlignment: MainAxisAlignment.center,
    children: const [
      Icon(Icons.image_not_supported_outlined, color: kTextLight, size: 38),
      SizedBox(height: 10),
      Text('No image uploaded yet',
          style: kSub, textAlign: TextAlign.center),
    ],
  );
}