import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';

/// Detecta cambios de red. "Hay red" no garantiza "hay servidor": el SyncManager lo confirma al sincronizar.
class ConnectivityMonitor {
  ConnectivityMonitor([Connectivity? c]) : _c = c ?? Connectivity();
  final Connectivity _c;
  final _ctrl = StreamController<bool>.broadcast();
  StreamSubscription<List<ConnectivityResult>>? _sub;
  bool online = true;

  Stream<bool> get changes => _ctrl.stream;

  Future<void> start() async {
    online = _isOnline(await _c.checkConnectivity());
    _sub = _c.onConnectivityChanged.listen((r) {
      final now = _isOnline(r);
      if (now != online) {
        online = now;
        _ctrl.add(now);
      }
    });
  }

  bool _isOnline(List<ConnectivityResult> r) => r.any((x) => x != ConnectivityResult.none);

  Future<void> dispose() async {
    await _sub?.cancel();
    await _ctrl.close();
  }
}
