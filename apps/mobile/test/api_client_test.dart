// api_client_test.dart (phase-06-mobile.md): token attached; error mapped to ApiException
// with the status; timeout produces a retryable error. No network: Dio gets a fake
// adapter that answers from the test.
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/data/api_client.dart';
import 'package:movie_match/data/models.dart';

typedef Handler = Future<ResponseBody> Function(RequestOptions options);

class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.handler);

  final Handler handler;
  final requests = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) {
    requests.add(options);
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody json(Object? body, [int status = 200]) => ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );

ResponseBody text(String body, int status) => ResponseBody.fromString(body, status);

Never dioError(DioExceptionType type, RequestOptions options) =>
    throw DioException(requestOptions: options, type: type);

({ApiClient client, FakeAdapter adapter}) make(Handler handler) {
  final adapter = FakeAdapter(handler);
  final dio = Dio()..httpClientAdapter = adapter;
  return (client: ApiClient(baseUrl: 'https://api.test', dio: dio), adapter: adapter);
}

const movieJson = {
  'id': 155,
  'title': 'The Dark Knight',
  'release_date': '2008-07-16',
  'runtime_minutes': 152,
  'overview': 'Batman raises the stakes.',
  'poster_path': '/p.jpg',
  'backdrop_path': '/b.jpg',
  'genres': ['Action', 'Crime'],
};

const meJson = {
  'id': 'a1b2',
  'created_at': '2026-11-20T10:00:00Z',
  'rating_count': 3,
  'ratings_needed': 7,
  'has_taste_profile': false,
  'taste_updated_at': null,
  'data_notice_required': true,
  'data_notice_accepted_at': null,
};

Future<ApiException> caught(Future<Object?> call) async {
  try {
    await call;
  } on ApiException catch (e) {
    return e;
  }
  fail('expected an ApiException');
}

void main() {
  group('token', () {
    test('is attached as a bearer token once set', () async {
      final t = make((_) async => json(meJson));
      t.client.accessToken = 'tok-123';
      await t.client.me();
      expect(t.adapter.requests.single.headers['Authorization'], 'Bearer tok-123');
      expect(t.adapter.requests.single.uri.toString(), 'https://api.test/me');
    });

    test('is absent signed out', () async {
      final t = make((_) async => json(meJson));
      await t.client.me();
      expect(t.adapter.requests.single.headers.containsKey('Authorization'), isFalse);
      t.client.accessToken = 'tok';
      t.client.accessToken = null;
      await t.client.me();
      expect(t.adapter.requests.last.headers.containsKey('Authorization'), isFalse);
    });
  });

  group('errors', () {
    test('404 maps to ApiException with the status, not retryable', () async {
      final t = make((_) async => text('{"detail":"Movie not found"}', 404));
      final e = await caught(t.client.getMovie(1));
      expect(e.status, 404);
      expect(e.isNotFound, isTrue);
      expect(e.retryable, isFalse);
      expect(e.message, contains('Movie not found'));
    });

    test('401 maps to ApiException 401', () async {
      final t = make((_) async => text('{"detail":"Invalid token"}', 401));
      final e = await caught(t.client.me());
      expect(e.status, 401);
      expect(e.isUnauthorized, isTrue);
    });

    test('5xx is retryable', () async {
      final t = make((_) async => text('', 503));
      final e = await caught(t.client.ratings());
      expect(e.status, 503);
      expect(e.retryable, isTrue);
    });

    for (final type in [
      DioExceptionType.connectionTimeout,
      DioExceptionType.receiveTimeout,
      DioExceptionType.sendTimeout,
    ]) {
      test('${type.name} is a retryable error with status 0', () async {
        final t = make((o) async => dioError(type, o));
        final e = await caught(t.client.recommendations(Lang.en));
        expect(e.status, 0);
        expect(e.retryable, isTrue);
        expect(e.message, contains('timeout'));
      });
    }

    test('no connection is retryable with status 0', () async {
      final t = make((o) async => dioError(DioExceptionType.connectionError, o));
      final e = await caught(t.client.watchlist());
      expect((e.status, e.retryable), (0, true));
    });

    test('a GET whose connection failed is sent once more, and that answer counts', () async {
      var calls = 0;
      final t = make((o) async {
        if (calls++ == 0) dioError(DioExceptionType.connectionError, o);
        return json(<Object>[]);
      });
      expect(await t.client.watchlist(), isEmpty);
      expect(t.adapter.requests, hasLength(2));
    });

    test('a GET whose connection timed out is sent once more; two failures are an error',
        () async {
      final t = make((o) async => dioError(DioExceptionType.connectionTimeout, o));
      final e = await caught(t.client.recommendations(Lang.en));
      expect((e.status, e.retryable), (0, true));
      expect(t.adapter.requests, hasLength(2), reason: 'once more, not more');
    });

    test('a POST is never sent twice: it may have reached the server', () async {
      final t = make((o) async => dioError(DioExceptionType.connectionError, o));
      await caught(t.client.addToWatchlist(155));
      expect(t.adapter.requests, hasLength(1));
    });

    test('a GET that timed out while the answer was coming is not sent again', () async {
      final t = make((o) async => dioError(DioExceptionType.receiveTimeout, o));
      await caught(t.client.watchlist());
      expect(t.adapter.requests, hasLength(1));
    });

    test('the connection is given up after 5 s, not 15', () {
      expect(connectTimeoutDefault, const Duration(seconds: 5));
    });

    test('a body of the wrong shape is an ApiException, not a crash', () async {
      final t = make((_) async => json({'id': 'not a number', 'title': 3}));
      final e = await caught(t.client.getMovie(155));
      expect(e.message, contains('unexpected response'));
    });
  });

  group('requests', () {
    test('rate posts the body as JSON', () async {
      final t = make((_) async => json({
            'movie_id': 155,
            'score': 9.5,
            'liked_aspects': ['pace'],
            'rated_at': '2026-11-23T12:00:00Z',
          }));
      final rating = await t.client.rate(const RatingIn(movieId: 155, score: 9.5, likedAspects: ['pace']));
      final sent = t.adapter.requests.single;
      expect(sent.method, 'POST');
      expect(jsonDecode(sent.data as String), {
        'movie_id': 155,
        'score': 9.5,
        'liked_aspects': ['pace'],
      });
      expect(rating.score, 9.5);
    });

    test('204 resolves without a body', () async {
      final t = make((_) async => ResponseBody.fromString('', 204));
      await t.client.unrate(155);
      expect(t.adapter.requests.single.method, 'DELETE');
      expect(t.adapter.requests.single.uri.path, '/ratings/155');
    });

    test('search repeats `trait`, as api.ts does', () {
      const params = SearchParams(q: 'heat', yearFrom: 1990, traits: ['pace', 'humor'], traitMinimum: 60);
      expect(params.toQuery(), 'q=heat&year_from=1990&trait=pace%3A60&trait=humor%3A60&limit=40');
    });

    test('events are sent in the API shape', () async {
      final t = make((_) async => json({'recorded': 2}));
      final at = DateTime.utc(2026, 11, 23, 9);
      final recorded = await t.client.sendEvents([
        RecommendationEvent(clicked: false, at: at, movieId: 155, source: EventSource.forYou),
        OnboardingStepEvent(at: at, step: OnboardingStep.rate),
      ]);
      expect(recorded, 2);
      expect(jsonDecode(t.adapter.requests.single.data as String), {
        'events': [
          {
            'type': 'recommendation_shown',
            'at': '2026-11-23T09:00:00.000Z',
            'movie_id': 155,
            'source': 'for_you',
          },
          {'type': 'onboarding_step', 'at': '2026-11-23T09:00:00.000Z', 'step': 'rate'},
        ],
      });
    });
  });

  group('models', () {
    test('recommendations parse and skip an unknown section', () async {
      final t = make((_) async => json({
            'status': 'ok',
            'ratings_needed': 0,
            'sections': [
              {
                'key': 'for_you',
                'seed': null,
                'items': [
                  {
                    'movie': movieJson,
                    'match': 87.4,
                    'band': 'strong',
                    'named_traits': ['dark_tone'],
                    'trait_side': 'reason',
                    'explanation': null,
                  },
                ],
              },
              {'key': 'from_a_newer_api', 'seed': null, 'items': []},
            ],
          }));
      final r = await t.client.recommendations(Lang.uz);
      expect(t.adapter.requests.single.uri.query, 'lang=uz');
      expect(r.enoughData, isTrue);
      expect(r.sections.single.key, SectionKey.forYou);
      final item = r.sections.single.items.single;
      expect((item.movie.title, item.movie.year, item.match, item.band),
          ('The Dark Knight', 2008, 87.4, MatchBand.strong));
      expect(item.traitSide, TraitSide.reason);
    });

    test('me parses times and the data-notice flag', () async {
      final t = make((_) async => json(meJson));
      final me = await t.client.me();
      expect(me.createdAt, DateTime.utc(2026, 11, 20, 10));
      expect(me.dataNoticeRequired, isTrue);
      expect(me.dataNoticeAcceptedAt, isNull);
    });
  });

  group('assistant stream', () {
    test('readSse keeps an unfinished block and skips unknown events', () {
      const buffer = 'event: text\r\ndata: {"text":"Hi"}\r\n\r\n'
          'event: sparkle\ndata: {}\n\n'
          'event: followups\ndata: {"items":["More like this",3]}\n\n'
          'event: done\ndata: {';
      final read = readSse(buffer);
      expect(read.events, hasLength(2));
      expect((read.events[0] as AssistantText).text, 'Hi');
      expect((read.events[1] as AssistantFollowups).items, ['More like this']);
      expect(read.rest, 'event: done\ndata: {');
    });

    test('events arrive across chunks, the last without a trailing blank line', () async {
      final t = make((_) async => ResponseBody(
            Stream.fromIterable([
              'event: text\ndata: {"te',
              'xt":"Try Heat."}\n\nevent: card\ndata: ${jsonEncode({'movie': movieJson, 'match': 80, 'band': null})}\n\n',
              'event: done\ndata: {}',
            ].map((s) => Uint8List.fromList(utf8.encode(s)))),
            200,
          ));
      final events = await t.client
          .assistantChat(const AssistantChatIn(message: 'like Heat', lang: Lang.en))
          .toList();
      expect(events.map((e) => e.runtimeType),
          [AssistantText, AssistantCardEvent, AssistantDone]);
      expect((events[1] as AssistantCardEvent).card.movie.id, 155);
    });

    test('the daily cap is an AssistantLimitException', () async {
      final t = make((_) async => text(
          jsonEncode({'detail': 'limit', 'limit': 20, 'resets_at': '2026-11-24T00:00:00Z'}), 429));
      try {
        await t.client.assistantChat(const AssistantChatIn(message: 'hi', lang: Lang.en)).toList();
        fail('expected AssistantLimitException');
      } on AssistantLimitException catch (e) {
        expect((e.status, e.limit.limit), (429, 20));
        expect(e.limit.resetsAt, DateTime.utc(2026, 11, 24));
      }
    });
  });
}
