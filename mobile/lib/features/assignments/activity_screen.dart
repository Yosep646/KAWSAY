import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api/api_client.dart';
import '../../core/config.dart';
import '../../core/data/repository.dart';
import '../../core/offline/rules.dart' as rules;
import '../../core/sync/sync_manager.dart';

/// Funciona SIN Internet: corrige localmente, da pistas descargadas y guarda cada intento en SQLite.
class ActivityScreen extends StatefulWidget {
  const ActivityScreen({super.key, required this.task});
  final LocalTask task;
  @override
  State<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends State<ActivityScreen> {
  List<LocalQuestion> _qs = [];
  int _i = 0;
  int _hints = 0;
  String? _feedback;
  String? _hintText;
  bool _closed = false;
  bool _loading = true;
  bool _saving = false;
  final _text = TextEditingController();
  late DateTime _shownAt;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final repo = context.read<Repository>();
    final qs = await repo.questions(widget.task.id);
    var i = 0;
    while (i < qs.length && await repo.questionClosed(widget.task.id, qs[i].id)) { i++; } // continúa donde quedó
    if (!mounted) return;
    setState(() { _qs = qs; _i = i; _loading = false; _shownAt = DateTime.now(); });
  }

  LocalQuestion get _q => _qs[_i];

  Future<void> _answer(Map<String, dynamic> answer) async {
    if (_saving || _closed) return;
    final repo = context.read<Repository>();
    final sync = context.read<SyncManager>();
    final question = _q;
    final ms = DateTime.now().difference(_shownAt).inMilliseconds;
    setState(() => _saving = true);
    try {
    final ok = await repo.recordAttempt(widget.task.id, question, answer, _hints, ms);
    final closed = await repo.questionClosed(widget.task.id, question.id);
    sync.refreshCounts();
    sync.syncNow(); // no bloquea: si no hay red, queda PENDING
    if (!mounted) return;
    _hints = 0;
    setState(() {
      _closed = closed;
      _hintText = null;
      _feedback = ok
          ? 'Correcto.'
          : closed ? (question.explanation ?? 'Revisemos juntos cómo se resuelve.') : 'Casi. Inténtalo otra vez; puedes pedir una pista.';
    });
    } catch (_) {
      if (mounted) setState(() => _feedback = 'No se pudo completar el guardado. Vuelve a abrir la actividad para revisar tu respuesta.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _help() async {
    final repo = context.read<Repository>();
    final api = context.read<ApiClient>();
    final question = _q;
    final attempts = await repo.attemptsCount(widget.task.id, _q.id);
    if (!mounted) return;
    final step = (_hints + 1 > attempts + 1 ? _hints + 1 : attempts + 1).clamp(0, 3);
    String text = rules.localHint(_q.hints, step); // siempre disponible offline
    try { // si hay Internet, el tutor del servidor puede dar una pista más personalizada (sin revelar la respuesta)
      final r = await api.tutorTurn(widget.task.id, question.id, step);
      text = (r['message'] as String?) ?? text;
    } catch (_) {}
    if (!mounted) return;
    setState(() { _hints++; _hintText = text; });
  }

  void _next() {
    setState(() { _i++; _feedback = null; _closed = false; _hintText = null; _text.clear(); _shownAt = DateTime.now(); });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_i >= _qs.length) return _Done(task: widget.task);
    final q = _q;
    return Scaffold(
      appBar: AppBar(title: Text(widget.task.title)),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text('Ejercicio ${_i + 1} de ${_qs.length}'),
        const SizedBox(height: 8),
        Text(q.prompt, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 16),
        if (!_closed) ...[
          if (q.type == 'MULTIPLE_CHOICE')
            for (var k = 0; k < (q.options?.length ?? 0); k++)
              Padding(padding: const EdgeInsets.only(bottom: 12), child: OutlinedButton(onPressed: _saving ? null : () => _answer({'index': k}), child: Text(q.options![k]))),
          if (q.type != 'MULTIPLE_CHOICE') ...[
            TextField(controller: _text, keyboardType: q.type == 'NUMERIC' ? const TextInputType.numberWithOptions(decimal: true) : TextInputType.text, decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Tu respuesta')),
            const SizedBox(height: 12),
            FilledButton(onPressed: _saving ? null : () {
              if (q.type == 'NUMERIC') {
                final v = num.tryParse(_text.text.replaceAll(',', '.'));
                if (v != null) _answer({'value': v});
              } else if (_text.text.trim().isNotEmpty) { _answer({'text': _text.text}); }
            }, child: const Text('Responder')),
          ],
          const SizedBox(height: 8),
          TextButton.icon(onPressed: _saving ? null : _help, icon: const Icon(Icons.lightbulb), label: const Text('Pedir una pista')),
        ],
        if (_hintText != null) Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(_hintText!))),
        if (_feedback != null) Card(color: Theme.of(context).colorScheme.secondaryContainer, child: Padding(padding: const EdgeInsets.all(16), child: Text(_feedback!))),
        if (_closed) FilledButton(onPressed: _next, child: Text(_i + 1 >= _qs.length ? 'Terminar' : 'Siguiente')),
        const SizedBox(height: 8),
        Text('Intentos por ejercicio: hasta $kMaxAttemptsPerQuestion', style: Theme.of(context).textTheme.bodySmall),
      ]),
    );
  }
}

class _Done extends StatelessWidget {
  const _Done({required this.task});
  final LocalTask task;
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(task.title)),
        body: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.check_circle, size: 72),
          const SizedBox(height: 16),
          const Text('Terminaste esta actividad. Tu trabajo está guardado en este dispositivo y se enviará cuando haya Internet.', textAlign: TextAlign.center),
          const SizedBox(height: 24),
          FilledButton(onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst), child: const Text('Volver al inicio')),
        ])),
      );
}
