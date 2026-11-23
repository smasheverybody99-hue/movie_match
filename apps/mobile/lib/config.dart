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

/// Supabase project URL and anon key: public values (the web ships them too), kept out of
/// git like every key and passed with --dart-define. CI takes them from the repository
/// variables SUPABASE_URL and SUPABASE_ANON_KEY. Without them sign-in says it is not set
/// up, as /welcome does on the web.
const supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const supabaseAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');

bool get authConfigured => supabaseUrl.isNotEmpty && supabaseAnonKey.isNotEmpty;

/// Where Supabase sends the browser back after Google, Apple or the email link. It must be
/// in the project's Redirect URLs (Authentication → URL Configuration) and match the
/// intent filter in android/app/src/main/AndroidManifest.xml. A URI scheme cannot hold
/// "_", so it is not the application id.
const authRedirectUrl = 'com.moviematch.moviematch://login-callback';
