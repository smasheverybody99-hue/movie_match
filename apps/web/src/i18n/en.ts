/**
 * English strings: the default language and the source dictionary (TZ 1.8). `uz.ts` and
 * `ru.ts` must have exactly these keys (TypeScript checks it at build time,
 * `i18n.test.ts` at test time).
 *
 * `{name}` placeholders are filled by `t(key, { name })`. A message that depends on a
 * count is a `Plural`: one form per CLDR plural category of the language, chosen by
 * `Intl.PluralRules` from `{n}` (English: one, other; Russian: one, few, many, other).
 * Trait labels (`trait.*`) are copied from packages/shared/traits.json; the test fails
 * if they drift.
 */
export interface Plural {
  zero?: string;
  one?: string;
  two?: string;
  few?: string;
  many?: string;
  other: string;
}
export type Message = string | Plural;

export const en = {
  "app.name": "Movie Match",
  "app.loadingPage": "Loading the page",

  "nav.label": "Main sections",
  "nav.home": "Home",
  "nav.search": "Search",
  "nav.dna": "Movie DNA",
  "nav.watchlist": "Watchlist",
  "nav.profile": "Profile",
  "nav.back": "Back",
  "nav.skipToContent": "Skip to main content",

  "common.retry": "Try again",
  "common.offline": "Offline. Showing saved content.",
  "common.offlineNoCache":
    "You're offline and this page hasn't been saved yet. Try again once you're connected.",
  "common.close": "Close",
  "common.cancel": "Cancel",
  "common.save": "Save",
  "common.minutes": "{n}m",
  "common.matchBadge": "{n}%",
  "common.matchLabel": "{n}% match",
  "common.poster": "Poster for {title}",
  "common.matchWord": "MATCH",
  "common.loading": "Loading",

  "welcome.tagline":
    "Find movies based on what you actually love — not just what everyone watched.",
  "welcome.google": "Continue with Google",
  "welcome.apple": "Continue with Apple",
  "welcome.email": "Continue with email",
  "welcome.emailLabel": "Your email",
  "welcome.emailPlaceholder": "you@example.com",
  "welcome.emailSend": "Send me a sign-in link",
  "welcome.emailSent": "We sent a link to {email}. Open your inbox and tap it.",
  "welcome.emailInvalid": "Enter a full email address, like you@example.com",
  "welcome.error": "Couldn't sign you in. Check your connection and try again.",
  "welcome.providerOff": "This sign-in method isn't switched on yet. Use another one.",
  "welcome.notConfigured":
    "Sign-in isn't set up yet: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are needed.",
  "welcome.terms": "By continuing you accept the Terms and Privacy Policy.",
  "welcome.about": "About",

  "onboarding.progress": "Onboarding, step {step} of 3",
  "onboarding.pick.title": "Which ones did you love?",
  "onboarding.pick.subtitle": "Pick at least 10 — that's how we learn your taste.",
  "onboarding.pick.search": "Search films",
  "onboarding.pick.searchPlaceholder": "Search films…",
  "onboarding.pick.count": "{n} / 10 picked",
  "onboarding.pick.noneSeen": "I haven't seen any of these",
  "onboarding.pick.needMore": "Pick {n} more",
  "onboarding.pick.continue": "Continue",
  "onboarding.pick.selected": "{title}, selected",
  "onboarding.pick.empty": "No films here yet. Try searching by title.",
  "onboarding.pick.error": "Couldn't load films. Check your connection and try again.",
  "onboarding.pick.noResults": "No films found for “{q}”. Try another spelling.",

  "onboarding.rate.title": "How much did you like it?",
  "onboarding.rate.position": "{i} / {n}",
  "onboarding.rate.scoreLabel": "Score out of 10",
  "onboarding.rate.outOf": "out of 10",
  "onboarding.rate.keysHint": "Keys 1–9 for a quick score, 0 for 10",
  "onboarding.rate.liked": "What did you like?",
  "onboarding.rate.notSeen": "Haven't seen it",
  "onboarding.rate.next": "Next",
  "onboarding.rate.previous": "Previous",
  "onboarding.rate.saveError": "Couldn't save the score. Try again.",
  "onboarding.rate.needMore": {
    one: "Recommendations need {n} more rating. Pick a few more films.",
    other: "Recommendations need {n} more ratings. Pick a few more films.",
  },
  "onboarding.rate.pickMore": "Pick more films",

  "onboarding.done.title": "All set!",
  "onboarding.done.body": {
    one: "You rated {n} film. Your recommendations are ready.",
    other: "You rated {n} films. Your recommendations are ready.",
  },
  "onboarding.done.cta": "See my recommendations",

  "feed.section.for_you": "For you",
  "feed.section.because_you_loved": "Because you loved {title}",
  "feed.section.under_90": "Under 90 minutes",
  "feed.section.outside_usual": "Outside your usual taste",
  "feed.notEnough": {
    one: "Rate {n} more film to get recommendations.",
    other: "Rate {n} more films to get recommendations.",
  },
  "feed.notEnoughCta": "Keep rating",
  "feed.empty": "No film matches you above 60% yet. Rate a few more films.",
  "feed.emptyCta": "Search films",
  "feed.error": "Couldn't load recommendations. Check your connection and try again.",

  "movie.whyYou": "Why you?",
  "movie.whyYouFallback": "What you share with it: {traits}.",
  "movie.noMatch": "Rate 10 films first to see how well this one matches you.",
  "movie.compareTitle": "Your taste vs this film",
  "movie.compareYou": "you",
  "movie.compareFilm": "film",
  "movie.traitsPending": "This film's DNA hasn't been computed yet.",
  "movie.director": "Director",
  "movie.cast": "Cast",
  "movie.overview": "Overview",
  "movie.rate": "Rate",
  "movie.yourRating": "Your rating: {score}",
  "movie.saveToList": "Save",
  "movie.onList": "Saved",
  "movie.rateDialog": "Rate {title}",
  "movie.rateSave": "Save rating",
  "movie.rateError": "The rating wasn't saved. Try again.",
  "movie.listError": "Your watchlist didn't change. Try again.",
  "movie.notFound": "We couldn't find this film. It may have left the catalogue.",
  "movie.notFoundCta": "Go home",
  "movie.error": "Couldn't load this film. Check your connection and try again.",

  "search.title": "Search",
  "search.label": "Film title",
  "search.placeholder": "Search films…",
  "search.filters": "Filters",
  "search.yearFrom": "From year",
  "search.yearTo": "To year",
  "search.runtime": "Length",
  "search.runtimeAny": "Any",
  "search.runtimeUpTo": "Up to {n} minutes",
  "search.traits": "Strong in",
  "search.clear": "Clear filters",
  "search.popular": "Popular films",
  "search.results": "Results",
  "search.empty": "No films match these filters. Try loosening them.",
  "search.error": "Search didn't work. Check your connection and try again.",

  "watchlist.title": "Watchlist",
  "watchlist.groups": "Groups",
  "watchlist.group.next": "Watch next",
  "watchlist.group.short": "Under 90 min",
  "watchlist.group.watched": "Watched",
  "watchlist.markWatched": "Watched",
  "watchlist.markWatchedLabel": "Mark {title} as watched",
  "watchlist.remove": "Remove",
  "watchlist.removeLabel": "Remove {title} from the watchlist",
  "watchlist.empty": "Your watchlist is empty. Find a film you're curious about and tap “Save”.",
  "watchlist.emptyGroup": "No films in this group.",
  "watchlist.emptyCta": "Search films",
  "watchlist.error": "Couldn't load your watchlist. Check your connection and try again.",
  "watchlist.actionError": "That change wasn't saved. Try again.",

  "dna.title": "Movie DNA",
  "dna.rateMore": {
    one: "Rate {n} more film to unlock your Movie DNA.",
    other: "Rate {n} more films to unlock your Movie DNA.",
  },
  "dna.rateMoreCta": "Rate films",
  "dna.noTaste":
    "No liked films yet: your DNA is built from films you rate above 5. Rate some films you enjoyed.",
  "dna.summary": "You prefer films strong in {a}, {b} and {c}.",
  "dna.stats": "Stats",
  "dna.statFilms": "Films rated",
  "dna.statAverage": "Average rating",
  "dna.statGenre": "Top genre",
  "dna.share": "Share",
  "dna.shareText": "My Movie DNA: {traits}.",
  "dna.copied": "Copied",
  "dna.shareError": "Couldn't share. Copy the text by hand.",
  "dna.error": "Couldn't load your Movie DNA. Check your connection and try again.",

  "profile.title": "Profile",
  "profile.language": "Language",
  "profile.signOut": "Sign out",
  "profile.delete": "Delete account",
  "profile.deleteConfirm":
    "All your ratings, your watchlist and your Movie DNA will be deleted. This can't be undone.",
  "profile.deleteYes": "Yes, delete",
  "profile.deleteError": "Couldn't delete the account. Try again.",
  // Each language is named in itself, the same in every dictionary; menu order: en, uz, ru.
  "lang.en": "English",
  "lang.uz": "O'zbek",
  "lang.ru": "Русский",
  "profile.about": "About",
  "profile.tmdb": "This product uses the TMDB API but is not endorsed or certified by TMDB.",
  "profile.tmdbLink": "The Movie Database (TMDB)",

  "notFound.title": "This page doesn't exist",
  "notFound.cta": "Go home",

  // packages/shared/traits.json label_en
  "trait.psychological_complexity": "Psychological",
  "trait.plot_twist": "Plot twists",
  "trait.mystery": "Mystery",
  "trait.character_depth": "Complex characters",
  "trait.emotional_intensity": "Emotional intensity",
  "trait.pacing": "Pace",
  "trait.humor": "Humor",
  "trait.romance": "Romance",
  "trait.action": "Action",
  "trait.violence": "Violence",
  "trait.visual_style": "Visual style",
  "trait.realism": "Realism",
  "trait.darkness": "Tone darkness",
  "trait.ending_ambiguity": "Open ending",
} satisfies Record<string, Message>;

export type MessageKey = keyof typeof en;
