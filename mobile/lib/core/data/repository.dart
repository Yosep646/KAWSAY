import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';
import '../database/app_database.dart';
import '../offline/rules.dart' as rules;

/// Curso de la planificación ACTIVE del aula y grado del estudiante.
class LocalCourse {
  const LocalCourse({
    required this.id,
    required this.name,
    required this.classroomName,
    required this.academicYear,
    required this.gradeId,
    required this.isDemo,
  });
  final String id;
  final String name;
  final String classroomName;
  final int academicYear;
  final int gradeId;
  final bool isDemo;

  factory LocalCourse.fromJson(Map<String, dynamic> data) => LocalCourse(
    id: data['id'] as String,
    name: data['name'] as String,
    classroomName: data['classroom_name'] as String,
    academicYear: data['academic_year'] as int,
    gradeId: data['grade_id'] as int,
    isDemo: data['is_demo'] == true,
  );
}

class LocalQuestion {
  LocalQuestion(this.id, this.position, this.type, this.prompt, this.options, this.correct, this.hints, this.explanation);
  final String id;
  final int position;
  final String type;
  final String prompt;
  final List<String>? options;
  final Map<String, dynamic> correct;
  final List<String> hints;
  final String? explanation;
}

class LocalTask {
  LocalTask(this.id, this.origin, this.subject, this.courseId, this.competencyId, this.competencyName, this.title, this.instructions,
      this.objective, this.total, this.closed);
  final String id;
  final String origin;
  final String? subject;
  final String? courseId;
  final String competencyId;
  final String? competencyName;
  final String title;
  final String instructions;
  final String objective;
  final int total;
  final int closed;
  bool get pending => closed < total;
}

/// Único punto de acceso a SQLite: la UI nunca toca la base directamente.
class Repository {
  Repository(this._d);
  final AppDatabase _d;
  Database get db => _d.db;
  static const _uuid = Uuid();

  Future<String> deviceId() async {
    final r = await db.query('meta', where: "key = 'device_id'");
    if (r.isNotEmpty) return r.first['value'] as String;
    final id = _uuid.v4();
    await db.insert('meta', {'key': 'device_id', 'value': id});
    return id;
  }

  Future<int> cursor() async {
    final r = await db.query('meta', where: "key = 'cursor'");
    return r.isEmpty ? 0 : int.parse(r.first['value'] as String);
  }

  Future<void> setCursor(int c) => db.insert('meta', {'key': 'cursor', 'value': '$c'}, conflictAlgorithm: ConflictAlgorithm.replace);

  /// Una base local pertenece a un único estudiante. No mezcla datos al cambiar cuenta.
  Future<void> saveProfile(Map<String, dynamic> u) async {
    await db.transaction((t) async {
      final owner = await t.query('meta', where: "key = 'owner_id'");
      final oldProfile = await t.query('profile', limit: 1);
      final ownerId = owner.isNotEmpty ? owner.first['value'] : oldProfile.isNotEmpty ? oldProfile.first['id'] : null;
      if (ownerId != null && ownerId != u['id']) {
        throw StateError('Este dispositivo está vinculado a otro estudiante. Solicita al docente su reprovisionamiento.');
      }
      await t.insert('meta', {'key': 'owner_id', 'value': u['id']}, conflictAlgorithm: ConflictAlgorithm.replace);
      await t.insert('profile', {
        'id': u['id'], 'display_name': u['display_name'], 'role': u['role'],
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    });
  }

  Future<void> clearProfile() async {
    await db.transaction((t) async {
      final rows = await t.query('profile', limit: 1);
      if (rows.isNotEmpty) {
        await t.insert('meta', {'key': 'owner_id', 'value': rows.first['id']}, conflictAlgorithm: ConflictAlgorithm.replace);
      }
      await t.delete('profile');
    });
  }

  Future<Map<String, Object?>?> profile() async {
    final r = await db.query('profile', limit: 1);
    return r.isEmpty ? null : r.first;
  }

  Future<void> saveLanguages(String? mother, String? preferred) =>
      db.update('profile', {'mother_language': mother, 'preferred_language': preferred});

  /// Catálogo descargado una sola vez; no se inventan variantes lingüísticas.
  Future<void> saveLanguageCatalog(List<dynamic> languages) async {
    await db.insert('meta', {'key': 'language_catalog', 'value': jsonEncode(languages)},
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<List<dynamic>> languageCatalog() async {
    final rows = await db.query('meta', where: "key = 'language_catalog'");
    return rows.isEmpty ? [] : jsonDecode(rows.first['value'] as String) as List<dynamic>;
  }

  Future<void> storeLanguagePreferences(Map<String, dynamic> values) async {
    await db.insert('meta', {'key': 'language_preferences', 'value': jsonEncode(values)},
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<Map<String, dynamic>?> languagePreferencesLocal() async {
    final pending = await pendingLanguagePreferences();
    if (pending != null) {
      return {'mother_language': pending['mother_language_code'],
              'mother_variant_id': pending['mother_variant_id'],
              'preferred_language': pending['preferred_language_code']};
    }
    final rows = await db.query('meta', where: "key = 'language_preferences'");
    return rows.isEmpty ? null :
        (jsonDecode(rows.first['value'] as String) as Map).cast<String, dynamic>();
  }

  /// Un único cambio pendiente por estudiante; se almacena ANTES de intentar subirlo.
  /// No expone nuevas identidades: se sincroniza con el token del alumno actual.
  Future<void> queueLanguagePreferences(String? mother, String? variant, String? preferred) async {
    final body = <String, dynamic>{
      'mother_language_code': mother,
      'mother_variant_id': variant,
      'preferred_language_code': preferred,
    };
    await db.transaction((transaction) async {
      await transaction.insert('meta', {'key': 'pending_language_preferences', 'value': jsonEncode(body)},
          conflictAlgorithm: ConflictAlgorithm.replace);
      await transaction.update('profile', {'mother_language': mother, 'preferred_language': preferred});
    });
  }

  Future<Map<String, dynamic>?> pendingLanguagePreferences() async {
    final rows = await db.query('meta', where: "key = 'pending_language_preferences'");
    return rows.isEmpty ? null :
        (jsonDecode(rows.first['value'] as String) as Map).cast<String, dynamic>();
  }

  Future<void> acknowledgeLanguagePreferences(Map<String, dynamic> submitted,
      Map<String, dynamic> serverResponse) async {
    await db.transaction((t) async {
      final rows = await t.query('meta', where: "key = 'pending_language_preferences'");
      // Si el alumno eligió otro idioma mientras llegaba el ACK, no borrar el cambio más reciente.
      if (rows.isEmpty || rows.first['value'] != jsonEncode(submitted)) return;
      await t.delete('meta', where: "key = 'pending_language_preferences'");
      await t.insert('meta', {'key': 'language_preferences', 'value': jsonEncode(serverResponse)},
          conflictAlgorithm: ConflictAlgorithm.replace);
      await t.update('profile', {'mother_language': serverResponse['mother_language'],
                                'preferred_language': serverResponse['preferred_language']});
    });
  }

  /// Reemplaza el catálogo local con la foto de la planificación ACTIVE del servidor.
  /// Guardado en SQLite: se conserva cuando el dispositivo queda sin conexión.
  Future<void> saveCourses(List<dynamic> courses) async {
    final clean = courses.map((item) =>
        LocalCourse.fromJson((item as Map).cast<String, dynamic>())).toList();
    await db.insert('meta', {
      'key': 'courses_catalog',
      'value': jsonEncode(courses),
    }, conflictAlgorithm: ConflictAlgorithm.replace);
    assert(clean.length == courses.length);
  }

  Future<List<LocalCourse>> courses() async {
    final rows = await db.query('meta', where: "key = 'courses_catalog'");
    if (rows.isEmpty) return [];
    final raw = jsonDecode(rows.first['value'] as String) as List;
    return raw.map((item) =>
        LocalCourse.fromJson((item as Map).cast<String, dynamic>())).toList();
  }

  /// Guarda/actualiza tareas descargadas (pull o "Quiero aprender") en una transacción.
  Future<void> upsertTasks(List<dynamic> tasks) async {
    await db.transaction((t) async {
      for (final raw in tasks) {
        final k = raw as Map<String, dynamic>;
        final tr = k['translation'] as Map<String, dynamic>?;
        final sa = k['student_assignment_id'] as String;
        await t.insert(
            'tasks',
            {
              'student_assignment_id': sa, 'assignment_id': k['assignment_id'], 'variant_id': k['variant_id'],
              'origin': k['origin'] ?? 'TEACHER', 'grade_id': k['grade_id'], 'subject': k['subject'],
              'course_id': k['course_id'],
              'competency_id': k['competency_id'], 'competency_name': k['competency_name'], 'topic_id': k['topic_id'],
              'topic_title': k['topic_title'],
              // solo traducciones VERIFICADAS llegan del servidor; si no hay, se muestra el idioma base
              'title': tr?['title'] ?? k['title'], 'instructions': tr?['instructions'] ?? k['instructions'],
              'learning_objective': k['learning_objective'], 'translation_json': tr == null ? null : jsonEncode(tr),
              'seq': k['seq'], 'pulled_at': DateTime.now().toUtc().toIso8601String(),
            },
            conflictAlgorithm: ConflictAlgorithm.replace);
        final prompts = (tr?['question_prompts'] as Map?)?.cast<String, dynamic>() ?? const {};
        for (final q in (k['questions'] as List)) {
          final m = q as Map<String, dynamic>;
          await t.insert(
              'questions',
              {
                'id': m['id'], 'student_assignment_id': sa, 'position': m['position'], 'type': m['type'],
                'prompt': prompts[m['id']] ?? m['prompt'], 'options_json': m['options'] == null ? null : jsonEncode(m['options']),
                'correct_json': jsonEncode(m['correct_answer']), 'hints_json': jsonEncode(m['hints'] ?? []),
                'explanation': m['explanation'], 'difficulty': m['difficulty'] ?? 2,
              },
              conflictAlgorithm: ConflictAlgorithm.replace);
        }
      }
    });
  }

  Future<void> saveOfficialProgress(List<dynamic> prog) async {
    for (final p in prog) {
      final m = p as Map<String, dynamic>;
      await db.insert('progress', {
        'competency_id': m['competency_id'], 'official_score': m['score'], 'official_evidence': m['evidence_count'],
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    }
  }

  Future<List<LocalTask>> tasks({String? origin}) async {
    final rows = await db.rawQuery('''
      SELECT t.*, (SELECT COUNT(*) FROM questions q WHERE q.student_assignment_id = t.student_assignment_id) AS total
      FROM tasks t ${origin == null ? '' : 'WHERE t.origin = ?'} ORDER BY t.seq''', origin == null ? [] : [origin]);
    final out = <LocalTask>[];
    for (final r in rows) {
      final id = r['student_assignment_id'] as String;
      final results = rules.questionResults(await _facts(id));
      out.add(LocalTask(id, r['origin'] as String, r['subject'] as String?, r['course_id'] as String?,
          r['competency_id'] as String,
          r['competency_name'] as String?, r['title'] as String, r['instructions'] as String, r['learning_objective'] as String,
          r['total'] as int, results.where((x) => x.closed).length));
    }
    return out;
  }

  Future<List<LocalQuestion>> questions(String saId) async {
    final rows = await db.query('questions', where: 'student_assignment_id = ?', whereArgs: [saId], orderBy: 'position');
    return rows
        .map((r) => LocalQuestion(
            r['id'] as String, r['position'] as int, r['type'] as String, r['prompt'] as String,
            r['options_json'] == null ? null : (jsonDecode(r['options_json'] as String) as List).cast<String>(),
            (jsonDecode(r['correct_json'] as String) as Map).cast<String, dynamic>(),
            (jsonDecode(r['hints_json'] as String) as List).cast<String>(), r['explanation'] as String?))
        .toList();
  }

  Future<List<rules.AttemptFact>> _facts(String saId, {String? competencyId}) async {
    final rows = competencyId == null
        ? await db.query('attempts', where: 'student_assignment_id = ?', whereArgs: [saId])
        : await db.rawQuery('''SELECT a.* FROM attempts a JOIN tasks t ON t.student_assignment_id = a.student_assignment_id
                               WHERE t.competency_id = ?''', [competencyId]);
    return rows
        .map((r) => rules.AttemptFact(r['question_id'] as String, r['attempt_number'] as int, (r['is_correct'] as int) == 1,
            r['hints_used'] as int, DateTime.parse(r['created_at'] as String)))
        .toList();
  }

  Future<int> attemptsCount(String saId, String qid) async => Sqflite.firstIntValue(await db.rawQuery(
          'SELECT COUNT(*) FROM attempts WHERE student_assignment_id = ? AND question_id = ?', [saId, qid])) ??
      0;

  Future<bool> questionClosed(String saId, String qid) async {
    final r = await db.query('attempts', where: 'student_assignment_id = ? AND question_id = ?', whereArgs: [saId, qid]);
    return r.any((x) => (x['is_correct'] as int) == 1) || r.length >= rules.maxAttempts;
  }

  /// Guarda el intento Y su evento de sync en UNA transacción. El UUID es la clave de idempotencia.
  /// Devuelve si la respuesta fue correcta según la corrección LOCAL (el servidor la re-evalúa).
  Future<bool> recordAttempt(String saId, LocalQuestion q, Map<String, dynamic> answer, int hintsUsed, int responseMs) async {
    final correct = rules.evaluateAnswer(q.type, q.correct, answer);
    if (correct == null) throw ArgumentError('Respuesta inválida');
    final n = await attemptsCount(saId, q.id) + 1;
    final id = _uuid.v4();
    final now = DateTime.now().toUtc().toIso8601String();
    await db.transaction((t) async {
      await t.insert('attempts', {
        'id': id, 'student_assignment_id': saId, 'question_id': q.id, 'attempt_number': n, 'answer_json': jsonEncode(answer),
        'is_correct': correct ? 1 : 0, 'hints_used': hintsUsed, 'response_time_ms': responseMs, 'created_at': now,
      });
      await t.insert('sync_queue', {
        'event_id': id, 'type': 'attempt.created', 'status': 'PENDING', 'attempts': 0, 'created_at': now, 'next_attempt_at': now,
        'payload_json': jsonEncode({
          'student_assignment_id': saId, 'question_id': q.id, 'attempt_number': n, 'answer': answer, 'is_correct': correct,
          'hints_used': hintsUsed, 'response_time_ms': responseMs, 'client_created_at': now,
        }),
      });
    });
    return correct;
  }

  Future<Map<String, int>> queueCounts() async {
    final rows = await db.rawQuery('SELECT status, COUNT(*) c FROM sync_queue GROUP BY status');
    return {for (final r in rows) r['status'] as String: r['c'] as int};
  }

  /// Progreso por competencia: local (provisional, calculado con las mismas reglas) y oficial del servidor.
  Future<List<Map<String, Object?>>> progress() async {
    final comps = await db.rawQuery('SELECT DISTINCT competency_id, competency_name FROM tasks');
    final out = <Map<String, Object?>>[];
    for (final c in comps) {
      final id = c['competency_id'] as String;
      final results = rules.questionResults(await _facts('', competencyId: id));
      final official = await db.query('progress', where: 'competency_id = ?', whereArgs: [id]);
      out.add({
        'competency': c['competency_name'] ?? id,
        'local': rules.localProgress(results),
        'official': official.isEmpty ? null : official.first['official_score'],
        'messages': rules.motivation(results, (c['competency_name'] ?? 'esta competencia') as String),
      });
    }
    return out;
  }
}
