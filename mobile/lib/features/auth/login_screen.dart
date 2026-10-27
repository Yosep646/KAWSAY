import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../app/session.dart';
import '../../core/api/api_client.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _code = TextEditingController();
  final _pin = TextEditingController();
  String? _error;
  bool _busy = false;

  Future<void> _go() async {
    setState(() { _busy = true; _error = null; });
    try {
      await context.read<Session>().login(_code.text, _pin.text);
    } on NetworkException {
      _error = 'Necesitas Internet para entrar la primera vez. Después podrás trabajar sin conexión.';
    } on ApiException catch (e) {
      _error = e.status == 401 ? 'Código o PIN incorrectos' : e.message;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ListView(children: [
              const SizedBox(height: 40),
              Text('KAWSAY', style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 8),
              const Text('Escribe el código y el PIN que te dio tu profesor o profesora.'),
              const SizedBox(height: 24),
              TextField(controller: _code, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: 'Código', border: OutlineInputBorder())),
              const SizedBox(height: 16),
              TextField(controller: _pin, obscureText: true, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'PIN', border: OutlineInputBorder())),
              if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
              const SizedBox(height: 24),
              FilledButton(onPressed: _busy ? null : _go, child: Text(_busy ? 'Entrando…' : 'Entrar')),
            ]),
          ),
        ),
      );
}
