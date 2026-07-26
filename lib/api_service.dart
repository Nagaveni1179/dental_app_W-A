import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'url.dart';

// Centralized HTTP layer — connected to the Flask backend.
// Set the Railway URL in url.dart. Admin login is handled in the frontend only.
class ApiService {
  static String get _base => Url.baseUrl;

  static Map<String, String> get _json => {'Content-Type': 'application/json'};

  // ── AUTH ──────────────────────────────────────────────
  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    try {
      final res = await http.post(
        Uri.parse("$_base/login"),
        headers: _json,
        body: jsonEncode({'email': email, 'password': password}),
      );
      return jsonDecode(res.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  static Future<Map<String, dynamic>> signup(
    Map<String, dynamic> payload,
  ) async {
    try {
      final res = await http.post(
        Uri.parse("$_base/signup"),
        headers: _json,
        body: jsonEncode(payload),
      );
      return jsonDecode(res.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  static Future<Map<String, dynamic>> resetPassword({
    required String email,
    required String newPassword,
  }) => _post("$_base/reset_password", {
    'email': email,
    'new_password': newPassword,
  });

  // ── SCANS ─────────────────────────────────────────────
  static Future<Map<String, dynamic>> uploadScan({
    required int patientId,
    required String patientName,
    required File image,
    String notes = '',
    String condition = '',
    String severity = 'Mild',
    String analysis = '',
    String summary = '',
  }) async {
    try {
      final req = http.MultipartRequest('POST', Uri.parse("$_base/scans"));
      req.fields['patient_id'] = patientId.toString();
      req.fields['patient_name'] = patientName;
      req.fields['notes'] = notes;
      req.fields['condition'] = condition;
      req.fields['severity'] = severity;
      req.fields['analysis'] = analysis;
      req.fields['summary'] = summary;
      req.fields['findings'] = '[]';
      req.fields['recommendations'] = '[]';
      req.files.add(await http.MultipartFile.fromPath('image', image.path));
      final streamed = await req.send();
      final body = await streamed.stream.bytesToString();
      return jsonDecode(body);
    } catch (e) {
      return {'error': 'Upload failed: $e'};
    }
  }

  static Future<List<dynamic>> getPatientScans(int userId) =>
      _getList("$_base/scans/patient/$userId");

  // Dentist saves a recommendation/review on a scan.
  static Future<Map<String, dynamic>> reviewScan(
    int scanId, {
    required int dentistId,
    required String dentistName,
    required String dentistNote,
  }) => _post("$_base/scans/$scanId/review", {
    'dentist_id': dentistId,
    'dentist_name': dentistName,
    'dentist_note': dentistNote,
  });

  // ── PAIN ──────────────────────────────────────────────
  static Future<Map<String, dynamic>> addPain(Map<String, dynamic> payload) =>
      _post("$_base/pain", payload);

  static Future<List<dynamic>> getPatientPain(int userId) =>
      _getList("$_base/pain/patient/$userId");

  // ── ANESTHESIA ────────────────────────────────────────
  static Future<Map<String, dynamic>> addAnesthesia(
    Map<String, dynamic> payload,
  ) => _post("$_base/anesthesia", payload);

  static Future<List<dynamic>> getPatientAnesthesia(int userId) =>
      _getList("$_base/anesthesia/patient/$userId");

  // ── APPOINTMENTS ──────────────────────────────────────
  static Future<Map<String, dynamic>> addAppointment(
    Map<String, dynamic> payload,
  ) => _post("$_base/appointments", payload);

  static Future<List<dynamic>> getPatientAppointments(int userId) =>
      _getList("$_base/appointments/patient/$userId");

  static Future<List<dynamic>> getAllAppointments() =>
      _getList("$_base/appointments");

  static Future<Map<String, dynamic>> updateAppointmentStatus(
    int id,
    String status,
  ) => _post("$_base/appointments/$id/status", {'status': status});

  // ── CONSULTATIONS ─────────────────────────────────────
  static Future<Map<String, dynamic>> addConsultation(
    Map<String, dynamic> payload,
  ) => _post("$_base/consultations", payload);

  static Future<List<dynamic>> getAllConsultations({String? status}) =>
      _getList(
        status == null
            ? "$_base/consultations"
            : "$_base/consultations?status=$status",
      );

  static Future<Map<String, dynamic>> replyConsultation(
    int id,
    int dentistId,
    String reply,
  ) => _post("$_base/consultations/$id/reply", {
    'dentist_id': dentistId,
    'reply': reply,
  });

  // ── DENTIST ───────────────────────────────────────────
  static Future<List<dynamic>> getDentistPatients() =>
      _getList("$_base/dentist/patients");

  static Future<Map<String, dynamic>> getDentistPatientDetail(int id) =>
      _getMap("$_base/dentist/patient/$id");

  // ── ADMIN ─────────────────────────────────────────────
  static Future<List<dynamic>> getUsers({String? role}) =>
      _getList(role == null ? "$_base/users" : "$_base/users?role=$role");

  static Future<Map<String, dynamic>> deleteUser(int id) async {
    try {
      final res = await http.delete(Uri.parse("$_base/users/$id"));
      return jsonDecode(res.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  static Future<Map<String, dynamic>> getAdminStats() =>
      _getMap("$_base/admin/stats");

  // ── DASHBOARD ─────────────────────────────────────────
  static Future<Map<String, dynamic>> getDashboard(int userId) =>
      _getMap("$_base/dashboard/$userId");

  // ── helpers ───────────────────────────────────────────
  static Future<Map<String, dynamic>> _post(
    String url,
    Map<String, dynamic> payload,
  ) async {
    try {
      final res = await http.post(
        Uri.parse(url),
        headers: _json,
        body: jsonEncode(payload),
      );
      return jsonDecode(res.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  static Future<List<dynamic>> _getList(String url) async {
    try {
      final res = await http.get(Uri.parse(url));
      final data = jsonDecode(res.body);
      return data is List ? data : [];
    } catch (e) {
      return [];
    }
  }

  static Future<Map<String, dynamic>> _getMap(String url) async {
    try {
      final res = await http.get(Uri.parse(url));
      return jsonDecode(res.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }
}
