class AppConstants {
  AppConstants._();

  static const String appName = 'VoiceBridge';
  static const String appVersion = '1.0.0';
  static const String appTagline = 'Offline multilingual clinical intake AI';

  static const String apiBaseUrl = 'http://localhost:8000';

  static const int maxRecordingSeconds = 120;
  static const int splashTimeoutSeconds = 30;
  static const int recentCasesLimit = 5;

  static const String modelFileName = 'voicebridge-q4km.gguf';

  static const List<String> supportedLanguages = [
    'English',
    'Swahili',
    'Tagalog',
    'Bengali',
    'Hausa',
    'Spanish',
    'French',
    'Arabic',
  ];

  static const Map<String, String> languageCodes = {
    'English': 'en',
    'Swahili': 'sw',
    'Tagalog': 'tl',
    'Bengali': 'bn',
    'Hausa': 'ha',
    'Spanish': 'es',
    'French': 'fr',
    'Arabic': 'ar',
  };
}
