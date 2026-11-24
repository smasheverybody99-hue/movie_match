/// /search — title, year, runtime and trait filters. Mirrors apps/web/src/pages/Search.tsx:
/// popular films before anything is typed, one request per pause in typing (250 ms), the
/// previous results stay while the next ones load. Streaming providers are not offered:
/// the catalogue has no provider data yet.
///
/// Phone differences: the filters fold under "Filters" (as on the web below 900 px); the
/// keyboard closes when the results are scrolled; no quick Rate / Save on the tiles.
library;

import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../data/api_client.dart';
import '../data/models.dart';
import '../data/traits.dart';
import '../state/app_state.dart';
import '../theme/tokens.dart';
import '../widgets/film_tile.dart';
import '../widgets/states.dart';
import 'profile_screen.dart' show ProfileButton;

const runtimes = [90, 120, 150];

/// "Strong in X" means the film scores at least this on X — the design's strong band.
const strongTrait = 70;

/// One request per pause in typing, not per key.
const searchDelay = Duration(milliseconds: 250);

class SearchFilters {
  const SearchFilters({this.yearFrom = '', this.yearTo = '', this.maxRuntime, this.traits = const []});

  final String yearFrom;
  final String yearTo;
  final int? maxRuntime;
  final List<String> traits;

  bool get any => yearFrom.isNotEmpty || yearTo.isNotEmpty || maxRuntime != null || traits.isNotEmpty;

  SearchFilters copyWith({String? yearFrom, String? yearTo, int? Function()? maxRuntime, List<String>? traits}) =>
      SearchFilters(
        yearFrom: yearFrom ?? this.yearFrom,
        yearTo: yearTo ?? this.yearTo,
        maxRuntime: maxRuntime == null ? this.maxRuntime : maxRuntime(),
        traits: traits ?? this.traits,
      );
}

int? _year(String value) {
  final n = int.tryParse(value);
  return value.length == 4 && n != null && n >= 1870 && n <= 2100 ? n : null;
}

/// The request for what is typed and chosen (web: toParams).
SearchParams toParams(String q, SearchFilters f) => SearchParams(
      q: q.trim().isEmpty ? null : q.trim(),
      yearFrom: _year(f.yearFrom),
      yearTo: _year(f.yearTo),
      maxRuntime: f.maxRuntime,
      traits: f.traits,
      traitMinimum: strongTrait,
    );

final searchProvider = FutureProvider.autoDispose.family<List<Movie>, SearchParams>(
    (ref, params) => ref.watch(apiClientProvider).searchMovies(params));

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _q = TextEditingController();
  final _yearFrom = TextEditingController();
  final _yearTo = TextEditingController();
  String _typed = '';
  SearchFilters _filters = const SearchFilters();
  Timer? _debounce;

  /// The last results shown: they stay while the next ones load (web: keepPreviousData).
  List<Movie>? _last;

  @override
  void dispose() {
    _debounce?.cancel();
    _q.dispose();
    _yearFrom.dispose();
    _yearTo.dispose();
    super.dispose();
  }

  void _onTyped(String text) {
    _debounce?.cancel();
    _debounce = Timer(searchDelay, () {
      if (mounted) setState(() => _typed = text);
    });
  }

  void _setFilters(SearchFilters f) => setState(() => _filters = f);

  void _clear() {
    _debounce?.cancel();
    _q.clear();
    _yearFrom.clear();
    _yearTo.clear();
    setState(() {
      _typed = '';
      _filters = const SearchFilters();
    });
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final params = toParams(_typed, _filters);
    final query = ref.watch(searchProvider(params));
    final idle = params.q == null && !_filters.any;
    if (query.hasValue) _last = query.value;
    final shown = query.value ?? (query.isLoading ? _last : null);

    final Widget results;
    if (shown != null) {
      results = shown.isEmpty
          ? SliverFillRemaining(
              hasScrollBody: false,
              child: EmptyState(
                message: s.t('search.empty'),
                actionLabel: s.t('search.clear'),
                onAction: _clear,
              ),
            )
          : _Grid(movies: shown);
    } else if (query.hasError) {
      results = SliverFillRemaining(
        hasScrollBody: false,
        child: ErrorState(
          message: s.t('search.error'),
          onRetry: () => ref.invalidate(searchProvider(params)),
        ),
      );
    } else {
      results = const _GridSkeleton();
    }

    return Scaffold(
      appBar: AppBar(title: Text(s.t('search.title')), actions: const [ProfileButton()]),
      body: CustomScrollView(
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x2, AppSpacing.x3, 0),
            sliver: SliverToBoxAdapter(
              child: TextField(
                key: const Key('search.q'),
                controller: _q,
                onChanged: _onTyped,
                textInputAction: TextInputAction.search,
                decoration: InputDecoration(
                  hintText: s.t('search.placeholder'),
                  labelText: s.t('search.label'),
                  floatingLabelBehavior: FloatingLabelBehavior.never,
                  prefixIcon: const Icon(Icons.search, color: AppColors.muted),
                ),
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: _FilterPanel(
              filters: _filters,
              yearFrom: _yearFrom,
              yearTo: _yearTo,
              onChanged: _setFilters,
              onClear: _clear,
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x2, AppSpacing.x3, 12),
            sliver: SliverToBoxAdapter(
              child: Row(children: [
                Expanded(
                  child: Semantics(
                    header: true,
                    child: Text(idle ? s.t('search.popular') : s.t('search.results'),
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                  ),
                ),
                if (query.isLoading && shown != null)
                  const SizedBox(
                    key: Key('search.busy'),
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.muted),
                  ),
              ]),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x4),
            sliver: results,
          ),
        ],
      ),
    );
  }
}

class _FilterPanel extends ConsumerWidget {
  const _FilterPanel({
    required this.filters,
    required this.yearFrom,
    required this.yearTo,
    required this.onChanged,
    required this.onClear,
  });

  final SearchFilters filters;
  final TextEditingController yearFrom;
  final TextEditingController yearTo;
  final ValueChanged<SearchFilters> onChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    Widget year(TextEditingController c, String label, String key, void Function(String) set) =>
        Expanded(
          child: TextField(
            key: Key(key),
            controller: c,
            keyboardType: TextInputType.number,
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(4),
            ],
            decoration: InputDecoration(hintText: label, labelText: label),
            onChanged: set,
          ),
        );
    return Theme(
      // No divider lines above and below the open panel.
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        key: const Key('search.filters'),
        title: Text(s.t('search.filters')),
        tilePadding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3),
        childrenPadding: const EdgeInsets.fromLTRB(AppSpacing.x3, 0, AppSpacing.x3, AppSpacing.x2),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            year(yearFrom, s.t('search.yearFrom'), 'search.yearFrom',
                (v) => onChanged(filters.copyWith(yearFrom: v))),
            const SizedBox(width: AppSpacing.x2),
            year(yearTo, s.t('search.yearTo'), 'search.yearTo',
                (v) => onChanged(filters.copyWith(yearTo: v))),
          ]),
          const SizedBox(height: AppSpacing.x3),
          DropdownButtonFormField<int?>(
            key: const Key('search.runtime'),
            initialValue: filters.maxRuntime,
            isExpanded: true,
            decoration: InputDecoration(labelText: s.t('search.runtime')),
            items: [
              DropdownMenuItem(value: null, child: Text(s.t('search.runtimeAny'))),
              for (final n in runtimes)
                DropdownMenuItem(value: n, child: Text(s.t('search.runtimeUpTo', {'n': n}))),
            ],
            onChanged: (v) => onChanged(filters.copyWith(maxRuntime: () => v)),
          ),
          const SizedBox(height: AppSpacing.x3),
          Text(s.t('search.traits'), style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: AppSpacing.x2),
          Wrap(
            spacing: AppSpacing.x2,
            runSpacing: AppSpacing.x2,
            children: [
              for (final key in traitKeys)
                FilterChip(
                  label: Text(s.t(traitLabelKey(key))),
                  selected: filters.traits.contains(key),
                  onSelected: (on) => onChanged(filters.copyWith(
                      traits: on ? [...filters.traits, key] : [for (final k in filters.traits) if (k != key) k])),
                ),
            ],
          ),
          if (filters.any) ...[
            const SizedBox(height: AppSpacing.x2),
            TextButton(onPressed: onClear, child: Text(s.t('search.clear'))),
          ],
        ],
      ),
    );
  }
}

class _Grid extends StatelessWidget {
  const _Grid({required this.movies});

  final List<Movie> movies;

  @override
  Widget build(BuildContext context) => SliverLayoutBuilder(builder: (context, constraints) {
        final width = constraints.crossAxisExtent;
        final columns = gridColumns(width);
        final tileWidth = (width - (columns - 1) * 10) / columns;
        return SliverGrid(
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: columns,
            crossAxisSpacing: 10,
            mainAxisSpacing: AppSpacing.x3,
            mainAxisExtent: FilmTile.heightFor(context, tileWidth),
          ),
          delegate: SliverChildBuilderDelegate(
            (context, i) => FilmTile(key: ValueKey(movies[i].id), movie: movies[i]),
            childCount: movies.length,
          ),
        );
      });
}

class _GridSkeleton extends ConsumerWidget {
  const _GridSkeleton();

  @override
  Widget build(BuildContext context, WidgetRef ref) => SliverLayoutBuilder(
        key: const Key('search.skeleton'),
        builder: (context, constraints) {
          final columns = gridColumns(constraints.crossAxisExtent);
          return SliverGrid(
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: columns,
              crossAxisSpacing: 10,
              mainAxisSpacing: AppSpacing.x3,
              childAspectRatio: 2 / 3,
            ),
            delegate: SliverChildBuilderDelegate(
              (context, i) => Semantics(
                label: i == 0 ? ref.watch(stringsProvider).t('common.loading') : null,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: AppColors.surface2,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                ),
              ),
              childCount: 12,
            ),
          );
        },
      );
}
