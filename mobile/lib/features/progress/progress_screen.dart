import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/data/repository.dart';

/// Progreso sencillo y positivo: sin etiquetas negativas. Si no hay evidencia suficiente, no se inventa un %.
class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mi progreso')),
        body: FutureBuilder<List<Map<String, Object?>>>(
          future: context.read<Repository>().progress(),
          builder: (_, snap) {
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            if (snap.data!.isEmpty) return const Center(child: Text('Cuando resuelvas ejercicios, aquí verás cómo avanzas.'));
            return ListView(padding: const EdgeInsets.all(16), children: [
              for (final p in snap.data!) Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${p['competency']}', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Builder(builder: (_) {
                  final v = (p['official'] ?? p['local']) as num?; // el servidor es la referencia; local = provisional
                  if (v == null) return const Text('Sigue practicando: aún no hay suficientes ejercicios para mostrar tu avance.');
                  return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    LinearProgressIndicator(value: v.toDouble(), minHeight: 14),
                    Text('${(v * 100).round()} %${p['official'] == null ? ' (se confirmará al sincronizar)' : ''}'),
                  ]);
                }),
                for (final m in (p['messages'] as List<String>)) Padding(padding: const EdgeInsets.only(top: 8), child: Text(m)),
              ]))),
            ]);
          },
        ),
      );
}
