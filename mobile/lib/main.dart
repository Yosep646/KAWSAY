import 'dart:io' show Platform;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'app/app.dart';
import 'app/session.dart';
import 'core/api/api_client.dart';
import 'core/data/repository.dart';
import 'core/database/app_database.dart';
import 'core/network/connectivity_monitor.dart';
import 'core/security/token_store.dart';
import 'core/sync/sync_manager.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi; // escritorio: mismo SQLite, misma app
  }
  final db = await AppDatabase.open();
  final repo = Repository(db);
  final tokens = TokenStore();
  final api = ApiClient(tokens);
  final net = ConnectivityMonitor();
  await net.start();
  final sync = SyncManager(repo, api, net);
  final session = Session(repo, api, tokens, sync);
  await session.restore(); // abre SIN Internet si ya hubo un inicio de sesión en este dispositivo
  runApp(MultiProvider(providers: [
    Provider.value(value: repo),
    Provider.value(value: api),
    Provider.value(value: net),
    ChangeNotifierProvider.value(value: sync),
    ChangeNotifierProvider.value(value: session),
  ], child: const KawsayApp()));
}
