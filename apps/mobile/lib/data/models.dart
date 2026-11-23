/// API models. They mirror services/api/app/schemas.py by hand, as
/// apps/web/src/lib/types.ts does. When a Pydantic schema changes, change schemas.py,
/// types.ts and this file in the same commit. All models live here so drift is visible.
library;

typedef Json = Map<String, dynamic>;

/// A response that does not have the expected shape (a field missing or of the wrong
/// type). The client turns it into an ApiException.
class FormatError implements Exception {
  const FormatError(this.message);
  final String message;
  @override
  String toString() => 'FormatError: $message';
}

T _field<T>(Json json, String key) {
  final value = json[key];
  if (value is T) return value;
  throw FormatError('"$key" is ${value.runtimeType}, expected $T');
}

Json _object(Object? value, String what) {
  if (value is Map<String, dynamic>) return value;
  throw FormatError('$what is ${value.runtimeType}, expected an object');
}

List<Json> _objects(Json json, String key) =>
    _field<List<dynamic>>(json, key).map((e) => _object(e, key)).toList();

List<String> _strings(Json json, String key) => _field<List<dynamic>>(json, key).cast<String>();

Map<String, int> _scores(Json json, String key) => {
      for (final e in _object(json[key], key).entries) e.key: (e.value as num).round(),
    };

double? _number(Json json, String key) => (_field<num?>(json, key))?.toDouble();

DateTime _time(Json json, String key) => DateTime.parse(_field<String>(json, key));

DateTime? _timeOrNull(Json json, String key) {
  final value = _field<String?>(json, key);
  return value == null ? null : DateTime.parse(value);
}

/// An enum value by its wire name; null for null and for a name this client does not know
/// (a newer API may add values).
E? _wire<E extends Enum>(List<E> values, Object? name, String Function(E) wireOf) {
  for (final value in values) {
    if (wireOf(value) == name) return value;
  }
  return null;
}

// --- shared enums ---------------------------------------------------------------------

/// Mirrors app.schemas.Lang. English is the default (TZ 1.8).
enum Lang { en, uz, ru }

/// FR-5, TZ 1.13: one of the user's N closest films, or in their closest share.
enum MatchBand { strong, good }

/// FR-5, TZ 1.27: which side the named traits fall on.
enum TraitSide { reason, difference }

enum SectionKey {
  forYou('for_you'),
  becauseYouLoved('because_you_loved'),
  under90('under_90'),
  outsideUsual('outside_usual');

  const SectionKey(this.wire);
  final String wire;
}

MatchBand? _band(Json json) => _wire(MatchBand.values, json['band'], (e) => e.name);
TraitSide? _side(Json json) => _wire(TraitSide.values, json['trait_side'], (e) => e.name);

// --- films ----------------------------------------------------------------------------

class Movie {
  const Movie({
    required this.id,
    required this.title,
    this.releaseDate,
    this.runtimeMinutes,
    this.overview,
    this.posterPath,
    this.backdropPath,
    this.genres = const [],
  });

  factory Movie.fromJson(Json json) => Movie(
        id: _field<int>(json, 'id'),
        title: _field<String>(json, 'title'),
        releaseDate: _field<String?>(json, 'release_date'),
        runtimeMinutes: _field<int?>(json, 'runtime_minutes'),
        overview: _field<String?>(json, 'overview'),
        posterPath: _field<String?>(json, 'poster_path'),
        backdropPath: _field<String?>(json, 'backdrop_path'),
        genres: _strings(json, 'genres'),
      );

  final int id;
  final String title;

  /// ISO date as the API sends it (`YYYY-MM-DD`).
  final String? releaseDate;
  final int? runtimeMinutes;
  final String? overview;
  final String? posterPath;
  final String? backdropPath;

  /// TMDB's names, alphabetical.
  final List<String> genres;

  int? get year => releaseDate == null ? null : int.tryParse(releaseDate!.split('-').first);
}

class TraitScores {
  const TraitScores({required this.scores, this.summary});

  factory TraitScores.fromJson(Json json) =>
      TraitScores(scores: _scores(json, 'scores'), summary: _field<String?>(json, 'summary'));

  /// Trait key -> 0-100.
  final Map<String, int> scores;
  final String? summary;
}

class MovieDetail extends Movie {
  const MovieDetail({
    required super.id,
    required super.title,
    super.releaseDate,
    super.runtimeMinutes,
    super.overview,
    super.posterPath,
    super.backdropPath,
    super.genres,
    this.traits,
    this.director,
    this.cast = const [],
    this.match,
    this.band,
    this.namedTraits = const [],
    this.traitSide,
    this.sensitive = false,
  });

  factory MovieDetail.fromJson(Json json) {
    final movie = Movie.fromJson(json);
    final traits = json['traits'];
    return MovieDetail(
      id: movie.id,
      title: movie.title,
      releaseDate: movie.releaseDate,
      runtimeMinutes: movie.runtimeMinutes,
      overview: movie.overview,
      posterPath: movie.posterPath,
      backdropPath: movie.backdropPath,
      genres: movie.genres,
      traits: traits == null ? null : TraitScores.fromJson(_object(traits, 'traits')),
      director: _field<String?>(json, 'director'),
      cast: _strings(json, 'cast'),
      match: _number(json, 'match'),
      band: _band(json),
      namedTraits: _strings(json, 'named_traits'),
      traitSide: _side(json),
      sensitive: _field<bool>(json, 'sensitive'),
    );
  }

  final TraitScores? traits;
  final String? director;
  final List<String> cast;

  /// The caller's match (FR-5); null signed out, or without traits or taste. Not shown.
  final double? match;
  final MatchBand? band;

  /// Trait keys worth naming, strongest first.
  final List<String> namedTraits;
  final TraitSide? traitSide;

  /// Explicit or extreme: in no list, and the page warns before it shows (Phase 5).
  final bool sensitive;
}

// --- recommendations -------------------------------------------------------------------

class Recommendation {
  const Recommendation({
    required this.movie,
    required this.match,
    this.band,
    this.namedTraits = const [],
    this.traitSide,
    this.explanation,
  });

  factory Recommendation.fromJson(Json json) => Recommendation(
        movie: Movie.fromJson(_object(json['movie'], 'movie')),
        match: _number(json, 'match')!,
        band: _band(json),
        namedTraits: _strings(json, 'named_traits'),
        traitSide: _side(json),
        explanation: _field<String?>(json, 'explanation'),
      );

  final Movie movie;

  /// 0-100, from trait distance. Not shown.
  final double match;
  final MatchBand? band;
  final List<String> namedTraits;
  final TraitSide? traitSide;
  final String? explanation;
}

class Section {
  const Section({required this.key, this.seed, required this.items});

  /// Null when the API sends a section this client does not know; the feed skips it.
  static Section? fromJson(Json json) {
    final key = _wire(SectionKey.values, json['key'], (e) => e.wire);
    if (key == null) return null;
    final seed = json['seed'];
    return Section(
      key: key,
      seed: seed == null ? null : Movie.fromJson(_object(seed, 'seed')),
      items: _objects(json, 'items').map(Recommendation.fromJson).toList(),
    );
  }

  final SectionKey key;

  /// The film in "Because you loved {film}"; null otherwise.
  final Movie? seed;
  final List<Recommendation> items;
}

class Recommendations {
  const Recommendations({
    required this.enoughData,
    required this.ratingsNeeded,
    required this.sections,
  });

  factory Recommendations.fromJson(Json json) {
    final status = _field<String>(json, 'status');
    if (status != 'ok' && status != 'not_enough_data') {
      throw FormatError('unknown status "$status"');
    }
    return Recommendations(
      enoughData: status == 'ok',
      ratingsNeeded: _field<int>(json, 'ratings_needed'),
      sections: [
        for (final s in _objects(json, 'sections')) ?Section.fromJson(s),
      ],
    );
  }

  /// `status` is "ok"; false for "not_enough_data".
  final bool enoughData;
  final int ratingsNeeded;
  final List<Section> sections;
}

/// Why an explanation has no text. Mirrors app/schemas.py ExplanationReason.
enum ExplanationReason {
  noGenerator('no_generator'),
  dailyCap('daily_cap'),
  noTaste('no_taste'),
  noTraits('no_traits'),
  nothingNamed('nothing_named'),
  failed('failed'),
  rejected('rejected');

  const ExplanationReason(this.wire);
  final String wire;
}

class Explanation {
  const Explanation({required this.movieId, required this.lang, this.text, this.reason});

  factory Explanation.fromJson(Json json) => Explanation(
        movieId: _field<int>(json, 'movie_id'),
        lang: _wire(Lang.values, json['lang'], (e) => e.name) ?? Lang.en,
        text: _field<String?>(json, 'text'),
        reason: _wire(ExplanationReason.values, json['reason'], (e) => e.wire),
      );

  final int movieId;
  final Lang lang;
  final String? text;
  final ExplanationReason? reason;
}

// --- the user --------------------------------------------------------------------------

class MovieDna {
  const MovieDna({
    required this.scores,
    this.summary,
    required this.ratingCount,
    required this.ratingsNeeded,
    this.averageRating,
    this.topGenre,
  });

  factory MovieDna.fromJson(Json json) => MovieDna(
        scores: _scores(json, 'scores'),
        summary: _field<String?>(json, 'summary'),
        ratingCount: _field<int>(json, 'rating_count'),
        ratingsNeeded: _field<int>(json, 'ratings_needed'),
        averageRating: _number(json, 'average_rating'),
        topGenre: _field<String?>(json, 'top_genre'),
      );

  /// The taste vector by trait key, 0-100. Empty until a scored film is liked.
  final Map<String, int> scores;
  final String? summary;
  final int ratingCount;
  final int ratingsNeeded;
  final double? averageRating;
  final String? topGenre;
}

class Me {
  const Me({
    required this.id,
    required this.createdAt,
    required this.ratingCount,
    required this.ratingsNeeded,
    required this.hasTasteProfile,
    this.tasteUpdatedAt,
    required this.dataNoticeRequired,
    this.dataNoticeAcceptedAt,
  });

  factory Me.fromJson(Json json) => Me(
        id: _field<String>(json, 'id'),
        createdAt: _time(json, 'created_at'),
        ratingCount: _field<int>(json, 'rating_count'),
        ratingsNeeded: _field<int>(json, 'ratings_needed'),
        hasTasteProfile: _field<bool>(json, 'has_taste_profile'),
        tasteUpdatedAt: _timeOrNull(json, 'taste_updated_at'),
        dataNoticeRequired: _field<bool>(json, 'data_notice_required'),
        dataNoticeAcceptedAt: _timeOrNull(json, 'data_notice_accepted_at'),
      );

  final String id;
  final DateTime createdAt;
  final int ratingCount;
  final int ratingsNeeded;
  final bool hasTasteProfile;
  final DateTime? tasteUpdatedAt;

  /// Show the data notice until it is accepted (ADR 0004, the alpha).
  final bool dataNoticeRequired;
  final DateTime? dataNoticeAcceptedAt;
}

class RatingIn {
  const RatingIn({required this.movieId, required this.score, this.likedAspects});

  final int movieId;

  /// 0.5 .. 10.0
  final double score;

  /// Trait keys, no repeats.
  final List<String>? likedAspects;

  Json toJson() => {
        'movie_id': movieId,
        'score': score,
        if (likedAspects != null) 'liked_aspects': likedAspects,
      };
}

class Rating {
  const Rating({
    required this.movieId,
    required this.score,
    this.likedAspects = const [],
    required this.ratedAt,
  });

  factory Rating.fromJson(Json json) => Rating(
        movieId: _field<int>(json, 'movie_id'),
        score: _number(json, 'score')!,
        likedAspects: _strings(json, 'liked_aspects'),
        ratedAt: _time(json, 'rated_at'),
      );

  final int movieId;
  final double score;
  final List<String> likedAspects;
  final DateTime ratedAt;
}

class WatchlistItem {
  const WatchlistItem({
    required this.movie,
    required this.addedAt,
    this.watchedAt,
    this.match,
    this.band,
  });

  factory WatchlistItem.fromJson(Json json) => WatchlistItem(
        movie: Movie.fromJson(_object(json['movie'], 'movie')),
        addedAt: _time(json, 'added_at'),
        watchedAt: _timeOrNull(json, 'watched_at'),
        match: _number(json, 'match'),
        band: _band(json),
      );

  final Movie movie;
  final DateTime addedAt;
  final DateTime? watchedAt;

  /// Null without traits or taste. Not shown.
  final double? match;
  final MatchBand? band;
}

class Health {
  const Health({required this.status, required this.traitDimensions, this.commit});

  factory Health.fromJson(Json json) => Health(
        status: _field<String>(json, 'status'),
        traitDimensions: _field<int>(json, 'trait_dimensions'),
        commit: _field<String?>(json, 'commit'),
      );

  final String status;
  final int traitDimensions;
  final String? commit;
}

// --- closed alpha (Phase 5) ------------------------------------------------------------

/// Where a recommendation was shown. Mirrors app.services.events.Source.
enum EventSource {
  forYou('for_you'),
  becauseYouLoved('because_you_loved'),
  under90('under_90'),
  outsideUsual('outside_usual'),
  assistant('assistant');

  const EventSource(this.wire);
  final String wire;

  static EventSource fromSection(SectionKey key) =>
      EventSource.values.firstWhere((e) => e.wire == key.wire);
}

enum OnboardingStep { pick, rate, done }

/// One event the client sends (POST /events). Mirrors app.schemas.EventIn.
sealed class ClientEvent {
  const ClientEvent(this.at);
  final DateTime at;
  Json toJson();
}

class RecommendationEvent extends ClientEvent {
  const RecommendationEvent({
    required this.clicked,
    required DateTime at,
    required this.movieId,
    required this.source,
  }) : super(at);

  /// `recommendation_clicked` when true, `recommendation_shown` otherwise.
  final bool clicked;
  final int movieId;
  final EventSource source;

  @override
  Json toJson() => {
        'type': clicked ? 'recommendation_clicked' : 'recommendation_shown',
        'at': at.toUtc().toIso8601String(),
        'movie_id': movieId,
        'source': source.wire,
      };
}

class OnboardingStepEvent extends ClientEvent {
  const OnboardingStepEvent({required DateTime at, required this.step}) : super(at);

  final OnboardingStep step;

  @override
  Json toJson() => {
        'type': 'onboarding_step',
        'at': at.toUtc().toIso8601String(),
        'step': step.name,
      };
}

/// The four chips under "Not right?". Mirrors app.services.feedback.Reason.
enum FeedbackReason {
  seen('seen'),
  notMyGenre('not_my_genre'),
  tooOld('too_old'),
  other('other');

  const FeedbackReason(this.wire);
  final String wire;
}

/// POST /feedback. Mirrors app.schemas.FeedbackIn.
class FeedbackIn {
  const FeedbackIn({required this.movieId, required this.source, this.reason});

  final int movieId;
  final EventSource source;
  final FeedbackReason? reason;

  Json toJson() => {'movie_id': movieId, 'source': source.wire, 'reason': reason?.wire};
}

// --- assistant (FR-8): POST /assistant/chat, a Server-Sent Events stream --------------

/// Mirrors app.schemas.AssistantChatIn.
class AssistantChatIn {
  const AssistantChatIn({required this.message, required this.lang, this.newConversation});

  /// 1-500 characters, not blank.
  final String message;
  final Lang lang;

  /// Forget the earlier turns before this message.
  final bool? newConversation;

  Json toJson() => {
        'message': message,
        'lang': lang.name,
        if (newConversation != null) 'new_conversation': newConversation,
      };
}

/// A film inside an answer (event `card`). Mirrors app.schemas.AssistantCardOut.
class AssistantCard {
  const AssistantCard({required this.movie, required this.match, this.band});

  factory AssistantCard.fromJson(Json json) => AssistantCard(
        movie: Movie.fromJson(_object(json['movie'], 'movie')),
        match: _number(json, 'match')!,
        band: _band(json),
      );

  final Movie movie;
  final double match;
  final MatchBand? band;
}

/// The 429 body when the day's messages are used up. Mirrors app.schemas.AssistantLimitOut.
class AssistantLimit {
  const AssistantLimit({required this.detail, required this.limit, required this.resetsAt});

  /// Null when the body is not a limit (any other 429).
  static AssistantLimit? tryParse(Object? body) {
    if (body is! Map<String, dynamic>) return null;
    final limit = body['limit'];
    final resets = body['resets_at'];
    if (limit is! int || resets is! String) return null;
    final at = DateTime.tryParse(resets);
    if (at == null) return null;
    return AssistantLimit(detail: '${body['detail'] ?? ''}', limit: limit, resetsAt: at);
  }

  final String detail;
  final int limit;

  /// The next UTC midnight.
  final DateTime resetsAt;
}

enum AssistantRefusalReason { offTopic, leak }

/// `timeout`: the answer did not come in time; the client says the assistant is busy.
enum AssistantErrorReason { failed, blocked, timeout }

/// One event of the stream, in the order the API sends them (app/routers/assistant.py).
sealed class AssistantEvent {
  const AssistantEvent();

  /// One SSE block as an event, or null for anything this client does not know: a newer
  /// API may add events, and an old client skips them. Mirrors toAssistantEvent in api.ts.
  static AssistantEvent? parse(String name, Object? data) {
    if (data is! Map<String, dynamic>) return null;
    switch (name) {
      case 'text':
        final text = data['text'];
        return text is String ? AssistantText(text) : null;
      case 'card':
        if (data['movie'] is! Map<String, dynamic> || data['match'] is! num) return null;
        try {
          return AssistantCardEvent(AssistantCard.fromJson(data));
        } on FormatError {
          return null;
        }
      case 'followups':
        final items = data['items'];
        return items is List ? AssistantFollowups(items.whereType<String>().toList()) : null;
      case 'refusal':
        return switch (data['reason']) {
          'off_topic' => const AssistantRefusal(AssistantRefusalReason.offTopic),
          'leak' => const AssistantRefusal(AssistantRefusalReason.leak),
          _ => null,
        };
      case 'error':
        return AssistantError(switch (data['reason']) {
          'blocked' => AssistantErrorReason.blocked,
          'timeout' => AssistantErrorReason.timeout,
          _ => AssistantErrorReason.failed,
        });
      case 'reset':
        return const AssistantReset();
      case 'done':
        return const AssistantDone();
      default:
        return null;
    }
  }
}

class AssistantText extends AssistantEvent {
  const AssistantText(this.text);
  final String text;
}

class AssistantCardEvent extends AssistantEvent {
  const AssistantCardEvent(this.card);
  final AssistantCard card;
}

class AssistantFollowups extends AssistantEvent {
  const AssistantFollowups(this.items);
  final List<String> items;
}

class AssistantRefusal extends AssistantEvent {
  const AssistantRefusal(this.reason);
  final AssistantRefusalReason reason;
}

class AssistantError extends AssistantEvent {
  const AssistantError(this.reason);
  final AssistantErrorReason reason;
}

/// A model call broke off and runs again: drop what this answer showed.
class AssistantReset extends AssistantEvent {
  const AssistantReset();
}

class AssistantDone extends AssistantEvent {
  const AssistantDone();
}
