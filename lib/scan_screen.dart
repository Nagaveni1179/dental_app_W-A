import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'login_screen.dart';
import 'chat_service.dart';
import 'api_service.dart';
import 'session.dart';
import 'package:flutter/foundation.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final ChatService _chat = ChatService();
  final ImagePicker _picker = ImagePicker();
  final _notes = TextEditingController();

  XFile? _image;
  String? _result;
  bool _loading = false;
  bool _saving = false;

  Future<void> _pick(ImageSource source) async {
    final picked = await _picker.pickImage(source: source, imageQuality: 80);
    if (picked != null) {
      setState(() {
        _image = picked;
        _result = null;
      });
    }
  }
void _sheet() {
  showModalBottomSheet(
    context: context,
    builder: (_) => SafeArea(
      child: Wrap(
        children: [
          ListTile(
            leading: const Icon(Icons.photo_camera),
            title: const Text('Camera'),
            onTap: () {
              Navigator.pop(context);
              _pick(ImageSource.camera);
            },
          ),
          ListTile(
            leading: const Icon(Icons.photo_library),
            title: const Text('Gallery'),
            onTap: () {
              Navigator.pop(context);
              _pick(ImageSource.gallery);
            },
          ),
        ],
      ),
    ),
  );
}
  String _severityFrom(String text) {
    final t = text.toLowerCase();
    if (t.contains('severe')) return 'Severe';
    if (t.contains('moderate')) return 'Moderate';
    return 'Mild';
  }

  Future<void> _analyze() async {
    if (_image == null) return;

    setState(() {
      _loading = true;
      _saving = true;
    });

    print('[ScanScreen] Sending image to backend...');

    final save = await ApiService.uploadScan(
      patientId: Session.userId,
      patientName: Session.name,
      image: _image!,
      notes: _notes.text.trim(),
    );

  print('[ScanScreen] Full response: $save');
    if (save.containsKey('error')) {
      print('[ScanScreen] Backend error: ${save['error']}');
    }

    final ok = save['scan'] != null;
    // Show analysis if available, otherwise show the error message
    final res = save['analysis'] ?? save['error'] ?? "No analysis available.";

    setState(() {
      _result = res;
      _loading = false;
      _saving = false;
    });

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(ok
            ? 'Saved to your records'
            : 'Error: ${save['error'] ?? 'Upload failed'}'),
        backgroundColor: ok ? kPrimaryDark : kDanger,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: _bar('Oral Scan'),
      body: SingleChildScrollView(
        padding: kPagePad,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            GestureDetector(
              onTap: _sheet,
              child: Container(
                height: 230,
                decoration: BoxDecoration(
                  color: kCard,
                  borderRadius: BorderRadius.circular(kRadius),
                  border: Border.all(color: kBorder, width: 1.4),
                ),
                child: _image == null
                    ? Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            height: 64,
                            width: 64,
                            decoration: BoxDecoration(
                              color: kPrimary.withOpacity(0.12),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.add_a_photo_outlined,
                              color: kPrimary,
                              size: 30,
                            ),
                          ),
                          const SizedBox(height: 14),
                          const Text('Tap to add an oral image', style: kBody),
                          const SizedBox(height: 4),
                          const Text('Camera or gallery', style: kSub),
                        ],
                      )
                    : ClipRRect(
                        borderRadius: BorderRadius.circular(kRadius),
                       child: kIsWeb
    ? Image.network(
        _image!.path,
        fit: BoxFit.cover,
        width: double.infinity,
      )
    : Image.file(
        File(_image!.path),
        fit: BoxFit.cover,
        width: double.infinity,
      ), 
                      ),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _notes,
              maxLines: 2,
              decoration: kInput(
                'Optional notes (e.g. pain location)',
                Icons.edit_note_outlined,
              ),
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: (_image == null || _loading) ? null : _analyze,
                icon: _loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2.4,
                        ),
                      )
                    : const Icon(Icons.auto_awesome),
                label: Text(_loading ? 'Analyzing...' : 'Analyze with AI'),
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
            if (_saving)
              const Padding(
                padding: EdgeInsets.only(top: 14),
                child: Text(
                  'Saving to your records...',
                  style: kSub,
                  textAlign: TextAlign.center,
                ),
              ),
            if (_result != null) ...[
              const SizedBox(height: 22),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: kCardDeco,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(
                          Icons.health_and_safety_outlined,
                          color: kPrimary,
                          size: 20,
                        ),
                        SizedBox(width: 8),
                        Text('AI Assessment', style: kH2),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(_result!, style: kBody),
                    const SizedBox(height: 12),
                    const Text(
                      'This is a screening aid, not a diagnosis. Please consult a dentist.',
                      style: TextStyle(
                        fontSize: 12,
                        color: kTextLight,
                        fontStyle: FontStyle.italic,
                      ),
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
}

AppBar _bar(String title) => AppBar(
  backgroundColor: kBg,
  elevation: 0,
  foregroundColor: kText,
  centerTitle: false,
  title: Text(title, style: kH2),
);
