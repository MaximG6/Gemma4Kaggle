import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/triage_output.dart';
import '../models/app_record.dart';

class VoicebridgeApi {
  VoicebridgeApi({String? baseUrl})
      : _baseUrl = baseUrl ?? 'http://localhost:8000';

  final String _baseUrl;

  Future<bool> healthCheck() async {
    try {
      final res =
          await http.get(Uri.parse('$_baseUrl/health')).timeout(
        const Duration(seconds: 5),
      );
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<TriageOutput> postIntake(Uint8List audioBytes, {String filename = 'recording.webm'}) async {
    final request =
        http.MultipartRequest('POST', Uri.parse('$_baseUrl/intake'));
    request.files.add(
      http.MultipartFile.fromBytes('file', audioBytes, filename: filename),
    );
    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode != 200) {
      throw ApiException(
        'Intake failed: ${response.statusCode} ${response.body}',
      );
    }

    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return TriageOutput.fromJson(json['triage'] as Map<String, dynamic>);
  }

  Future<TriageOutput> postText(String text) async {
    final res = await http
        .post(
          Uri.parse('$_baseUrl/intake/text'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'text': text}),
        )
        .timeout(const Duration(seconds: 60));

    if (res.statusCode != 200) {
      throw ApiException(
        'Text intake failed: ${res.statusCode} ${res.body}',
      );
    }

    final json = jsonDecode(res.body) as Map<String, dynamic>;
    return TriageOutput.fromJson(json['triage'] as Map<String, dynamic>);
  }

  Future<AppRecord?> getRecord(String id) async {
    final res = await http
        .get(Uri.parse('$_baseUrl/records/$id'))
        .timeout(const Duration(seconds: 10));

    if (res.statusCode == 404) {
      return null;
    }
    if (res.statusCode != 200) {
      throw ApiException('Failed to fetch record: ${res.statusCode}');
    }

    // Backend returns triage JSON directly, not wrapped
    final json = jsonDecode(res.body) as Map<String, dynamic>;
    return AppRecord(
      id: id,
      output: TriageOutput.fromJson(json),
      createdAt: DateTime.now(),
    );
  }

  Future<Map<String, dynamic>> postInteractive(
    String text, {
    String? sessionId,
  }) async {
    final body = <String, dynamic>{'text': text};
    if (sessionId != null) body['session_id'] = sessionId;

    final res = await http
        .post(
          Uri.parse('$_baseUrl/intake/interactive'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 90));

    if (res.statusCode != 200) {
      throw ApiException(
        'Interactive intake failed: ${res.statusCode} ${res.body}',
      );
    }

    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<AppRecord>> getRecords({int limit = 50}) async {
    final res = await http
        .get(Uri.parse('$_baseUrl/records?limit=$limit'))
        .timeout(const Duration(seconds: 10));

    if (res.statusCode != 200) {
      throw ApiException('Failed to fetch records: ${res.statusCode}');
    }

    final list = jsonDecode(res.body) as List<dynamic>;
    return list
        .map((e) => AppRecord.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;

  @override
  String toString() => 'ApiException: $message';
}
