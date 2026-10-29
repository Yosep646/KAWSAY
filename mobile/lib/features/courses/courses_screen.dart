import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/data/repository.dart';
import '../../core/sync/sync_manager.dart';
import '../assignments/activity_screen.dart';

/// Cursos del estudiante, derivados de las asignaciones descargadas de su aula.
/// No crea cursos ficticios ni necesita Internet para consultarlos.
class CoursesScreen extends StatefulWidget {
  const CoursesScreen({super.key});

  @override
  State<CoursesScreen> createState() => _CoursesScreenState();
}

class _CoursesScreenState extends State<CoursesScreen> {
  late Future<List<LocalTask>> _future;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _future = context.read<Repository>().tasks(origin: 'TEACHER');
  }

  Future<void> _refresh() async {
    await context.read<SyncManager>().syncNow();
    if (!mounted) return;
    setState(_reload);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mis cursos')),
        body: FutureBuilder<List<LocalTask>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return Center(child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('No se pudieron cargar los cursos guardados. ${snapshot.error}'),
              ));
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final grouped = <String, List<LocalTask>>{};
            for (final task in snapshot.data!) {
              final name = task.subject?.trim();
              grouped.putIfAbsent(
                name == null || name.isEmpty ? 'Área sin identificar' : name,
                () => <LocalTask>[],
              ).add(task);
            }
            return RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                children: [
                  Text('Actividades de tus áreas curriculares',
                      style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 6),
                  const Text('Los cursos y ejercicios descargados se pueden consultar sin Internet.'),
                  const SizedBox(height: 16),
                  if (grouped.isEmpty)
                    const Card(child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Text('Todavía no tienes cursos con actividades descargadas. '
                          'Cuando tu docente publique una actividad y te conectes, aparecerá aquí.'),
                    )),
                  for (final entry in grouped.entries)
                    Card(
                      clipBehavior: Clip.antiAlias,
                      child: ExpansionTile(
                        initiallyExpanded: true,
                        leading: const Icon(Icons.menu_book_outlined),
                        title: Text(entry.key),
                        subtitle: Text(
                          '${entry.value.length} actividades · '
                          '${entry.value.where((task) => task.pending).length} pendientes',
                        ),
                        children: [
                          for (final task in entry.value)
                            ListTile(
                              title: Text(task.title),
                              subtitle: Text(
                                '${task.competencyName ?? 'Competencia curricular'} · '
                                '${task.closed} de ${task.total} ejercicios resueltos',
                              ),
                              trailing: Icon(
                                task.pending ? Icons.play_circle_outline : Icons.check_circle_outline,
                              ),
                              onTap: () async {
                                await Navigator.push(context, MaterialPageRoute(
                                  builder: (_) => ActivityScreen(task: task),
                                ));
                                if (mounted) setState(_reload);
                              },
                            ),
                        ],
                      ),
                    ),
                ],
              ),
            );
          },
        ),
      );
}
