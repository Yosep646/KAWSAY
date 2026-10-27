/// Reglas pedagógicas LOCALES (sin IA, sin Internet). Espejo de backend/app/domain/adaptive.py.
/// Es lo que permite corregir, dar pistas y estimar progreso sin conexión. El servidor RE-corrige y recalcula.
import 'dart:convert';

const double scoreClean = 1.0, scoreSome = 0.7, scoreMuch = 0.4, scoreWrong = 0.0;
const int maxAttempts = 3;
const int progressWindow = 20, progressMinEvidence = 5;
const double progressDecay = 0.9;

class AttemptFact {
  AttemptFact(this.questionId, this.attemptNumber, this.isCorrect, this.hintsUsed, this.at);
  final String questionId;
  final int attemptNumber;
  final bool isCorrect;
  final int hintsUsed;
  final DateTime at;
}

class QuestionResult {
  QuestionResult(this.questionId, this.score, this.closed, this.hints, this.at);
  final String questionId;
  final double score;
  final bool closed;
  final int hints;
  final DateTime at;
}

/// Corrección local. null = respuesta mal formada. Misma lógica que evaluate_answer() del servidor.
bool? evaluateAnswer(String type, Map<String, dynamic> correct, Map<String, dynamic> answer) {
  try {
    switch (type) {
      case 'MULTIPLE_CHOICE':
        final idx = answer['index'];
        return idx is int ? idx == correct['index'] : null;
      case 'NUMERIC':
        final v = answer['value'];
        if (v is! num) return null;
        final tol = (correct['tolerance'] as num?) ?? 0;
        return ((v.toDouble()) - (correct['value'] as num).toDouble()).abs() <= tol.toDouble();
      case 'SHORT_TEXT':
        final t = answer['text'];
        if (t is! String) return null;
        String norm(String s) => s.toLowerCase().trim().split(RegExp(r'\s+')).join(' ');
        return (correct['accepted'] as List).map((e) => norm(e as String)).contains(norm(t));
    }
  } catch (_) {
    return null;
  }
  return null;
}

List<QuestionResult> questionResults(List<AttemptFact> attempts) {
  final byQ = <String, List<AttemptFact>>{};
  for (final a in attempts) {
    byQ.putIfAbsent(a.questionId, () => []).add(a);
  }
  final out = <QuestionResult>[];
  byQ.forEach((qid, items) {
    final correct = items.any((a) => a.isCorrect);
    final wrong = items.where((a) => !a.isCorrect).length;
    final hints = items.fold<int>(0, (s, a) => s + a.hintsUsed);
    final closed = correct || items.length >= maxAttempts;
    final score = !correct
        ? scoreWrong
        : (hints >= 2 || wrong >= 2)
            ? scoreMuch
            : (hints == 1 || wrong == 1)
                ? scoreSome
                : scoreClean;
    out.add(QuestionResult(qid, score, closed, hints,
        items.map((a) => a.at).reduce((a, b) => a.isAfter(b) ? a : b)));
  });
  return out;
}

/// Media ponderada por recencia. null = sin evidencia suficiente (no se inventa un porcentaje).
double? localProgress(List<QuestionResult> results) {
  final closed = results.where((r) => r.closed).toList()..sort((a, b) => b.at.compareTo(a.at));
  final recent = closed.take(progressWindow).toList();
  if (recent.length < progressMinEvidence) return null;
  var num = 0.0, den = 0.0, w = 1.0;
  for (final r in recent) {
    num += w * r.score;
    den += w;
    w *= progressDecay;
  }
  return double.parse((num / den).toStringAsFixed(4));
}

/// Escalera de ayuda local: 0 guía, 1 y 2 pistas del docente, 3 andamiaje. NUNCA revela la respuesta.
String localHint(List<String> hints, int step) {
  const generic = [
    'Antes de responder, léelo con calma: ¿qué te pide el ejercicio? Cuéntalo con tus palabras.',
    'Piensa en lo que ya sabes sobre este tema. ¿Qué datos del ejercicio te sirven?',
    'Mira cada opción y descarta la que sabes que no encaja. ¿Cuál te parece mejor y por qué?',
    'Vamos paso a paso: resuelve primero una parte pequeña y luego únela con el resto.',
  ];
  final s = step.clamp(0, 3);
  if (s == 1 && hints.isNotEmpty) return hints[0];
  if (s == 2 && hints.length > 1) return hints[1];
  return generic[s];
}

/// Motivación solo con datos reales; si no hay evidencia, no hay mensaje.
List<String> motivation(List<QuestionResult> results, String competency) {
  final c = results.where((r) => r.closed).toList()..sort((a, b) => a.at.compareTo(b.at));
  final msgs = <String>[];
  var streak = 0;
  for (final r in c.reversed) {
    if (r.score != scoreClean) break;
    streak++;
  }
  if (streak >= 3) msgs.add('Resolviste $streak ejercicios seguidos sin ayuda en $competency.');
  if (c.length >= 10) {
    double mean(List<QuestionResult> l) => l.fold<double>(0, (s, r) => s + r.score) / l.length;
    final a = mean(c.sublist(c.length - 10, c.length - 5)), b = mean(c.sublist(c.length - 5));
    if (b - a >= 0.2) msgs.add('Tu precisión mejoró en $competency: de ${(a * 100).round()} % a ${(b * 100).round()} %.');
  }
  return msgs;
}

String jsonOf(Object o) => jsonEncode(o);
