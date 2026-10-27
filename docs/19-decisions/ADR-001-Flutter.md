# ADR-001 · Flutter para la app de estudiante
**Estado:** Propuesto
## Contexto
Android primero, luego iOS/Windows/macOS/tablets; equipos pequeños; dispositivos de gama baja; offline.
## Decisión
Flutter/Dart con capas `presentation/domain/data`, SQLite local (drift o sqflite+migraciones), gestor de estado Riverpod/Bloc (se decide en Fase 7).
## Alternativas
Nativo Kotlin/Swift (más costo, dos bases de código); React Native (buen ecosistema, SQLite y rendimiento en gama baja menos predecibles); PWA (offline limitado, almacenamiento no garantizado).
## Consecuencias
+ Un código para 4 plataformas, buen rendimiento; − Dart menos común, soporte desktop menos maduro que móvil; tamaño de APK a vigilar.
