import 'package:flutter/material.dart';
import 'login_screen.dart';
import 'chat_service.dart';
import 'api_service.dart';
import 'session.dart';

class PainScreen extends StatefulWidget {
  const PainScreen({super.key});

  @override
  State<PainScreen> createState() => _PainScreenState();
}

class _PainScreenState extends State<PainScreen> {
  final ChatService _chat = ChatService();

  double _intensity = 5;
  String _duration = 'A few hours';
  String _trigger = 'When eating';
  bool _swelling = false;
  bool _sensitivity = false;
  bool _bleeding = false;

  int? _score;
  String? _advice;
  bool _loading = false;

  int _calculate() {
    double s = _intensity * 6;
    if (_duration == 'A few days') s += 12;
    if (_duration == 'A week or more') s += 20;
    if (_trigger == 'Constant') s += 12;
    if (_swelling) s += 8;
    if (_sensitivity) s += 5;
    if (_bleeding) s += 7;
    return s.clamp(0, 100).round();
  }

  Future<void> _submit() async {
    final score = _calculate();
    setState(() {
      _score = score;
      _loading = true;
      _advice = null;
    });
    final advice = await _chat.painAdvice(score, {
      'intensity': _intensity.round().toString(),
      'duration': _duration,
      'trigger': _trigger,
      'swelling': _swelling.toString(),
      'sensitivity': _sensitivity.toString(),
      'bleeding': _bleeding.toString(),
    });

    // Save to backend.
    await ApiService.addPain({
      'patient_id': Session.userId,
      'patient_name': Session.name,
      'intensity': _intensity.round(),
      'duration': _duration,
      'trigger': _trigger,
      'swelling': _swelling,
      'sensitivity': _sensitivity,
      'bleeding': _bleeding,
      'score': score,
      'severity': _scoreLabel(score),
      'advice': advice,
    });

    setState(() {
      _advice = advice;
      _loading = false;
    });
  }

  Color _scoreColor(int s) =>
      s >= 70 ? kDanger : (s >= 40 ? kWarning : kSuccess);
  String _scoreLabel(int s) =>
      s >= 70 ? 'Severe' : (s >= 40 ? 'Moderate' : 'Mild');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: _bar('Pain Severity'),
      body: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: kCardDeco,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Pain intensity: ${_intensity.round()}/10',
                      style: const TextStyle(
                          fontWeight: FontWeight.w700, color: kText)),
                  Slider(
                    value: _intensity,
                    min: 0,
                    max: 10,
                    divisions: 10,
                    activeColor: kPrimary,
                    label: _intensity.round().toString(),
                    onChanged: (v) => setState(() => _intensity = v),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _dropdownCard('How long has it lasted?', _duration,
                ['A few hours', 'A few days', 'A week or more'],
                (v) => setState(() => _duration = v)),
            const SizedBox(height: 16),
            _dropdownCard('When does it hurt?', _trigger,
                ['When eating', 'When cold/hot', 'Constant'],
                (v) => setState(() => _trigger = v)),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              decoration: kCardDeco,
              child: Column(
                children: [
                  _switch('Swelling present', _swelling,
                      (v) => setState(() => _swelling = v)),
                  _switch('Tooth sensitivity', _sensitivity,
                      (v) => setState(() => _sensitivity = v)),
                  _switch('Gum bleeding', _bleeding,
                      (v) => setState(() => _bleeding = v)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              height: 52,
              child: ElevatedButton(
                onPressed: _loading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: kPrimary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
                child: const Text('Calculate Pain Score',
                    style:
                        TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ),
            ),
            if (_score != null) ...[
              const SizedBox(height: 22),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: kCardDeco,
                child: Column(
                  children: [
                    Text('$_score',
                        style: TextStyle(
                            fontSize: 48,
                            fontWeight: FontWeight.w800,
                            color: _scoreColor(_score!))),
                    Text('out of 100  •  ${_scoreLabel(_score!)}', style: kSub),
                    const SizedBox(height: 14),
                    LinearProgressIndicator(
                      value: _score! / 100,
                      minHeight: 8,
                      backgroundColor: kBorder,
                      color: _scoreColor(_score!),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    const SizedBox(height: 18),
                    if (_loading)
                      const Padding(
                        padding: EdgeInsets.all(8),
                        child: CircularProgressIndicator(color: kPrimary),
                      )
                    else if (_advice != null)
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(_advice!, style: kBody),
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

  Widget _dropdownCard(String title, String value, List<String> opts,
      void Function(String) onChanged) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: kCardDeco,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style:
                  const TextStyle(fontWeight: FontWeight.w700, color: kText)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
                color: kBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: kBorder)),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: value,
                isExpanded: true,
                items: opts
                    .map((o) => DropdownMenuItem(value: o, child: Text(o)))
                    .toList(),
                onChanged: (v) => onChanged(v ?? value),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _switch(String label, bool value, void Function(bool) onChanged) {
    return SwitchListTile(
      title: Text(label, style: kBody),
      value: value,
      activeColor: kPrimary,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12),
      onChanged: onChanged,
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
