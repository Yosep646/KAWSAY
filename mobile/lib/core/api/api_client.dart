import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../security/token_store.dart';

class ApiException implements Exception {
  ApiException(this.status, this.code, this.message);
  final int status;
  final String code;
  final String message;
  bool get isAuth => status == 401;
  @override
  String toString() => message;
}

/// Error de red (sin conexión / servidor inalcanzable): NO es un error del usuario; los eventos se conservan.
class NetworkException implements Exception {
  @override
  String toString() => 'Sin conexión con el servidor';
}

class ApiClient {
  ApiClient(this.tokens, {http.Client? client}) : _http = client ?? http.Client();
  final TokenStore tokens;
  final http.Client _http;
  void Function()? onSessionExpired;
  Future<bool>? _refreshing;

  dynamic _decode(http.Response res) {
    try {
      return res.body.isEmpty ? null : jsonDecode(utf8.decode(res.bodyBytes));
    } on FormatException {
      throw ApiException(res.statusCode, 'invalid_response', 'El servidor devolvió una respuesta inválida');
    }
  }

  Uri _u(String path, [Map<String, String>? q]) => Uri.parse('$kApiBase/api/v1$path').replace(queryParameters: q);

  Future<dynamic> _send(String method, String path,
      {Object? body, Map<String, String>? query, bool auth = true, bool retry = true}) async {
    final headers = <String, String>{'content-type': 'application/json'};
    if (auth) {
      final t = await tokens.access;
      if (t != null) headers['authorization'] = 'Bearer $t';
    }
    http.Response res;
    try {
      final uri = _u(path, query);
      final enc = body == null ? null : jsonEncode(body);
      final f = switch (method) {
        'GET' => _http.get(uri, headers: headers),
        'PUT' => _http.put(uri, headers: headers, body: enc),
        _ => _http.post(uri, headers: headers, body: enc),
      };
      res = await f.timeout(const Duration(seconds: 15));
    } catch (_) {
      throw NetworkException();
    }
    if (res.statusCode == 401 && auth && retry) {
      if (await _refresh()) return _send(method, path, body: body, query: query, retry: false);
      onSessionExpired?.call();
    }
    final data = _decode(res);
    if (res.statusCode >= 400) {
      final d = (data is Map) ? data : const {};
      throw ApiException(res.statusCode, '${d['code'] ?? 'error'}', '${d['message'] ?? 'Error ${res.statusCode}'}');
    }
    return data;
  }

  Future<bool> _refresh() async {
    if (_refreshing != null) return _refreshing!;
    final operation = _refreshOnce();
    _refreshing = operation;
    try {
      return await operation;
    } finally {
      _refreshing = null;
    }
  }

  Future<bool> _refreshOnce() async {
    final rt = await tokens.refresh;
    if (rt == null) return false;
    try {
      final res = await _http
          .post(_u('/auth/refresh'), headers: {'content-type': 'application/json'}, body: jsonEncode({'refresh_token': rt}))
          .timeout(const Duration(seconds: 15));
      if (res.statusCode == 401) return false;
      if (res.statusCode != 200) {
        throw ApiException(res.statusCode, 'refresh_unavailable', 'No se pudo renovar la sesión. Inténtalo más tarde.');
      }
      final d = _decode(res) as Map<String, dynamic>;
      await tokens.save(d['access_token'] as String, d['refresh_token'] as String);
      return true;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw NetworkException();
    }
  }

  Future<Map<String, dynamic>> studentLogin(String code, String pin, String deviceId) async {
    final d = await _send('POST', '/auth/student-login',
        body: {'login_code': code.trim().toUpperCase(), 'pin': pin, 'device_id': deviceId}, auth: false) as Map<String, dynamic>;
    await tokens.save(d['access_token'] as String, d['refresh_token'] as String);
    return d;
  }

  Future<Map<String, dynamic>> pull(int cursor) async =>
      await _send('GET', '/sync/pull', query: {'cursor': '$cursor', 'limit': '20'}) as Map<String, dynamic>;
  Future<List<dynamic>> push(String deviceId, List<Map<String, dynamic>> events) async =>
      ((await _send('POST', '/sync/push', body: {'device_id': deviceId, 'events': events})) as Map)['results'] as List<dynamic>;
  Future<List<dynamic>> subjects() async => await _send('GET', '/learning/subjects') as List<dynamic>;
  Future<List<dynamic>> topics(String subjectId) async => await _send('GET', '/learning/topics', query: {'subject_id': subjectId}) as List<dynamic>;
  Future<List<dynamic>> activities(String topicId) async => await _send('GET', '/learning/activities', query: {'topic_id': topicId}) as List<dynamic>;
  Future<Map<String, dynamic>> startPractice(String variantId) async =>
      await _send('POST', '/learning/start', body: {'variant_id': variantId}) as Map<String, dynamic>;
  Future<Map<String, dynamic>> tutorTurn(String saId, String qid, int step) async =>
      await _send('POST', '/tutor/turn', body: {'student_assignment_id': saId, 'question_id': qid, 'step': step}) as Map<String, dynamic>;
  Future<List<dynamic>> languages() async => await _send('GET', '/languages') as List<dynamic>;
  Future<Map<String, dynamic>> languagePreferences() async =>
      await _send('GET', '/students/me/languages') as Map<String, dynamic>;
  Future<Map<String, dynamic>> setLanguages(String? mother, String? motherVariantId, String? preferred) async =>
      await _send('PUT', '/students/me/languages', body: {
        'mother_language_code': mother,
        'mother_variant_id': motherVariantId,
        'preferred_language_code': preferred,
      }) as Map<String, dynamic>;
  Future<void> logoutRemote() async {
    final rt = await tokens.refresh;
    if (rt != null) {
      try {
        await _http.post(_u('/auth/logout'), headers: {'content-type': 'application/json'}, body: jsonEncode({'refresh_token': rt})).timeout(const Duration(seconds: 15));
      } catch (_) {}
    }
  }
}
