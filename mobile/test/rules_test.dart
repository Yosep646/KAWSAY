// Verifica que la lógica LOCAL de la app coincide con el servidor, usando vectores generados desde Python:
//   python scripts/gen_rule_vectors.py   ->  shared/rules_vectors.json
// ESTADO: escrito, NO ejecutado (no hay Flutter/Dart en el entorno de desarrollo). Ejecutar: flutter test
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:kawsay_student/core/offline/rules.dart' as r;

void main() {
  final vectors = jsonDecode(File('../shared/rules_vectors.json').readAsStringSync()) as Map<String, dynamic>;
  final t0 = DateTime.utc(2026, 5, 4, 9);

  test('evaluateAnswer coincide con el servidor', () {
    for (final v in vectors['evaluate'] as List) {
      final got = r.evaluateAnswer(v['type'] as String, Map<String, dynamic>.from(v['correct'] as Map), Map<String, dynamic>.from(v['answer'] as Map));
      expect(got, v['expected'], reason: '${v['type']} ${v['answer']}');
    }
  });

  for (final s in vectors['scenarios'] as List) {
    test('escenario ${s['name']}: scores, cierre y progreso coinciden', () {
      final facts = [for (final a in s['attempts'] as List) r.AttemptFact(a['q'] as String, a['n'] as int, a['ok'] as bool, a['hints'] as int, t0.add(Duration(minutes: a['minute'] as int)))];
      final results = r.questionResults(facts);
      final expected = (s['results'] as Map).cast<String, dynamic>();
      expect(results.length, expected.length);
      for (final res in results) {
        final e = expected[res.questionId] as Map<String, dynamic>;
        expect(res.score, (e['score'] as num).toDouble(), reason: res.questionId);
        expect(res.closed, e['closed']);
        expect(res.hints, e['hints']);
      }
      final p = r.localProgress(results);
      final ep = s['progress'] as num?;
      if (ep == null) {
        expect(p, isNull);
      } else {
        expect(p, closeTo(ep.toDouble(), 1e-4));
      }
      final msgs = r.motivation(results, 'Cantidad');
      expect(msgs.where((m) => m.startsWith('Resolviste')).firstOrNull, s['streak_message']);
      expect(msgs.where((m) => m.startsWith('Tu precisión')).firstOrNull, s['improve_message']);
    });
  }

  test('la pista local nunca revela la respuesta y escala', () {
    expect(r.localHint(['pista A', 'pista B'], 1), 'pista A');
    expect(r.localHint(['pista A', 'pista B'], 2), 'pista B');
    expect(r.localHint([], 1), contains('Piensa'));
    expect(r.localHint(['x'], 99), contains('paso a paso'));
  });
}
