import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kawsay_student/core/data/repository.dart';
import 'package:kawsay_student/core/database/app_database.dart';
import 'package:kawsay_student/features/courses/courses_screen.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

final mathCourse = <String, dynamic>{
  'id': 'room1:math', 'subject_id': 'math', 'name': 'Matemática',
  'classroom_id': 'room1', 'classroom_name': 'Aula multigrado',
  'academic_year': 2026, 'grade_id': 4, 'is_demo': false,
};
final languageCourse = <String, dynamic>{
  'id': 'room1:lang', 'subject_id': 'lang', 'name': 'Comunicación',
  'classroom_id': 'room1', 'classroom_name': 'Aula multigrado',
  'academic_year': 2026, 'grade_id': 4, 'is_demo': false,
};

Map<String, dynamic> publishedTask() => {
  'student_assignment_id': 'sa-math', 'assignment_id': 'a-math', 'variant_id': 'v-math',
  'origin': 'TEACHER', 'grade_id': 4, 'subject': 'Matemática',
  'course_id': 'room1:math', 'competency_id': 'comp-math',
  'competency_name': 'Resuelve problemas de cantidad', 'topic_id': 't-math',
  'topic_title': 'Sumas', 'title': 'Actividad del maestro',
  'instructions': 'Resuelve las preguntas', 'learning_objective': 'Sumar números naturales',
  'seq': 1, 'translation': null,
  'questions': [
    {
      'id': 'q-math', 'position': 1, 'type': 'MULTIPLE_CHOICE', 'prompt': '2 + 3 = ?',
      'options': ['4', '5'], 'correct_answer': {'index': 1},
      'hints': ['Cuenta los sumandos'], 'explanation': '2 + 3 = 5', 'difficulty': 1,
    },
  ],
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  test('catálogo de cursos persiste offline sin actividades y se actualiza', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repository = Repository(db);
    await repository.saveCourses([mathCourse, languageCourse]);
    final courses = await repository.courses();
    expect(courses.map((c) => c.name), containsAll(['Matemática', 'Comunicación']));
    expect(courses.every((c) => c.academicYear == 2026), isTrue);
    expect(await repository.tasks(origin: 'TEACHER'), isEmpty);
    await repository.saveCourses([mathCourse]);
    expect((await repository.courses()).map((c) => c.name), ['Matemática']);
  });

  test('actividad docente aparece bajo el curso correcto y se resuelve offline', () async {
    final db = await AppDatabase.open(path: inMemoryDatabasePath);
    addTearDown(db.close);
    final repo = Repository(db);
    await repo.saveCourses([mathCourse, languageCourse]);
    await repo.upsertTasks([publishedTask()]);
    final tasks = await repo.tasks(origin: 'TEACHER');
    expect(tasks, hasLength(1));
    expect(tasks.single.subject, 'Matemática');
    expect(tasks.single.courseId, mathCourse['id']);
    final q = (await repo.questions(tasks.single.id)).single;
    expect(await repo.recordAttempt(tasks.single.id, q, {'index': 1}, 0, 1500), isTrue);
    expect((await repo.queueCounts())['PENDING'], 1);
    expect((await repo.tasks(origin: 'TEACHER')).single.pending, isFalse);
    expect((await repo.courses()), hasLength(2));
  });

  testWidgets('Mis cursos muestra Matemática y Comunicación sin tareas',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: CoursesContent(
          courses: [LocalCourse.fromJson(mathCourse), LocalCourse.fromJson(languageCourse)],
          downloaded: const <LocalTask>[],
          onOpen: (_) {},
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Matemática'), findsOneWidget);
    expect(find.text('Comunicación'), findsOneWidget);
    expect(find.textContaining('todavía no ha publicado actividades'), findsNWidgets(2));
  });
}
