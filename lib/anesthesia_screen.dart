import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'session.dart';
import 'chat_service.dart';
import 'api_service.dart';

class AnesthesiaScreen extends StatefulWidget {
  const AnesthesiaScreen({super.key});

  @override
  State<AnesthesiaScreen> createState() => _AnesthesiaScreenState();
}

class _AnesthesiaScreenState extends State<AnesthesiaScreen> {
  final ChatService _chat = ChatService();
  final _region = TextEditingController();
  final _medical = TextEditingController();
  final _medications = TextEditingController();

  String _infection = 'No';
  String _inflammation = 'Mild';
  String _anxiety = 'Low';
  String _history = 'No';

  String? _result;
  bool _loading = false;

  String _riskFrom(String text) {
    final t = text.toLowerCase();
    if (t.contains('risk level: high') || t.contains('high')) return 'High';
    if (t.contains('moderate')) return 'Moderate';
    return 'Low';
  }

  Future<void> _predict() async {
    if (_region.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter the tooth / region'),
          backgroundColor: kPrimaryDark,
        ),
      );
      return;
    }
    setState(() {
      _loading = true;
      _result = null;
    });
    final response = await ApiService.addAnesthesia({
      'patient_id': Session.userId,
      'patient_name': Session.name,
      'age': Session.age == 0 ? 'N/A' : Session.age.toString(),
      'gender': Session.gender.isEmpty ? 'N/A' : Session.gender,
      'region': _region.text.trim(),
      'infection': _infection,
      'inflammation': _inflammation,
      'anxiety': _anxiety,
      'history': _history,
      'medical_conditions': _medical.text.trim(),
      'medications': _medications.text.trim(),
    });

    final res = response['result'] ?? "No prediction available.";

    // Save to backend.
    await ApiService.addAnesthesia({
      'patient_id': Session.userId,
      'patient_name': Session.name,
      'region': _region.text.trim(),
      'infection': _infection,
      'inflammation': _inflammation,
      'anxiety': _anxiety,
      'history': _history,
      'medical_conditions': _medical.text.trim(),
      'medications': _medications.text.trim(),
      'risk_level': _riskFrom(res),
      'result': res,
    });

    setState(() {
      _result = res;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: _bar('Anesthesia Prediction'),
      body: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: kDanger.withOpacity(0.08),
                borderRadius: BorderRadius.circular(kRadius),
                border: Border.all(color: kDanger.withOpacity(0.25)),
              ),
              child: const Text(
                'Predicts the risk of local anesthesia failure to help the dentist plan ahead.',
                style: kBody,
              ),
            ),
            const SizedBox(height: 18),
            TextField(
              controller: _region,
              decoration: kInput(
                'Tooth / region (e.g. lower left molar)',
                Icons.place_outlined,
              ),
            ),
            const SizedBox(height: 14),
            _picker(
              'Existing infection / abscess',
              _infection,
              ['No', 'Yes'],
              (v) => setState(() => _infection = v),
            ),
            _picker(
              'Inflammation severity',
              _inflammation,
              ['Mild', 'Moderate', 'Severe'],
              (v) => setState(() => _inflammation = v),
            ),
            _picker('Anxiety level', _anxiety, [
              'Low',
              'Medium',
              'High',
            ], (v) => setState(() => _anxiety = v)),
            _picker(
              'Previous anesthesia failure',
              _history,
              ['No', 'Yes'],
              (v) => setState(() => _history = v),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _medical,
              decoration: kInput(
                'Medical conditions (optional)',
                Icons.local_hospital_outlined,
              ),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _medications,
              decoration: kInput(
                'Current medications (optional)',
                Icons.medication_outlined,
              ),
            ),
            const SizedBox(height: 22),
            SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _loading ? null : _predict,
                icon: _loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2.4,
                        ),
                      )
                    : const Icon(Icons.analytics_outlined),
                label: Text(_loading ? 'Predicting...' : 'Predict Risk'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: kPrimary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),
            if (_result != null) ...[
              const SizedBox(height: 22),
              Container(
                padding: const EdgeInsets.all(18),
                decoration: kCardDeco,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.vaccines_rounded, color: kPrimary, size: 20),
                        SizedBox(width: 8),
                        Text('Prediction Result', style: kH2),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(_result!, style: kBody),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _picker(
    String label,
    String value,
    List<String> opts,
    void Function(String) onChanged,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 8, left: 2),
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: kText,
                fontSize: 13.5,
              ),
            ),
          ),
          Row(
            children: opts.map((o) {
              final selected = value == o;
              return Expanded(
                child: GestureDetector(
                  onTap: () => onChanged(o),
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: selected ? kPrimary.withOpacity(0.12) : kCard,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: selected ? kPrimary : kBorder,
                        width: selected ? 1.5 : 1,
                      ),
                    ),
                    child: Text(
                      o,
                      style: TextStyle(
                        fontSize: 12.5,
                        color: selected ? kPrimary : kTextLight,
                        fontWeight: selected
                            ? FontWeight.w700
                            : FontWeight.w500,
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

AppBar _bar(String title) => AppBar(
  backgroundColor: kBg,
  elevation: 0,
  foregroundColor: kText,
  centerTitle: false,
  title: Text(title, style: kH2),
);
