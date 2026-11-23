/// Build-time settings. Nothing here is read from a file or hard-coded per environment.
library;

/// Base URL of the API, passed at build time and never written into code:
///
///     flutter run --dart-define=API_URL=https://movie-match-api-mgdn.onrender.com
///
/// CI passes it in .github/workflows/android.yml. Empty when the flag is missing; the app
/// then says so on screen instead of calling a wrong host.
const apiBaseUrl = String.fromEnvironment('API_URL');

bool get apiConfigured => apiBaseUrl.isNotEmpty;
