import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/data/repository.dart';
import '../../core/sync/sync_manager.dart';
import '../assignments/activity_screen.dart';

class _CourseData {
  const _CourseData(this.catalog, this.tasks);
  final List<LocalCourse> catalog;
  final List<LocalTask> tasks;
}

/// Cursos reales de la planificación ACTIVE. La consulta usa SQLite local
/// incluso en modo avión; el docente sigue siendo quien publica las tareas.
class CoursesScreen extends StatefulWidget {
  const CoursesScreen({super.key});

  @override
  State<CoursesScreen> createState() => _CoursesScreenState();
}

class _CoursesScreenState extends State<CoursesScreen> {
  late Future<_CourseData> _future;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<_CourseData> _load() async {
    final repo = context.read<Repository>();
    final catalog = await repo.courses();
    final tasks = await repo.tasks(origin: 'TEACHER');
    return _CourseData(catalog, tasks);
  }

  void _reload() => _future = _load();

  Future<void> _refresh() async {
    await context.read<SyncManager>().syncNow();
    if (mounted) setState(_reload);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mis cursos')),
        body: FutureBuilder<_CourseData>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return Center(child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('No se pudieron cargar tus cursos guardados. ${snapshot.error}'),
              ));
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final courses = snapshot.data!.catalog;
            final downloaded = snapshot.data!.tasks;
            final byName = <String, List<LocalTask>>{};
            for (final task in downloaded) {
              final name = task.subject?.trim().toLowerCase() ?? '';
              byName.putIfAbsent(name, () => <LocalTask>[]).add(task);
            }
            final knownNames = courses.map((c) => c.name.trim().toLowerCase()).toSet();
            final archived = downloaded.where((t) =>
                !knownNames.contains(t.subject?.trim().toLowerCase() ?? '')).toList();

            return RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                children: [
                  Text('Mis áreas curriculares', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 6),
                  const Text('Tus cursos y actividades descargadas se conservan sin Internet. '
                      'Desliza hacia abajo para sincronizar cuando tengas conexión.'),
                  const SizedBox(height: 16),
                  if (courses.isEmpty && archived.isEmpty)
                    const Card(child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Text('Aún no hay cursos sincronizados. '
                          'Conéctate al menos una vez para descargar la planificación de tu aula.'),
                    )),
                  for (final course in courses)
                    _CourseCard(
                      name: course.name,
                      classroom: course.classroomName,
                      year: course.academicYear,
                      isDemo: course.isDemo,
                      tasks: byName[course.name.trim().toLowerCase()] ?? const [],
                      onReturned: () => setState(_reload),
                    ),
                  if (archived.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text('Actividades descargadas anteriormente',
                        style: Theme.of(context).textTheme.titleMedium),
                    _CourseCard(
                      name: 'Otras actividades',
                      classroom: 'Guardadas en este dispositivo',
                      tasks: archived,
                      onReturned: () => setState(_reload),
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      );
}

class _CourseCard extends StatelessWidget {
  const _CourseCard({
    required this.name,
    required this.classroom,
    required this.tasks,
    required this.onReturned,
    this.year,
    this.isDemo = false,
  });
  final String name;
  final String classroom;
  final int? year;
  final bool isDemo;
  final List<LocalTask> tasks;
  final VoidCallback onReturned;

  @override
  Widget build(BuildContext context) => Card(
        clipBehavior: Clip.antiAlias,
        child: ExpansionTile(
          initiallyExpanded: true,
          leading: const Icon(Icons.menu_book_outlined),
          title: Text(name),
          subtitle: Text(
            '$classroom${year == null ? '' : ' · $year'} · '
            '${tasks.where((t) => t.pending).length} pendientes'
            '${isDemo ? ' · Plan de prueba' : ''}',
          ),
          children: tasks.isEmpty
              ? [const ListTile(title: Text('Tu docente todavía no ha publicado actividades para este curso.'))]
              : [
                  for (final task in tasks)
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
                        onReturned();
                      },
                    ),
                ],
        ),
      );
}
