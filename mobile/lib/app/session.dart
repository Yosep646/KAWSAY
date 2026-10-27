import 'package:flutter/foundation.dart';
import '../core/api/api_client.dart';
import '../core/data/repository.dart';
import '../core/security/token_store.dart';
import '../core/sync/sync_manager.dart';

/// Sesión del estudiante. Una sesión previamente habilitada permite abrir la app SIN Internet:
/// el perfil mínimo está en SQLite y los tokens en almacenamiento seguro del sistema.
class Session extends ChangeNotifier {
  Session(this._repo, this._api, this._tokens, this._sync);
  final Repository _repo;
  final ApiClient _api;
  final TokenStore _tokens;
  final SyncManager _sync;
  Map<String, Object?>? profile;

  bool get signedIn => profile != null;
  String get name => (profile?['display_name'] as String?) ?? '';

  Future<void> restore() async {
    profile = await _tokens.refresh == null ? null : await _repo.profile();
    if (signedIn) await _sync.start();
    notifyListeners();
  }

  /// Requiere Internet SOLO la primera vez (o tras un cierre de sesión).
  Future<void> login(String code, String pin) async {
    final d = await _api.studentLogin(code, pin, await _repo.deviceId());
    final user = d['user'] as Map<String, dynamic>;
    if (user['role'] != 'STUDENT') throw ApiException(403, 'forbidden', 'Esta app es para estudiantes');
    try {
      await _repo.saveProfile(user);
    } on StateError catch (e) {
      await _tokens.clear();
      throw ApiException(409, 'device_bound', e.message.toString());
    }
    profile = await _repo.profile();
    await _sync.start();
    notifyListeners();
  }

  /// No se borran intentos locales pendientes: se avisa a la UI si quedan eventos sin enviar.
  Future<bool> canLogoutSafely() async {
    final counts = await _repo.queueCounts();
    return ['PENDING', 'SYNCING', 'FAILED', 'CONFLICT'].every((s) => (counts[s] ?? 0) == 0);
  }

  Future<void> logout() async {
    await _sync.stop();
    if (!await canLogoutSafely()) {
      await _sync.start();
      throw ApiException(409, 'pending_work', 'Hay respuestas pendientes o conflictos por revisar.');
    }
    await _api.logoutRemote();
    await _tokens.clear();
    await _repo.clearProfile();
    profile = null;
    notifyListeners();
  }
}
