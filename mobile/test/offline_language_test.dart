import 'package:flutter_test/flutter_test.dart';
import 'package:kawsay_student/core/api/api_client.dart';
import 'package:kawsay_student/core/data/repository.dart';
import 'package:kawsay_student/core/database/app_database.dart';
import 'package:kawsay_student/core/network/connectivity_monitor.dart';
import 'package:kawsay_student/core/security/token_store.dart';
import 'package:kawsay_student/core/sync/sync_manager.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

class LanguageApiFake extends ApiClient {
  LanguageApiFake() : super(TokenStore());
  bool offline = true;
  int confirmed = 0;

  @override
  Future<Map<String, dynamic>> setLanguages(String? mother, String? variant, String? preferred) async {
    if (offline) throw NetworkException();
    confirmed++;
    return {
      'mother_language': mother,
      'mother_variant_id': variant,
      'preferred_language': preferred,
    };
  }

  @override
  Future<Map<String, dynamic>> pull(int cursor) async {
    if (offline) throw NetworkException();
    return {'tasks': [], 'courses': [], 'progress': [], 'cursor': cursor, 'has_more': false};
  }
}

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  test('catálogo real descargado y preferencia quedan disponibles sin red', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repo = Repository(db);
    await repo.saveProfile({'id': 'student1', 'display_name': 'Estudiante', 'role': 'STUDENT'});
    await repo.saveLanguageCatalog([
      {'code': 'es', 'name': 'Español', 'variants': []},
      {'code': 'qu', 'name': 'Quechua', 'variants': []},
    ]);
    await repo.queueLanguagePreferences('qu', null, 'qu');
    expect((await repo.languageCatalog()).length, 2);
    expect((await repo.languagePreferencesLocal())?['preferred_language'], 'qu');
    expect((await repo.pendingLanguagePreferences())?['preferred_language_code'], 'qu');

    final fake = LanguageApiFake()..offline = true;
    final sync = SyncManager(repo, fake, ConnectivityMonitor());
    addTearDown(sync.dispose);
    await sync.syncNow();
    expect(sync.state, SyncState.offline);
    expect(await repo.pendingLanguagePreferences(), isNotNull);
    expect(fake.confirmed, 0);

    fake.offline = false;
    await sync.syncNow();
    expect(sync.state, SyncState.idle);
    expect(fake.confirmed, 1);
    expect(await repo.pendingLanguagePreferences(), isNull);
    expect((await repo.languagePreferencesLocal())?['preferred_language'], 'qu');
    expect((await repo.profile())?['preferred_language'], 'qu');
    await sync.syncNow();
    expect(fake.confirmed, 1);
  });

  test('confirmación de una elección antigua no borra una elección más reciente', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repo = Repository(db);
    await repo.saveProfile({'id': 'student1', 'display_name': 'Estudiante', 'role': 'STUDENT'});
    await repo.queueLanguagePreferences('es', null, 'qu');
    final first = (await repo.pendingLanguagePreferences())!;
    await repo.queueLanguagePreferences('es', null, 'ay');
    await repo.acknowledgeLanguagePreferences(first, {
      'mother_language': 'es', 'preferred_language': 'qu', 'mother_variant_id': null,
    });
    expect((await repo.pendingLanguagePreferences())?['preferred_language_code'], 'ay');
    expect((await repo.languagePreferencesLocal())?['preferred_language'], 'ay');
  });
}
