/// /assistant (FR-8). Mirrors apps/web/src/pages/Assistant.tsx: three starter prompts on
/// an empty conversation; the answer streams in as text and rows of film cards from the
/// engine; two or three follow-up chips after the last answer. Today's cap is a state of
/// the screen with its reset time, not a dialog. Four states: empty (starters), loading
/// (waiting for the first words), error (the answer failed, with Try again), content.
///
/// The tab shows only while the server offers the assistant (`/me` assistant_enabled, the
/// user's decision of 2026-11-24): off at the AI-free web launch (TZ 1.38) without a new APK.
///
/// Phone differences: the question field sits at the bottom, above the keyboard; New
/// conversation is in the top bar.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show ChangeNotifierProvider;
import 'package:material_ui/material_ui.dart';

import '../data/models.dart';
import '../state/app_state.dart';
import '../state/assistant_chat.dart';
import '../theme/tokens.dart';
import '../widgets/not_right.dart';
import 'feed_screen.dart' show CardRow, openRecommendation;
import 'profile_screen.dart' show ProfileButton;

const starters = ['assistant.starter.mind', 'assistant.starter.light', 'assistant.starter.dark'];

/// app.schemas.AssistantChatIn
const maxChars = 500;

/// The reset time in the viewer's clock: "05:00 AM" in English, "05:00" in Uzbek and
/// Russian (as Intl.DateTimeFormat with 2-digit hour and minute gives it on the web).
String resetTime(DateTime at, Lang lang) {
  final local = at.toLocal();
  String two(int n) => n.toString().padLeft(2, '0');
  if (lang != Lang.en) return '${two(local.hour)}:${two(local.minute)}';
  final h = local.hour % 12 == 0 ? 12 : local.hour % 12;
  return '${two(h)}:${two(local.minute)} ${local.hour < 12 ? 'AM' : 'PM'}';
}

/// One conversation per visit to the screen.
final assistantChatProvider = ChangeNotifierProvider.autoDispose<AssistantChat>((ref) =>
    AssistantChat(api: ref.watch(apiClientProvider), lang: ref.watch(langProvider)));

class AssistantScreen extends ConsumerStatefulWidget {
  const AssistantScreen({super.key});

  @override
  ConsumerState<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends ConsumerState<AssistantScreen> {
  final _draft = TextEditingController();
  final _scroll = ScrollController();

  @override
  void dispose() {
    _draft.dispose();
    _scroll.dispose();
    super.dispose();
  }

  /// Keep the newest words in view while they arrive.
  void _toEnd() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scroll.hasClients) _scroll.jumpTo(_scroll.position.maxScrollExtent);
      });

  void _send(AssistantChat chat) {
    if (chat.busy || chat.limit != null || _draft.text.trim().isEmpty) return;
    chat.ask(_draft.text);
    _draft.clear();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(stringsProvider);
    final chat = ref.watch(assistantChatProvider);
    final exchanges = chat.exchanges;
    final last = exchanges.lastOrNull;
    final limited = chat.limit != null;
    final reminder = ref.watch(meProvider).value?.dataNoticeRequired ?? false;
    _toEnd();

    final log = <Widget>[
      Text(s.t('assistant.lead'), style: const TextStyle(color: AppColors.muted)),
      if (reminder) ...[
        const SizedBox(height: AppSpacing.x2),
        Text(s.t('notice.assistantReminder'),
            key: const Key('assistant.reminder'),
            style: const TextStyle(fontSize: 12, color: AppColors.muted)),
      ],
      const SizedBox(height: AppSpacing.x3),
      if (exchanges.isEmpty) ...[
        Text(s.t('assistant.startersLabel').toUpperCase(),
            style: const TextStyle(
                fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.9, color: AppColors.muted)),
        const SizedBox(height: AppSpacing.x2),
        for (final key in starters)
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x2),
            child: OutlinedButton(
              key: Key('assistant.starter.$key'),
              style: OutlinedButton.styleFrom(
                alignment: Alignment.centerLeft,
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3, vertical: 12),
              ),
              onPressed: () => chat.ask(s.t(key)),
              child: Text(s.t(key)),
            ),
          ),
      ] else
        for (final e in exchanges) ...[
          _Question(text: e.question),
          const SizedBox(height: AppSpacing.x2),
          Semantics(
            label: s.t('assistant.answer'),
            liveRegion: true,
            child: _Answer(
              exchange: e,
              onRetry: identical(e, last) && chat.retryable != null
                  ? () => chat.ask(e.question)
                  : null,
            ),
          ),
          const SizedBox(height: AppSpacing.x4),
        ],
      if (last != null &&
          last.status == ExchangeStatus.done &&
          last.followups.isNotEmpty &&
          !limited)
        Semantics(
          container: true,
          label: s.t('assistant.followupsLabel'),
          child: Wrap(
            spacing: AppSpacing.x2,
            runSpacing: AppSpacing.x2,
            children: [
              for (final q in last.followups)
                ActionChip(label: Text(q), onPressed: () => chat.ask(q)),
            ],
          ),
        ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('assistant.title')),
        actions: [
          if (exchanges.isNotEmpty)
            IconButton(
              tooltip: s.t('assistant.newConversation'),
              icon: const Icon(Icons.restart_alt),
              onPressed: chat.restart,
            ),
          const ProfileButton(),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              controller: _scroll,
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              padding: const EdgeInsets.fromLTRB(0, AppSpacing.x3, 0, AppSpacing.x3),
              children: [
                // The card rows run edge to edge; everything else has the page margin.
                for (final w in log)
                  w is _Answer || (w is Semantics && w.child is _Answer)
                      ? w
                      : Padding(
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3),
                          child: w,
                        ),
              ],
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.x3, AppSpacing.x2, AppSpacing.x3, AppSpacing.x2),
              child: Row(children: [
                Expanded(
                  child: TextField(
                    key: const Key('assistant.input'),
                    controller: _draft,
                    enabled: !limited,
                    maxLength: maxChars,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    onTap: chat.warm,
                    onChanged: (_) {
                      chat.warm();
                      setState(() {});
                    },
                    onSubmitted: (_) => _send(chat),
                    decoration: InputDecoration(
                      hintText: s.t('assistant.placeholder'),
                      labelText: s.t('assistant.inputLabel'),
                      floatingLabelBehavior: FloatingLabelBehavior.never,
                      counterText: '',
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.x2),
                IconButton.filled(
                  key: const Key('assistant.send'),
                  tooltip: s.t('assistant.send'),
                  onPressed: chat.busy || limited || _draft.text.trim().isEmpty
                      ? null
                      : () => _send(chat),
                  icon: const Icon(Icons.send),
                ),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _Question extends ConsumerWidget {
  const _Question({required this.text});
  final String text;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Align(
        alignment: Alignment.centerRight,
        child: Semantics(
          label: '${ref.watch(stringsProvider).t('assistant.you')}: $text',
          excludeSemantics: true,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: AppColors.surface2,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              child: Text(text),
            ),
          ),
        ),
      );
}

class _Answer extends ConsumerWidget {
  const _Answer({required this.exchange, this.onRetry});

  final Exchange exchange;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(stringsProvider);
    final hidden = ref.watch(hiddenCardsProvider); // "Not right?" takes a card out of view
    Widget pad(Widget child) =>
        Padding(padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3), child: child);

    switch (exchange.status) {
      case ExchangeStatus.waiting:
        return pad(Row(
          key: const Key('assistant.thinking'),
          children: [
            if (!MediaQuery.disableAnimationsOf(context)) ...[
              const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.muted),
              ),
              const SizedBox(width: AppSpacing.x2),
            ],
            Flexible(
              child: Text(s.t('assistant.thinking'), style: const TextStyle(color: AppColors.muted)),
            ),
          ],
        ));
      case ExchangeStatus.refused:
        return pad(Text(s.t(exchange.refusal == AssistantRefusalReason.leak
            ? 'assistant.leak'
            : 'assistant.offTopic')));
      case ExchangeStatus.limit:
        final limit = exchange.limit!;
        return pad(Text(
          s.t('assistant.limit', {'n': limit.limit, 'time': resetTime(limit.resetsAt, s.lang)}),
          key: const Key('assistant.limit'),
          style: const TextStyle(color: AppColors.gold),
        ));
      case ExchangeStatus.streaming:
      case ExchangeStatus.done:
      case ExchangeStatus.failed:
        break;
    }

    final error = exchange.error;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final part in exchange.parts)
          switch (part) {
            TextPart(:final text) => pad(Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: Text(text.trim(), style: const TextStyle(height: 1.5)),
              )),
            CardsPart(:final cards) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: CardRow(
                  items: [
                    for (final c in cards)
                      if (!hidden.contains(c.movie.id))
                        Recommendation(movie: c.movie, match: c.match, band: c.band),
                  ],
                  source: EventSource.assistant,
                  onOpen: (movie) => openRecommendation(context, ref, movie, EventSource.assistant),
                ),
              ),
          },
        if (exchange.status == ExchangeStatus.failed)
          pad(Semantics(
            liveRegion: true,
            child: Column(
              key: const Key('assistant.error'),
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(s.t(switch (error) {
                  ExchangeError.blocked => 'assistant.blocked',
                  ExchangeError.timeout => 'assistant.busy',
                  _ => 'assistant.failed',
                })),
                if (onRetry != null && error != ExchangeError.blocked) ...[
                  const SizedBox(height: AppSpacing.x2),
                  OutlinedButton(onPressed: onRetry, child: Text(s.t('common.retry'))),
                ],
              ],
            ),
          )),
      ],
    );
  }
}
