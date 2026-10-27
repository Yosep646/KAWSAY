/// URL del backend. Se define al compilar: flutter run --dart-define=KAWSAY_API=http://10.0.2.2:8000
/// (10.0.2.2 = localhost del host visto desde el emulador Android). Nunca hay claves de IA en la app.
const String kApiBase = String.fromEnvironment('KAWSAY_API', defaultValue: 'http://10.0.2.2:8000');
const int kSyncBatchSize = 100;
const int kMaxAttemptsPerQuestion = 3; // igual que RULES['max_attempts_per_question'] del backend
