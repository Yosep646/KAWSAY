import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../app/session.dart';
import '../../core/api/api_client.dart';
import '../../core/data/repository.dart';
import '../../core/sync/sync_manager.dart';

/// El estudiante declara su idioma; si pierde Internet, se encola en SQLite.
/// El servidor sólo entrega contenido en traducciones pedagógicas verificadas.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  List<dynamic> _langs = [];
  String? _mother, _motherVariantId, _preferred, _msg;
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final repo = context.read<Repository>();
    try {
      final cachedLanguages = await repo.languageCatalog();
      final cachedPreferences = await repo.languagePreferencesLocal();
      if (mounted) {
        setState(() {
          _langs = cachedLanguages;
          _mother = cachedPreferences?['mother_language'] as String?;
          _motherVariantId = cachedPreferences?['mother_variant_id'] as String?;
          _preferred = cachedPreferences?['preferred_language'] as String?;
          _loading = false;
        });
      }

      final api = context.read<ApiClient>();
      final fetched = await Future.wait([api.languages(), api.languagePreferences()]);
      final languages = fetched[0] as List<dynamic>;
      final preference = fetched[1] as Map<String, dynamic>;
      await repo.saveLanguageCatalog(languages);
      final pending = await repo.pendingLanguagePreferences();
      if (pending == null) {
        await repo.storeLanguagePreferences(preference);
      }
      if (!mounted) return;
      setState(() {
        _langs = languages;
        if (pending == null) {
          _mother = preference['mother_language'] as String?;
          _motherVariantId = preference['mother_variant_id'] as String?;
          _preferred = preference['preferred_language'] as String?;
        }
        _msg = pending == null ? null : 'Tienes un cambio de idioma pendiente de sincronizar.';
      });
    } on NetworkException {
      if (mounted) setState(() {
        _loading = false;
        _msg = _langs.isEmpty
            ? 'Primero conéctate una vez para descargar los idiomas disponibles.'
            : 'Sin conexión: puedes elegir un idioma; el cambio se enviará cuando vuelva Internet.';
      });
    } on ApiException catch (e) {
      if (mounted) setState(() { _loading = false; _msg = e.message; });
    }
  }

  Future<void> _save() async {
    if (_saving || _langs.isEmpty) return;
    setState(() => _saving = true);
    try {
      final repo = context.read<Repository>();
      await repo.queueLanguagePreferences(_mother, _motherVariantId, _preferred);
      await context.read<SyncManager>().syncNow();
      final pending = await repo.pendingLanguagePreferences();
      if (!mounted) return;
      setState(() => _msg = pending == null
          ? 'Idioma guardado en tu cuenta. Solo se muestran traducciones educativas verificadas.'
          : 'Tu elección está guardada en este dispositivo y se enviará cuando haya conexión.');
    } catch (_) {
      if (mounted) setState(() => _msg =
          'No se pudo guardar tu elección en el dispositivo. Verifica el espacio de almacenamiento.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    List<DropdownMenuItem<String?>> items() => [
      const DropdownMenuItem(value: null, child: Text('Sin indicar')),
      for (final language in _langs)
        DropdownMenuItem(value: language['code'] as String, child: Text('${language['name']}')),
    ];
    final motherLanguage = _langs.cast<Map>().where((l) => l['code'] == _mother).firstOrNull;
    final variants = (motherLanguage?['variants'] as List<dynamic>?) ?? const [];
    return Scaffold(
      appBar: AppBar(title: const Text('Mi idioma y ajustes')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (_loading) const LinearProgressIndicator(),
        DropdownButtonFormField<String?>(
          value: _mother,
          items: items(),
          onChanged: _loading || _langs.isEmpty ? null : (value) => setState(() {
            _mother = value;
            _motherVariantId = null;
          }),
          decoration: const InputDecoration(labelText: 'Mi lengua materna'),
        ),
        if (variants.isNotEmpty) ...[
          const SizedBox(height: 16),
          DropdownButtonFormField<String?>(
            value: _motherVariantId,
            items: [
              const DropdownMenuItem(value: null, child: Text('Sin indicar')),
              for (final variant in variants)
                DropdownMenuItem(value: variant['id'] as String, child: Text('${variant['name']}')),
            ],
            onChanged: (value) => setState(() => _motherVariantId = value),
            decoration: const InputDecoration(labelText: 'Variante declarada'),
          ),
        ],
        const SizedBox(height: 16),
        DropdownButtonFormField<String?>(
          value: _preferred,
          items: items(),
          onChanged: _loading || _langs.isEmpty ? null : (value) => setState(() => _preferred = value),
          decoration: const InputDecoration(labelText: 'Prefiero aprender en'),
        ),
        const SizedBox(height: 16),
        const Text('El idioma lo eliges tú o tu familia. No se determina por tu ubicación. '
            'El contenido se traduce únicamente cuando una persona lo ha revisado y aprobado.'),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: _langs.isEmpty || _loading || _saving ? null : _save,
          child: Text(_saving ? 'Guardando…' : 'Guardar mi idioma'),
        ),
        if (_msg != null) Padding(padding: const EdgeInsets.only(top: 12),
          child: Text(_msg!, key: const Key('language-save-status'))),
        const Divider(height: 40),
        OutlinedButton(
          onPressed: () async {
            final ok = await context.read<Session>().canLogoutSafely();
            if (!context.mounted) return;
            if (!ok) {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Tienes respuestas sin enviar. Conéctate y sincroniza antes de salir.'),
              ));
              return;
            }
            final repo = context.read<Repository>();
            if (await repo.pendingLanguagePreferences() != null) {
              if (!context.mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Tienes un cambio de idioma sin sincronizar. Conéctate antes de salir.'),
              ));
              return;
            }
            await context.read<Session>().logout();
            if (context.mounted) Navigator.of(context).popUntil((route) => route.isFirst);
          },
          child: const Text('Cerrar sesión'),
        ),
      ]),
    );
  }
}
