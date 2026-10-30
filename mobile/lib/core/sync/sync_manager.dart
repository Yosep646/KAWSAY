import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import '../api/api_client.dart';
import '../config.dart';
import '../data/repository.dart';
import '../network/connectivity_monitor.dart';

enum SyncState { idle, syncing, offline, sessionExpired, error }

/// Estados de cada evento: PENDING -> SYNCING -> SYNCED | FAILED (rechazo permanente) ; red caída => vuelve a PENDING.
/// El servidor es idempotente por event_id, así que reenviar es siempre seguro.
class SyncManager extends ChangeNotifier {
  SyncManager(this._repo, this._api, this._net);
  final Repository _repo;
  final ApiClient _api;
  final ConnectivityMonitor _net;
  SyncState state = SyncState.idle;
  Map<String, int> counts = {};
  String? lastError;
  Timer? _timer;
  StreamSubscription<bool>? _sub;
  bool _running = false;
  bool _stopped = false;

  Future<void> start() async {
    await stop();
    _stopped = false;
    state = SyncState.idle;
    _api.onSessionExpired = () {
      state = SyncState.sessionExpired;
      notifyListeners();
    };
    _sub = _net.changes.listen((online) {
      if (online) {
        syncNow();
      } else {
        state = SyncState.offline;
        notifyListeners();
      }
    });
    _timer = Timer.periodic(const Duration(seconds: 60), (_) => syncNow());
    await refreshCounts();
    unawaited(syncNow());
  }

  Future<void> refreshCounts() async {
    counts = await _repo.queueCounts();
    notifyListeners();
  }

  int get pending => (counts['PENDING'] ?? 0) + (counts['SYNCING'] ?? 0);
  int get failed => counts['FAILED'] ?? 0;
  int get conflicts => counts['CONFLICT'] ?? 0;

  Future<void> stop() async {
    _stopped = true;
    _timer?.cancel();
    await _sub?.cancel();
    _sub = null;
    while (_running) {
      await Future<void>.delayed(const Duration(milliseconds: 20));
    }
  }

  Future<void> syncNow() async {
    if (_stopped || _running || state == SyncState.sessionExpired) return;
    _running = true;
    state = SyncState.syncing;
    notifyListeners();
    try {
      await _push();
      await _syncLanguagePreferences();
      await _pull();
      lastError = null;
      state = SyncState.idle;
    } on NetworkException {
      state = SyncState.offline; // los eventos siguen PENDING; nada se pierde
    } on ApiException catch (e) {
      lastError = e.message;
      state = e.isAuth ? SyncState.sessionExpired : SyncState.error;
    } catch (_) {
      lastError = 'No se pudo completar la sincronización. Tus respuestas se conservan.';
      state = SyncState.error;
    } finally {
      _running = false;
      await refreshCounts();
    }
  }

  /// La preferencia local se confirma en servidor antes de descargar traducciones.
  /// Si la red cae se conserva la misma operación para reintentar, sin inventar traducciones.
  Future<void> _syncLanguagePreferences() async {
    final pending = await _repo.pendingLanguagePreferences();
    if (pending == null) return;
    final response = await _api.setLanguages(
      pending['mother_language_code'] as String?,
      pending['mother_variant_id'] as String?,
      pending['preferred_language_code'] as String?,
    );
    await _repo.acknowledgeLanguagePreferences(pending, response);
  }

  Future<void> _push() async {
    final db = _repo.db;
    final now = DateTime.now().toUtc().toIso8601String();
    while (true) {
      final rows = await db.query('sync_queue',
          where: "status = 'PENDING' AND next_attempt_at <= ?", whereArgs: [now], orderBy: 'created_at', limit: kSyncBatchSize);
      if (rows.isEmpty) return;
      final ids = rows.map((r) => r['event_id'] as String).toList();
      await db.rawUpdate("UPDATE sync_queue SET status='SYNCING' WHERE event_id IN (${List.filled(ids.length, '?').join(',')})", ids);
      try {
        final events = rows
            .map((r) => {'event_id': r['event_id'], 'type': r['type'], 'payload': jsonDecode(r['payload_json'] as String)})
            .toList();
        final results = await _api.push(await _repo.deviceId(), events);
        final seen = <String>{};
        // Validar el lote completo ANTES de confirmar ningún evento.
        for (final raw in results) {
          if (raw is! Map<String, dynamic> || !ids.contains(raw['event_id']) ||
              !seen.add(raw['event_id'] as String) ||
              !['ACKED', 'DUPLICATE', 'REJECTED'].contains(raw['status'])) {
            throw ApiException(502, 'invalid_response', 'Confirmación de sincronización inválida');
          }
        }
        if (seen.length != ids.length) {
          throw ApiException(502, 'incomplete_response', 'Faltan confirmaciones del servidor');
        }
        await db.transaction((t) async {
          for (final raw in results) {
            final m = raw as Map<String, dynamic>;
            final ok = m['status'] == 'ACKED' || m['status'] == 'DUPLICATE';
            final conflict = ['duplicate_or_conflict', 'event_id_conflict'].contains(m['reason']);
            await t.update('sync_queue', {
              'status': ok ? 'SYNCED' : conflict ? 'CONFLICT' : 'FAILED', 'last_error': m['reason'],
            }, where: 'event_id = ?', whereArgs: [m['event_id']]);
          }
        });
      } catch (_) {
        await _backoff(ids);
        rethrow;
      }
    }
  }

  Future<void> _backoff(List<String> ids) async {
    for (final id in ids) {
      final r = await _repo.db.query('sync_queue', where: 'event_id = ?', whereArgs: [id]);
      if (r.isEmpty) continue;
      final n = (r.first['attempts'] as int) + 1;
      final wait = min(30 * pow(2, n).toInt(), 3600);
      await _repo.db.update('sync_queue', {
        'status': 'PENDING', 'attempts': n,
        'next_attempt_at': DateTime.now().toUtc().add(Duration(seconds: wait)).toIso8601String(),
       }, where: "event_id = ? AND status = 'SYNCING'", whereArgs: [id]);
    }
  }

  Future<void> _pull() async {
    var cursor = await _repo.cursor();
    while (true) {
      final d = await _api.pull(cursor);
      final next = d['cursor'];
      if (next is! int || next < cursor || (d['has_more'] == true && next == cursor)) {
        throw ApiException(502, 'invalid_cursor', 'El servidor devolvió un cursor de sincronización inválido');
      }
      await _repo.upsertTasks(d['tasks'] as List);
      if (d['courses'] is List) {
        await _repo.saveCourses(d['courses'] as List);
      }
      await _repo.saveOfficialProgress(d['progress'] as List);
      cursor = next;
      await _repo.setCursor(cursor);
      if (d['has_more'] != true) return;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _sub?.cancel();
    super.dispose();
  }
}
