/// The API client. Mirrors apps/web/src/lib/api.ts: same endpoints, a bearer token set
/// from the Supabase session (Supabase issues it, the API verifies it), and one exception
/// type whose `status` the screens branch on.
library;

import 'dart:convert';

import 'package:dio/dio.dart';

import 'models.dart';

/// Any failed request. `status` is the HTTP status, or 0 when the request never got an
/// answer (offline, timeout, API down). Screens branch on `status` and `retryable`, never
/// on `message`: the message is for logs, not for users.
class ApiException implements Exception {
  const ApiException(this.status, this.message, {this.retryable = false});

  final int status;
  final String message;

  /// Worth a "Try again" button: no answer, or the server failed (5xx).
  final bool retryable;

  bool get isNotFound => status == 404;
  bool get isUnauthorized => status == 401;

  @override
  String toString() => 'ApiException($status): $message';
}

/// The assistant's 429: today's messages are used up until `limit.resetsAt` (FR-8).
class AssistantLimitException extends ApiException {
  AssistantLimitException(this.limit) : super(429, limit.detail);
  final AssistantLimit limit;
}

class SearchParams {
  const SearchParams({
    this.q,
    this.yearFrom,
    this.yearTo,
    this.maxRuntime,
    this.traits = const [],
    this.traitMinimum = 70,
    this.limit = 40,
  });

  final String? q;
  final int? yearFrom;
  final int? yearTo;
  final int? maxRuntime;

  /// Trait keys; each means "scores at least `traitMinimum`".
  final List<String> traits;
  final int traitMinimum;
  final int limit;

  /// Two searches are the same when they send the same request (a provider key).
  @override
  bool operator ==(Object other) => other is SearchParams && other.toQuery() == toQuery();

  @override
  int get hashCode => toQuery().hashCode;

  /// The query string, as searchQuery() in api.ts builds it (`trait` repeats).
  String toQuery() => Uri(queryParameters: {
        if (q != null && q!.isNotEmpty) 'q': q,
        if (yearFrom != null) 'year_from': '$yearFrom',
        if (yearTo != null) 'year_to': '$yearTo',
        if (maxRuntime != null) 'max_runtime': '$maxRuntime',
        if (traits.isNotEmpty) 'trait': [for (final t in traits) '$t:$traitMinimum'],
        'limit': '$limit',
      }).query;
}

/// Complete SSE blocks out of `buffer`, and what is left of it (a block still arriving).
/// Mirrors readSse() in api.ts.
({List<AssistantEvent> events, String rest}) readSse(String buffer) {
  final blocks = buffer.replaceAll('\r\n', '\n').split('\n\n');
  final rest = blocks.removeLast();
  final events = <AssistantEvent>[];
  for (final block in blocks) {
    var name = 'message';
    final data = <String>[];
    for (final line in block.split('\n')) {
      if (line.startsWith('event:')) {
        name = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        data.add(line.substring(5).trimLeft());
      }
    }
    Object? parsed;
    try {
      parsed = jsonDecode(data.join('\n'));
    } on FormatException {
      continue;
    }
    final event = AssistantEvent.parse(name, parsed);
    if (event != null) events.add(event);
  }
  return (events: events, rest: rest);
}

class ApiClient {
  ApiClient({
    required String baseUrl,
    Dio? dio,
    Duration connectTimeout = const Duration(seconds: 15),
    Duration receiveTimeout = const Duration(seconds: 30),
  }) : _dio = dio ?? Dio() {
    _dio.options
      ..baseUrl = baseUrl
      ..connectTimeout = connectTimeout
      ..receiveTimeout = receiveTimeout
      ..sendTimeout = connectTimeout
      ..responseType = ResponseType.plain;
  }

  final Dio _dio;
  String? _accessToken;

  /// Set on every Supabase session change; null signed out.
  set accessToken(String? token) => _accessToken = token;
  bool get hasAccessToken => _accessToken != null;

  Map<String, String> get _headers => {
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  Future<Object?> _send(String method, String path, {Object? body}) async {
    final Response<String> response;
    try {
      response = await _dio.request<String>(
        path,
        data: body == null ? null : jsonEncode(body),
        options: Options(
          method: method,
          headers: _headers,
          contentType: body == null ? null : Headers.jsonContentType,
        ),
      );
    } on DioException catch (e) {
      throw _map(e);
    }
    final text = response.data ?? '';
    if (response.statusCode == 204 || text.isEmpty) return null;
    try {
      return jsonDecode(text);
    } on FormatException catch (e) {
      throw ApiException(response.statusCode ?? 0, 'not JSON: ${e.message}');
    }
  }

  Future<T> _get<T>(String path, T Function(Object? data) decode) =>
      _call('GET', path, decode: decode);

  Future<T> _call<T>(
    String method,
    String path, {
    Object? body,
    required T Function(Object? data) decode,
  }) async {
    final data = await _send(method, path, body: body);
    try {
      return decode(data);
    } on FormatError catch (e) {
      throw ApiException(200, 'unexpected response: ${e.message}');
    } on TypeError catch (e) {
      throw ApiException(200, 'unexpected response: $e');
    }
  }

  Future<void> _void(String method, String path, {Object? body}) =>
      _call(method, path, body: body, decode: (_) {});

  static Json _obj(Object? data) {
    if (data is Map<String, dynamic>) return data;
    throw FormatError('expected an object, got ${data.runtimeType}');
  }

  static List<T> _list<T>(Object? data, T Function(Json) item) {
    if (data is! List) throw FormatError('expected a list, got ${data.runtimeType}');
    return data.map((e) => item(_obj(e))).toList();
  }

  static ApiException _map(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.transformTimeout:
        return ApiException(0, 'timeout (${e.type.name})', retryable: true);
      case DioExceptionType.connectionError:
      case DioExceptionType.unknown:
        return ApiException(0, e.message ?? 'network error', retryable: true);
      case DioExceptionType.badResponse:
        final status = e.response?.statusCode ?? 0;
        final detail = '${e.response?.data ?? ''}';
        return ApiException(
          status,
          detail.isEmpty ? (e.response?.statusMessage ?? 'HTTP $status') : detail,
          retryable: status >= 500,
        );
      case DioExceptionType.cancel:
        return const ApiException(0, 'cancelled');
      case DioExceptionType.badCertificate:
        return const ApiException(0, 'bad certificate');
    }
  }

  // --- endpoints, in api.ts order -------------------------------------------------------

  Future<Health> health() => _get('/health', (d) => Health.fromJson(_obj(d)));

  Future<List<Movie>> searchMovies(SearchParams params) =>
      _get('/movies?${params.toQuery()}', (d) => _list(d, Movie.fromJson));

  Future<MovieDetail> getMovie(int id) => _get('/movies/$id', (d) => MovieDetail.fromJson(_obj(d)));

  Future<Me> me() => _get('/me', (d) => Me.fromJson(_obj(d)));
  Future<MovieDna> dna() => _get('/me/dna', (d) => MovieDna.fromJson(_obj(d)));
  Future<void> deleteAccount() => _void('DELETE', '/me');
  Future<void> acceptDataNotice() => _void('POST', '/me/data-notice');

  Future<List<Movie>> onboardingFilms(int limit, int offset) =>
      _get('/onboarding/films?limit=$limit&offset=$offset', (d) => _list(d, Movie.fromJson));

  Future<List<Rating>> ratings() => _get('/ratings', (d) => _list(d, Rating.fromJson));
  Future<Rating> rate(RatingIn body) =>
      _call('POST', '/ratings', body: body.toJson(), decode: (d) => Rating.fromJson(_obj(d)));
  Future<void> unrate(int movieId) => _void('DELETE', '/ratings/$movieId');

  Future<List<WatchlistItem>> watchlist() =>
      _get('/watchlist', (d) => _list(d, WatchlistItem.fromJson));
  Future<WatchlistItem> addToWatchlist(int movieId) => _call('POST', '/watchlist',
      body: {'movie_id': movieId}, decode: (d) => WatchlistItem.fromJson(_obj(d)));
  Future<void> removeFromWatchlist(int movieId) => _void('DELETE', '/watchlist/$movieId');
  Future<WatchlistItem> markWatched(int movieId) => _call('POST', '/watchlist/$movieId/watched',
      decode: (d) => WatchlistItem.fromJson(_obj(d)));

  Future<Recommendations> recommendations(Lang lang) =>
      _get('/recommendations?lang=${lang.name}', (d) => Recommendations.fromJson(_obj(d)));
  Future<Explanation> explanation(int movieId, Lang lang) => _get(
      '/recommendations/$movieId/explanation?lang=${lang.name}',
      (d) => Explanation.fromJson(_obj(d)));
  Future<void> dismiss(int movieId) => _void('POST', '/dismissals', body: {'movie_id': movieId});

  /// A batch of what the viewer saw; returns how many the API recorded.
  Future<int> sendEvents(List<ClientEvent> events) => _call('POST', '/events',
      body: {'events': [for (final e in events) e.toJson()]},
      decode: (d) => (_obj(d)['recorded'] as num).toInt());
  Future<void> onboardingDone() => _void('POST', '/onboarding/done');
  Future<void> markWrong(FeedbackIn body) => _void('POST', '/feedback', body: body.toJson());

  /// POST /assistant/chat as a stream of events, in arrival order; ends with the stream.
  /// Throws AssistantLimitException on the daily cap, ApiException otherwise.
  Stream<AssistantEvent> assistantChat(AssistantChatIn body, {CancelToken? cancel}) async* {
    final Response<ResponseBody> response;
    try {
      response = await _dio.post<ResponseBody>(
        '/assistant/chat',
        data: jsonEncode(body.toJson()),
        cancelToken: cancel,
        options: Options(
          headers: {..._headers, 'Accept': 'text/event-stream'},
          contentType: Headers.jsonContentType,
          responseType: ResponseType.stream,
          validateStatus: (_) => true,
        ),
      );
    } on DioException catch (e) {
      throw _map(e);
    }
    final status = response.statusCode ?? 0;
    final stream = response.data?.stream;
    if (status != 200 || stream == null) {
      final text = stream == null ? '' : await utf8.decodeStream(stream);
      if (status == 429) {
        Object? json;
        try {
          json = jsonDecode(text);
        } on FormatException {
          json = null;
        }
        final limit = AssistantLimit.tryParse(json);
        if (limit != null) throw AssistantLimitException(limit);
      }
      throw ApiException(status, text.isEmpty ? 'HTTP $status' : text, retryable: status >= 500);
    }
    var buffer = '';
    try {
      await for (final chunk in stream.cast<List<int>>().transform(utf8.decoder)) {
        final read = readSse(buffer + chunk);
        buffer = read.rest;
        yield* Stream.fromIterable(read.events);
      }
    } on DioException catch (e) {
      throw _map(e);
    }
    yield* Stream.fromIterable(readSse('$buffer\n\n').events);
  }
}
