import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/data/repository.dart';
import 'activity_screen.dart';

class TasksScreen extends StatelessWidget {
  const TasksScreen({super.key, required this.origin, required this.title});
  final String? origin;
  final String title;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(title)),
        body: FutureBuilder<List<LocalTask>>(
          future: context.read<Repository>().tasks(origin: origin),
          builder: (_, snap) {
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            final tasks = snap.data!;
            if (tasks.isEmpty) return const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('Aún no tienes tareas descargadas. Conéctate a Internet una vez para recibirlas.')));
            final bySubject = <String, List<LocalTask>>{};
            for (final t in tasks) { bySubject.putIfAbsent(t.subject ?? 'Otras', () => []).add(t); }
            return ListView(padding: const EdgeInsets.all(16), children: [
              for (final e in bySubject.entries) ...[
                Text('${e.key} · ${e.value.where((t) => t.pending).length} pendientes', style: Theme.of(context).textTheme.titleLarge),
                for (final t in e.value)
                  Card(child: ListTile(
                    title: Text(t.title), subtitle: Text(t.pending ? '${t.closed} de ${t.total} ejercicios' : 'Terminada'),
                    trailing: Icon(t.pending ? Icons.play_arrow : Icons.check_circle),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ActivityScreen(task: t))),
                  )),
              ],
            ]);
          },
        ),
      );
}
