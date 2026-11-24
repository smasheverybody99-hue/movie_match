/// Small values kept on the phone between app starts (web: localStorage). Behind an
/// interface so widget tests can keep them in memory and still "restart" the app with the
/// same store.
library;

import 'package:shared_preferences/shared_preferences.dart';

abstract interface class LocalStore {
  String? read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
}

class PrefsLocalStore implements LocalStore {
  PrefsLocalStore(this._prefs);

  final SharedPreferencesWithCache _prefs;

  @override
  String? read(String key) => _prefs.getString(key);

  @override
  Future<void> write(String key, String value) => _prefs.setString(key, value);

  @override
  Future<void> delete(String key) => _prefs.remove(key);
}

class MemoryLocalStore implements LocalStore {
  final values = <String, String>{};

  @override
  String? read(String key) => values[key];

  @override
  Future<void> write(String key, String value) async => values[key] = value;

  @override
  Future<void> delete(String key) async => values.remove(key);
}
