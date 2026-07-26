import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:mime/mime.dart';

class ChatService {
  static const List<String> _apiKeys = [
    
  ];

  static const String _baseUrl =
      "https://api.groq.com/openai/v1/chat/completions";

  static const String _visionModel =
      "meta-llama/llama-4-scout-17b-16e-instruct";
  static const String _textModel = "llama-3.1-8b-instant";

  // ---------------------------------------------------------------------------
  // 1. ORAL IMAGE ANALYSIS (vision)
  // ---------------------------------------------------------------------------
  Future<String> analyzeOralImage(File imageFile, {String? notes}) async {
    for (int i = 0; i < _apiKeys.length; i++) {
      try {
        return await _sendImageRequest(imageFile, _apiKeys[i], notes);
      } catch (e) {
        print('Vision exception with key ${i + 1}: $e');
        continue;
      }
    }
    return "The analysis service is busy right now. Please try again shortly.";
  }

  // ---------------------------------------------------------------------------
  // 2. ANESTHESIA FAILURE PREDICTION (text reasoning)
  // ---------------------------------------------------------------------------
  Future<String> predictAnesthesiaFailure(Map<String, String> data) async {
    final prompt = '''
Assess the likelihood of LOCAL ANESTHESIA FAILURE for a dental patient based on the details below.
Return your answer in this exact structure:

RISK LEVEL: <Low | Moderate | High>
CONFIDENCE: <percentage>
KEY FACTORS: <short bullet reasons>
RECOMMENDATIONS FOR DENTIST: <preventive measures>

Patient details:
- Age: ${data['age']}
- Gender: ${data['gender']}
- Tooth/Region: ${data['region']}
- Existing infection / abscess: ${data['infection']}
- Inflammation severity: ${data['inflammation']}
- Anxiety level: ${data['anxiety']}
- Previous anesthesia failure: ${data['history']}
- Medical conditions: ${data['medical']}
- Current medications: ${data['medications']}
''';

    for (int i = 0; i < _apiKeys.length; i++) {
      try {
        return await _sendTextRequest(
          prompt,
          _apiKeys[i],
          system:
              "You are a clinical decision-support assistant for dentists, specialized in predicting local anesthesia failure risk. Be concise, evidence-aware, and never replace a clinician's judgement.",
        );
      } catch (e) {
        print('Anesthesia exception with key ${i + 1}: $e');
        continue;
      }
    }
    return "Prediction service is busy. Please try again shortly.";
  }

  // ---------------------------------------------------------------------------
  // 3. PAIN SEVERITY COMMENTARY (text reasoning)
  // ---------------------------------------------------------------------------
  Future<String> painAdvice(int score, Map<String, String> symptoms) async {
    final prompt = '''
A patient has a calculated dental pain severity score of $score/100.
Symptoms reported: ${jsonEncode(symptoms)}

Give a short, reassuring summary covering:
- What this severity likely means
- Whether urgent dental care is advised
- Safe self-care tips until they see a dentist
Keep it under 120 words.''';

    for (int i = 0; i < _apiKeys.length; i++) {
      try {
        return await _sendTextRequest(
          prompt,
          _apiKeys[i],
          system:
              "You are Dental Insight AI, a friendly dental health assistant. Give safe, practical guidance and always recommend professional care when severity is high.",
        );
      } catch (e) {
        print('Pain advice exception with key ${i + 1}: $e');
        continue;
      }
    }
    return "Could not generate advice right now. Please try again shortly.";
  }

  // ---------------------------------------------------------------------------
  // INTERNAL HELPERS
  // ---------------------------------------------------------------------------
  Future<String> _sendTextRequest(String message, String apiKey,
      {required String system}) async {
    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {
        'Authorization': 'Bearer $apiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': _textModel,
        'messages': [
          {'role': 'system', 'content': system},
          {'role': 'user', 'content': message}
        ],
        'temperature': 0.5,
        'max_tokens': 1024,
        'top_p': 0.9,
        'stream': false,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['choices'] != null && data['choices'].isNotEmpty) {
        return data['choices'][0]['message']['content'] ??
            'No response received.';
      }
    } else if (response.statusCode == 429) {
      throw Exception('Rate limit exceeded');
    } else {
      throw Exception('API Error ${response.statusCode}: ${response.body}');
    }
    throw Exception('No valid response received');
  }

  Future<String> _sendImageRequest(
      File imageFile, String apiKey, String? notes) async {
    final fileSize = await imageFile.length();
    if (fileSize > 4 * 1024 * 1024) {
      return "Image is too large. Please use an image smaller than 4MB.";
    }

    final imageBytes = await imageFile.readAsBytes();
    final base64Image = base64Encode(imageBytes);
    final mimeType = lookupMimeType(imageFile.path) ?? 'image/jpeg';

    final analysisPrompt = '''
Analyze this oral / dental image and provide a structured assessment:

CONDITION DETECTED: cavities, tooth decay, plaque, gum infection, discoloration, or other visible issues
SEVERITY: mild / moderate / severe
OBSERVATIONS: what is visible and why it matters
RECOMMENDATIONS: immediate care and whether a dentist visit is needed

${notes != null && notes.isNotEmpty ? 'Patient notes: $notes' : ''}

Important: This is a screening aid, not a diagnosis. Recommend professional consultation for confirmation.''';

    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {
        'Authorization': 'Bearer $apiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': _visionModel,
        'messages': [
          {
            'role': 'system',
            'content':
                '''You are Dental Insight AI, an expert dental vision assistant. You identify visible oral conditions (cavities, decay, plaque, gum infection, discoloration) from images and provide clear, safe, actionable guidance. Always remind the user this is a screening aid and not a replacement for a dentist.'''
          },
          {
            'role': 'user',
            'content': [
              {'type': 'text', 'text': analysisPrompt},
              {
                'type': 'image_url',
                'image_url': {'url': 'data:$mimeType;base64,$base64Image'}
              }
            ]
          }
        ],
        'temperature': 0.6,
        'max_completion_tokens': 1024,
        'top_p': 0.9,
        'stream': false,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['choices'] != null && data['choices'].isNotEmpty) {
        return data['choices'][0]['message']['content'] ??
            'No response received.';
      }
    } else if (response.statusCode == 429) {
      throw Exception('Rate limit exceeded');
    } else {
      throw Exception('API Error ${response.statusCode}: ${response.body}');
    }
    throw Exception('No valid response received');
  }
}
