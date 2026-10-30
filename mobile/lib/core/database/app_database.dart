import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// SQLite local: fuente de verdad del estudiante cuando no hay Internet.
/// Cada attempt se guarda junto con su evento de sync_queue en UNA transacción (nunca uno sin el otro).
class AppDatabase {
  AppDatabase._(this.db);
  final Database db;
  static const int schemaVersion = 1;

  static Future<AppDatabase> open({String? path}) async {
    final dbPath = path ?? p.join(await getDatabasesPath(), 'kawsay.db');
    final db = await openDatabase(dbPath, version: schemaVersion, onConfigure: (d) async {
      await d.execute('PRAGMA foreign_keys = ON');
    }, onCreate: (d, v) async => _create(d));
    // Recuperación ante cierre brusco: lo que quedó SYNCING vuelve a PENDING (el servidor es idempotente).
    await db.update('sync_queue', {'status': 'PENDING'}, where: "status = 'SYNCING'");
    return AppDatabase._(db);
  }

  static Future<void> _create(Database d) async {
    await d.execute('''CREATE TABLE profile(
      id TEXT PRIMARY KEY, display_name TEXT NOT NULL, role TEXT NOT NULL, grade_id INTEGER,
      preferred_language TEXT, mother_language TEXT, updated_at TEXT NOT NULL)''');
    await d.execute('''CREATE TABLE tasks(
      student_assignment_id TEXT PRIMARY KEY, assignment_id TEXT NOT NULL, variant_id TEXT NOT NULL,
      origin TEXT NOT NULL CHECK(origin IN ('TEACHER','SELF')), grade_id INTEGER NOT NULL,
      subject TEXT, competency_id TEXT NOT NULL, competency_name TEXT, topic_id TEXT, topic_title TEXT,
      title TEXT NOT NULL, instructions TEXT NOT NULL, learning_objective TEXT NOT NULL,
      translation_json TEXT, seq INTEGER NOT NULL, pulled_at TEXT NOT NULL)''');
    await d.execute('''CREATE TABLE questions(
      id TEXT PRIMARY KEY, student_assignment_id TEXT NOT NULL REFERENCES tasks(student_assignment_id) ON DELETE CASCADE,
      position INTEGER NOT NULL, type TEXT NOT NULL, prompt TEXT NOT NULL, options_json TEXT,
      correct_json TEXT NOT NULL, hints_json TEXT NOT NULL, explanation TEXT, difficulty INTEGER NOT NULL)''');
    await d.execute('''CREATE TABLE attempts(
      id TEXT PRIMARY KEY, student_assignment_id TEXT NOT NULL, question_id TEXT NOT NULL,
      attempt_number INTEGER NOT NULL CHECK(attempt_number >= 1), answer_json TEXT NOT NULL,
      is_correct INTEGER NOT NULL, hints_used INTEGER NOT NULL CHECK(hints_used >= 0),
      response_time_ms INTEGER NOT NULL CHECK(response_time_ms >= 0), created_at TEXT NOT NULL,
      UNIQUE(student_assignment_id, question_id, attempt_number))''');
    await d.execute('''CREATE TABLE progress(
      competency_id TEXT PRIMARY KEY, competency_name TEXT, official_score REAL, official_evidence INTEGER,
      updated_at TEXT NOT NULL)''');
    await d.execute('''CREATE TABLE sync_queue(
      event_id TEXT PRIMARY KEY, type TEXT NOT NULL, payload_json TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('PENDING','SYNCING','SYNCED','FAILED','CONFLICT')),
      attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_at TEXT NOT NULL, next_attempt_at TEXT NOT NULL)''');
    await d.execute('CREATE INDEX ix_queue_status ON sync_queue(status, next_attempt_at)');
    await d.execute('CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)');
  }

  Future<void> close() => db.close();
}
