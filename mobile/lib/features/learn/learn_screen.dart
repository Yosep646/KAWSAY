import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api/api_client.dart';
import '../../core/data/repository.dart';
import '../assignments/activity_screen.dart';
import '../assignments/tasks_screen.dart';

/// QUIERO APRENDER: materia → tema → actividad (solo contenido publicado para TU grado).
/// Sin Internet muestra lo ya descargado; el catálogo nuevo requiere conexión.
class LearnScreen extends StatefulWidget {
  const LearnScreen({super.key});
  @override
  State<LearnScreen> createState() => _LearnScreenState();
}

class _LearnScreenState extends State<LearnScreen> {
  List<dynamic>? _subjects;
  String? _error;

  @override
  void initState() {
    super.initState();
    context.read<ApiClient>().subjects().then((s) => setState(() => _subjects = s)).catchError((Object e) {
      setState(() => _error = e is NetworkException ? 'Sin conexión. Puedes practicar lo que ya descargaste.' : '$e');
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Quiero aprender')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          if (_error != null) Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(_error!))),
          OutlinedButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TasksScreen(origin: 'SELF', title: 'Mi práctica descargada'))), child: const Text('Mi práctica descargada')),
          const SizedBox(height: 12),
          if (_subjects == null && _error == null) const Center(child: CircularProgressIndicator()),
          if (_subjects != null && _subjects!.isEmpty) const Text('Todavía no hay actividades publicadas para tu grado.'),
          for (final s in (_subjects ?? [])) Card(child: ListTile(title: Text('${s['name']}'), subtitle: Text('${s['activities']} actividades'), onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => _Topics(subject: s as Map<String, dynamic>))))),
        ]),
      );
}

class _Topics extends StatelessWidget {
  const _Topics({required this.subject});
  final Map<String, dynamic> subject;
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('${subject['name']}')),
        body: FutureBuilder<List<dynamic>>(
          future: context.read<ApiClient>().topics(subject['id'] as String),
          builder: (_, snap) {
            if (snap.hasError) return const Center(child: Text('Sin conexión.'));
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            return ListView(padding: const EdgeInsets.all(16), children: [
              for (final t in snap.data!) Card(child: ListTile(
                title: Text('${t['title']}'), subtitle: Text('${t['competency']}${t['my_progress_percent'] == null ? '' : ' · tu avance: ${t['my_progress_percent']} %'}'),
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => _Activities(topic: t as Map<String, dynamic>))))),
            ]);
          },
        ),
      );
}

class _Activities extends StatelessWidget {
  const _Activities({required this.topic});
  final Map<String, dynamic> topic;

  Future<void> _start(BuildContext context, String variantId) async {
    final repo = context.read<Repository>();
    final nav = Navigator.of(context);
    try {
      final task = await context.read<ApiClient>().startPractice(variantId); // descarga a SQLite
      await repo.upsertTasks([task]);
      final local = (await repo.tasks()).firstWhere((t) => t.id == task['student_assignment_id']);
      nav.push(MaterialPageRoute(builder: (_) => ActivityScreen(task: local)));
    } on NetworkException {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Necesitas Internet para descargar esta actividad.')));
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('${topic['title']}')),
        body: FutureBuilder<List<dynamic>>(
          future: context.read<ApiClient>().activities(topic['id'] as String),
          builder: (_, snap) {
            if (snap.hasError) return const Center(child: Text('Sin conexión.'));
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            return ListView(padding: const EdgeInsets.all(16), children: [
              Text('${topic['objective']}'),
              for (final a in snap.data!) Card(child: ListTile(title: Text('${a['title']}'), subtitle: Text('${a['questions']} ejercicios'), trailing: const Icon(Icons.download), onTap: () => _start(context, a['variant_id'] as String))),
            ]);
          },
        ),
      );
}
