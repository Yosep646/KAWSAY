import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../app/session.dart';
import '../../core/api/api_client.dart';
import '../../core/data/repository.dart';
import '../../core/sync/sync_manager.dart';

/// Idioma: lo elige la persona. NUNCA se infiere por ubicación. Solo se muestran traducciones verificadas.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  List<dynamic> _langs = [];
  String? _mother, _motherVariantId, _preferred, _msg;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final api = context.read<ApiClient>();
      final result = await Future.wait([api.languages(), api.languagePreferences()]);
      if (!mounted) return;
      final preference = result[1] as Map<String, dynamic>;
      setState(() {
        _langs = result[0] as List<dynamic>;
        _mother = preference['mother_language'] as String?;
        _motherVariantId = preference['mother_variant_id'] as String?;
        _preferred = preference['preferred_language'] as String?;
        _loading = false;
      });
    } on NetworkException {
      if (mounted) setState(() { _loading = false; _msg = 'Sin conexión: para cambiar el idioma necesitas Internet.'; });
    } on ApiException catch (e) {
      if (mounted) setState(() { _loading = false; _msg = e.message; });
    }
  }

  Future<void> _save() async {
    final api = context.read<ApiClient>();
    final repo = context.read<Repository>();
    final sync = context.read<SyncManager>();
    try {
      final saved = await api.setLanguages(_mother, _motherVariantId, _preferred);
      await repo.saveLanguages(saved['mother_language'] as String?, saved['preferred_language'] as String?);
      await sync.syncNow();
      if (!mounted) return;
      setState(() => _msg = 'Guardado. Verás el contenido en ese idioma cuando exista una traducción verificada.');
    } on NetworkException {
      if (mounted) setState(() => _msg = 'Sin conexión: inténtalo cuando tengas Internet.');
    } on ApiException catch (e) {
      if (mounted) setState(() => _msg = e.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    List<DropdownMenuItem<String?>> items() => [const DropdownMenuItem(value: null, child: Text('Sin indicar')), for (final l in _langs) DropdownMenuItem(value: l['code'] as String, child: Text('${l['name']}'))];
    final motherLanguage = _langs.cast<Map>().where((l) => l['code'] == _mother).firstOrNull;
    final variants = (motherLanguage?['variants'] as List<dynamic>?) ?? const [];
    return Scaffold(
      appBar: AppBar(title: const Text('Ajustes')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (_loading) const LinearProgressIndicator(),
        // Keep value for the declared Flutter 3.22 minimum (initialValue requires a newer SDK).
        // ignore: deprecated_member_use
        DropdownButtonFormField<String?>(value: _mother, items: items(), onChanged: _loading ? null : (v) => setState(() { _mother = v; _motherVariantId = null; }), decoration: const InputDecoration(labelText: 'Mi lengua materna')),
        if (variants.isNotEmpty) ...[
          const SizedBox(height: 16),
          DropdownButtonFormField<String?>(
            // ignore: deprecated_member_use
            value: _motherVariantId,
            items: [const DropdownMenuItem(value: null, child: Text('Sin indicar')), for (final v in variants) DropdownMenuItem(value: v['id'] as String, child: Text('${v['name']}'))],
            onChanged: (v) => setState(() => _motherVariantId = v),
            decoration: const InputDecoration(labelText: 'Variante declarada'),
          ),
        ],
        const SizedBox(height: 16),
        // ignore: deprecated_member_use
        DropdownButtonFormField<String?>(value: _preferred, items: items(), onChanged: _loading ? null : (v) => setState(() => _preferred = v), decoration: const InputDecoration(labelText: 'Prefiero aprender en')),
        const SizedBox(height: 16),
        const Text('El idioma se registra según lo que tú o tu familia declaran. No se determina por tu ubicación.'),
        const SizedBox(height: 16),
        FilledButton(onPressed: _langs.isEmpty || _loading ? null : _save, child: const Text('Guardar')),
        if (_msg != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_msg!)),
        const Divider(height: 40),
        OutlinedButton(onPressed: () async {
          final ok = await context.read<Session>().canLogoutSafely();
          if (!context.mounted) return;
          if (!ok) { ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Tienes respuestas sin enviar. Conéctate y sincroniza antes de salir.'))); return; }
          await context.read<Session>().logout();
          if (context.mounted) Navigator.of(context).popUntil((r) => r.isFirst);
        }, child: const Text('Cerrar sesión')),
      ]),
    );
  }
}
