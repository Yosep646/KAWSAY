import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Tokens en almacenamiento seguro del sistema (Keystore/Keychain). Nunca en SQLite ni en texto plano.
class TokenStore {
  TokenStore([FlutterSecureStorage? s]) : _s = s ?? const FlutterSecureStorage();
  final FlutterSecureStorage _s;

  Future<String?> get access => _s.read(key: 'access');
  Future<String?> get refresh => _s.read(key: 'refresh');
  Future<void> save(String access, String refresh) async {
    await _s.write(key: 'access', value: access);
    await _s.write(key: 'refresh', value: refresh);
  }

  Future<void> clear() async {
    await _s.delete(key: 'access');
    await _s.delete(key: 'refresh');
  }
}
