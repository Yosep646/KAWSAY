import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../app/session.dart';
import '../../core/data/repository.dart';
import '../../core/sync/sync_manager.dart';
import '../../shared/widgets/big_button.dart';
import '../assignments/tasks_screen.dart';
import '../learn/learn_screen.dart';
import '../progress/progress_screen.dart';
import '../settings/settings_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final session = context.watch<Session>();
    final sync = context.watch<SyncManager>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('KAWSAY'),
        actions: [IconButton(tooltip: 'Idioma y ajustes', icon: const Icon(Icons.settings), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen())))],
      ),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text('Hola, ${session.name}', style: Theme.of(context).textTheme.titleLarge),
        const Text('¿Qué quieres aprender hoy?'),
        const SizedBox(height: 8),
        _StatusChip(sync: sync),
        const SizedBox(height: 8),
        FutureBuilder<List<LocalTask>>(
          future: context.read<Repository>().tasks(origin: 'TEACHER'),
          builder: (_, snap) {
            final pending = (snap.data ?? []).where((t) => t.pending).length;
            return BigButton(label: 'MIS TAREAS', subtitle: pending == 0 ? 'Nada pendiente' : '$pending pendientes', icon: Icons.assignment,
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TasksScreen(origin: 'TEACHER', title: 'Mis tareas'))));
          },
        ),
        BigButton(label: 'QUIERO APRENDER', icon: Icons.explore, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const LearnScreen()))),
        BigButton(label: 'MI PROGRESO', icon: Icons.stacked_bar_chart, onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProgressScreen()))),
        BigButton(label: 'TUTOR KAWSAY', subtitle: 'Abre una actividad y pide ayuda', icon: Icons.support_agent,
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TasksScreen(origin: null, title: 'Tutor KAWSAY: elige una actividad')))),
      ]),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.sync});
  final SyncManager sync;
  @override
  Widget build(BuildContext context) {
    final text = switch (sync.state) {
      SyncState.offline => 'Sin conexión · tu trabajo se guarda en este dispositivo${sync.pending > 0 ? ' (${sync.pending} por enviar)' : ''}',
      SyncState.syncing => 'Sincronizando…',
      SyncState.sessionExpired => 'Tu sesión expiró. Vuelve a entrar cuando tengas Internet; lo que guardaste no se pierde.',
      SyncState.error => sync.lastError ?? 'Error de sincronización. Tus respuestas están guardadas.',
      SyncState.idle => sync.failed + sync.conflicts > 0
          ? '${sync.failed} respuestas rechazadas · ${sync.conflicts} conflictos por revisar'
          : sync.pending > 0 ? '${sync.pending} respuestas por enviar' : 'Sin pendientes en la cola local',
    };
    return Row(children: [
      Expanded(child: Chip(avatar: Icon(sync.state == SyncState.offline ? Icons.cloud_off : Icons.cloud_done), label: Text(text))),
      TextButton(onPressed: sync.state == SyncState.syncing ? null : sync.syncNow, child: const Text('Sincronizar')),
    ]);
  }
}
