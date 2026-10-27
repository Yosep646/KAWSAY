import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../features/auth/login_screen.dart';
import '../features/home/home_screen.dart';
import 'session.dart';
import 'theme.dart';

class KawsayApp extends StatelessWidget {
  const KawsayApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'KAWSAY',
        theme: kawsayTheme(Brightness.light),
        darkTheme: kawsayTheme(Brightness.dark),
        home: Consumer<Session>(builder: (_, s, __) => s.signedIn ? const HomeScreen() : const LoginScreen()),
      );
}
