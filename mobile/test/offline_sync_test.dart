// Contrato offline/sync de la app con SQLite en memoria y un API falso.
// ESTADO: escrito, NO ejecutado. Ejecutar: flutter test
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:kawsay_student/core/api/api_client.dart';
import 'package:kawsay_student/core/data/repository.dart';
import 'package:kawsay_student/core/database/app_database.dart';
import 'package:kawsay_student/core/network/connectivity_monitor.dart';
import 'package:kawsay_student/core/security/token_store.dart';
import 'package:kawsay_student/core/sync/sync_manager.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

class FakeApi extends ApiClient {
  FakeApi() : super(TokenStore());
  bool offline = false;
  final seen = <String>{};
  int accepted = 0;
  List<dynamic>? responseOverride;
  @override
  Future<List<dynamic>> push(String deviceId, List<Map<String, dynamic>> events) async {
    if (offline) throw NetworkException();
    if (responseOverride != null) return responseOverride!;
    return [
      for (final e in events)
        () {
          final id = e['event_id'] as String;
          final dup = !seen.add(id);
          if (!dup) accepted++;
          return {'event_id': id, 'status': dup ? 'DUPLICATE' : 'ACKED'};
        }()
    ];
  }

  @override
  Future<Map<String, dynamic>> pull(int cursor) async {
    if (offline) throw NetworkException();
    return {'tasks': [], 'progress': [], 'cursor': cursor, 'has_more': false};
  }
}

Map<String, dynamic> task() => {
      'student_assignment_id': 'sa1', 'assignment_id': 'a1', 'variant_id': 'v1', 'origin': 'TEACHER', 'grade_id': 1,
      'subject': 'Matemática', 'competency_id': 'c1', 'competency_name': 'Cantidad', 'topic_id': 't1', 'topic_title': 'Comparar',
      'title': 'Tarea', 'instructions': 'Resuelve', 'learning_objective': 'obj', 'seq': 1, 'translation': null,
      'questions': [{'id': 'q1', 'position': 1, 'type': 'MULTIPLE_CHOICE', 'prompt': '¿?', 'options': ['a', 'b'], 'correct_answer': {'index': 1}, 'hints': ['p1'], 'explanation': 'e', 'difficulty': 1}],
    };

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  test('offline: intento y evento se guardan juntos, persisten y se envían sin duplicar', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repo = Repository(db);
    await repo.upsertTasks([task()]);
    final q = (await repo.questions('sa1')).first;

    expect(await repo.recordAttempt('sa1', q, {'index': 1}, 0, 1500), isTrue); // sin red
    expect((await repo.queueCounts())['PENDING'], 1);
    expect(await repo.attemptsCount('sa1', 'q1'), 1);

    final api = FakeApi()..offline = true;
    final sync = SyncManager(repo, api, ConnectivityMonitor());
    addTearDown(sync.dispose);
    await sync.syncNow(); // sin red: nada se pierde
    expect((await repo.queueCounts())['PENDING'], 1);

    api.offline = false;
    await db.db.update('sync_queue', {'next_attempt_at': '2000-01-01T00:00:00Z'}); // vence el backoff
    await sync.syncNow();
    expect((await repo.queueCounts())['SYNCED'], 1);
    await sync.syncNow(); // reenviar no duplica
    expect(api.accepted, 1);
  });

  test('un evento SYNCING tras un cierre brusco vuelve a PENDING al abrir la base', () async {
    final folder = await Directory.systemTemp.createTemp('kawsay-offline-test-');
    addTearDown(() => folder.delete(recursive: true));
    final path = '${folder.path}/resume.db';
    final first = await AppDatabase.open(path: path);
    await first.db.insert('sync_queue', {'event_id': 'e1', 'type': 'attempt.created', 'payload_json': '{}', 'status': 'SYNCING', 'attempts': 0, 'created_at': 'x', 'next_attempt_at': 'x'});
    await first.close();
    final second = await AppDatabase.open(path: path);
    addTearDown(second.close);
    expect((await Repository(second).queueCounts())['PENDING'], 1);
  });

  test('confirmación incompleta conserva el evento para reintento', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repo = Repository(db);
    await repo.upsertTasks([task()]);
    await repo.recordAttempt('sa1', (await repo.questions('sa1')).first, {'index': 1}, 0, 100);
    final sync = SyncManager(repo, FakeApi()..responseOverride = [], ConnectivityMonitor());
    addTearDown(sync.dispose);
    await sync.syncNow();
    expect((await repo.queueCounts())['PENDING'], 1);
    expect((await repo.queueCounts())['SYNCED'], isNull);
    expect(sync.state, SyncState.error);
  });

  test('una cuenta distinta no puede reutilizar los datos descargados', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repo = Repository(db);
    await repo.saveProfile({'id': 'student1', 'display_name': 'Uno', 'role': 'STUDENT'});
    await repo.clearProfile();
    expect(await repo.profile(), isNull);
    await expectLater(repo.saveProfile({'id': 'student2', 'display_name': 'Dos', 'role': 'STUDENT'}), throwsStateError);
    await repo.saveProfile({'id': 'student1', 'display_name': 'Uno', 'role': 'STUDENT'});
    expect((await repo.profile())?['id'], 'student1');
  });
}
