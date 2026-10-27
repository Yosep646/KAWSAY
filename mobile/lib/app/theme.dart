import 'package:flutter/material.dart';

ThemeData kawsayTheme(Brightness b) => ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1F6F4A), brightness: b),
      textTheme: const TextTheme(bodyMedium: TextStyle(fontSize: 18), titleLarge: TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
      // botones grandes (>= 56 dp) para manos pequeñas y pantallas táctiles
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(64), textStyle: const TextStyle(fontSize: 20))),
      outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(56), textStyle: const TextStyle(fontSize: 18))),
    );
