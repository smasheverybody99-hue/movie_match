import type { Message, MessageKey } from "./en";

/**
 * Uzbek strings: the second language (TZ 1.8). Exactly the keys of `en.ts`.
 *
 * Uzbek does not inflect a noun after a number ("1 ta film", "5 ta film"), so plain
 * strings serve where English needs a `Plural`.
 */
export const uz: Record<MessageKey, Message> = {
  "app.name": "Movie Match",
  "app.loadingPage": "Sahifa yuklanmoqda",

  // Navigation
  "nav.label": "Asosiy bo'limlar",
  "nav.home": "Bosh sahifa",
  "nav.search": "Qidiruv",
  "nav.dna": "Movie DNA",
  "nav.watchlist": "Watchlist",
  "nav.profile": "Profil",
  "nav.back": "Orqaga",
  "nav.skipToContent": "Asosiy qismga o'tish",

  // Common
  "common.retry": "Qayta urinish",
  "common.offline": "Oflayn. Saqlangan ma'lumot ko'rsatilmoqda.",
  "common.offlineNoCache":
    "Internet yo'q, bu sahifa esa hali saqlanmagan. Ulanish qaytgach, qayta urining.",
  "common.close": "Yopish",
  "common.cancel": "Bekor qilish",
  "common.save": "Saqlash",
  "common.minutes": "{n} daq",
  "common.matchBadge": "{n}%",
  "common.matchLabel": "{n}% mos",
  "common.poster": "{title} posteri",
  "common.matchWord": "MOSLIK",
  "common.loading": "Yuklanmoqda",

  // Welcome / auth
  "welcome.tagline":
    "Hamma ko'rgan filmni emas — siz haqiqatan yaxshi ko'radigan narsaga qarab film toping.",
  "welcome.google": "Google bilan davom etish",
  "welcome.apple": "Apple bilan davom etish",
  "welcome.email": "Email bilan davom etish",
  "welcome.emailLabel": "Email manzilingiz",
  "welcome.emailPlaceholder": "siz@misol.uz",
  "welcome.emailSend": "Kirish havolasini yuborish",
  "welcome.emailSent": "Havola {email} manziliga yuborildi. Pochtangizni ochib, havolani bosing.",
  "welcome.emailInvalid": "Email manzilini to'liq kiriting, masalan: siz@misol.uz",
  "welcome.error": "Kirib bo'lmadi. Internetni tekshirib, qayta urining.",
  "welcome.providerOff": "Bu usul hozircha yoqilmagan. Boshqa usul bilan kiring.",
  "welcome.notConfigured":
    "Kirish hali sozlanmagan: VITE_SUPABASE_URL va VITE_SUPABASE_ANON_KEY kerak.",
  "welcome.terms": "Davom etsangiz, Foydalanish shartlari va Maxfiylik siyosatini qabul qilasiz.",
  "welcome.about": "Loyiha haqida",

  // Onboarding — pick
  "onboarding.progress": "Onboarding, {step}-qadam, jami 3",
  "onboarding.pick.title": "Qaysilarini yoqtirgansiz?",
  "onboarding.pick.subtitle": "Kamida 10 ta tanlang — ta'mingizni shundan o'rganamiz.",
  "onboarding.pick.search": "Film qidirish",
  "onboarding.pick.searchPlaceholder": "Film qidirish…",
  "onboarding.pick.count": "{n} / 10 tanlandi",
  "onboarding.pick.noneSeen": "Hech birini ko'rmadim",
  "onboarding.pick.needMore": "Yana {n} ta tanlang",
  "onboarding.pick.continue": "Davom etish",
  "onboarding.pick.selected": "{title}, tanlangan",
  "onboarding.pick.empty": "Bu yerda hozircha film yo'q. Nomi bo'yicha qidirib ko'ring.",
  "onboarding.pick.error": "Filmlarni yuklab bo'lmadi. Internetni tekshirib, qayta urining.",
  "onboarding.pick.noResults": "“{q}” bo'yicha film topilmadi. Boshqacha yozib ko'ring.",

  // Onboarding — rate
  "onboarding.rate.title": "Qanchalik yoqdi?",
  "onboarding.rate.position": "{i} / {n}",
  "onboarding.rate.scoreLabel": "Baho, 10 dan",
  "onboarding.rate.outOf": "10 dan",
  "onboarding.rate.keysHint": "1–9 tugmalari: tezkor baho, 0 — 10",
  "onboarding.rate.liked": "Nimasi yoqdi?",
  "onboarding.rate.notSeen": "Ko'rmadim",
  "onboarding.rate.next": "Keyingisi",
  "onboarding.rate.previous": "Oldingisi",
  "onboarding.rate.saveError": "Bahoni saqlab bo'lmadi. Qayta urining.",
  "onboarding.rate.needMore":
    "Tavsiya uchun yana {n} ta baho kerak. Yana bir nechta film tanlang.",
  "onboarding.rate.pickMore": "Yana film tanlash",

  // Onboarding — done
  "onboarding.done.title": "Tayyor!",
  "onboarding.done.body": "{n} ta baho qo'ydingiz. Tavsiyalaringiz tayyor.",
  "onboarding.done.cta": "Tavsiyalarni ko'rish",

  // Feed
  "feed.section.for_you": "Siz uchun",
  "feed.section.because_you_loved": "{title} yoqqani uchun",
  "feed.section.under_90": "90 daqiqadan qisqa",
  "feed.section.outside_usual": "Odatdagi ta'mingizdan tashqari",
  "feed.notEnough": "Tavsiya uchun yana {n} ta film baholang.",
  "feed.notEnoughCta": "Baholashni davom ettirish",
  "feed.empty": "Hozircha sizga 60% dan yuqori mos film topilmadi. Yana bir nechta film baholang.",
  "feed.emptyCta": "Film qidirish",
  "feed.error": "Tavsiyalarni yuklab bo'lmadi. Internetni tekshirib, qayta urining.",
  "feed.quickSave": "{title} filmini saqlash",
  "feed.scrollPrev": "Oldingi filmlar",
  "feed.scrollNext": "Keyingi filmlar",

  // Film page
  "movie.whyYou": "Nega sizga?",
  "movie.whyYouFallback": "Siz bilan umumiy jihatlari: {traits}.",
  "movie.whyYouGeneral": "Ta'mingizga umuman mos — bitta yaqqol jihati bilan emas.",
  "movie.noMatch": "Mosligini hisoblash uchun avval 10 ta film baholang.",
  "movie.compareTitle": "Sizning ta'mingiz va shu film",
  "movie.compareYou": "siz",
  "movie.compareFilm": "film",
  "movie.traitsPending": "Bu filmning DNA'si hali hisoblanmagan.",
  "movie.director": "Rejissyor",
  "movie.cast": "Rollarda",
  "movie.overview": "Qisqacha",
  "movie.rate": "Baholash",
  "movie.yourRating": "Bahoyingiz: {score}",
  "movie.saveToList": "Saqlash",
  "movie.onList": "Saqlangan",
  "movie.rateDialog": "{title} filmini baholash",
  "movie.rateSave": "Bahoni saqlash",
  "movie.rateError": "Baho saqlanmadi. Qayta urining.",
  "movie.listError": "Watchlist o'zgarmadi. Qayta urining.",
  "movie.notFound": "Bunday film topilmadi. U katalogdan olib tashlangan bo'lishi mumkin.",
  "movie.notFoundCta": "Bosh sahifaga",
  "movie.error": "Filmni yuklab bo'lmadi. Internetni tekshirib, qayta urining.",

  // Search
  "search.title": "Qidiruv",
  "search.label": "Film nomi",
  "search.placeholder": "Film qidirish…",
  "search.filters": "Filtrlar",
  "search.yearFrom": "Yildan",
  "search.yearTo": "Yilgacha",
  "search.runtime": "Davomiyligi",
  "search.runtimeAny": "Farqi yo'q",
  "search.runtimeUpTo": "{n} daqiqagacha",
  "search.traits": "Kuchli tomoni",
  "search.clear": "Filtrlarni tozalash",
  "search.popular": "Mashhur filmlar",
  "search.results": "Natijalar",
  "search.empty": "Bu shartlarga mos film yo'q. Filtrlarni yumshatib ko'ring.",
  "search.error": "Qidiruv ishlamadi. Internetni tekshirib, qayta urining.",

  // Watchlist
  "watchlist.title": "Watchlist",
  "watchlist.groups": "Guruhlar",
  "watchlist.group.next": "Keyingi ko'riladigan",
  "watchlist.group.short": "90 daqiqagacha",
  "watchlist.group.watched": "Ko'rilgan",
  "watchlist.markWatched": "Ko'rdim",
  "watchlist.markWatchedLabel": "{title} — ko'rdim deb belgilash",
  "watchlist.remove": "O'chirish",
  "watchlist.removeLabel": "{title} — ro'yxatdan o'chirish",
  "watchlist.empty": "Ro'yxatingiz hali bo'sh. Qiziq filmni topib, “Saqlash”ni bosing.",
  "watchlist.emptyGroup": "Bu guruhda film yo'q.",
  "watchlist.emptyCta": "Film qidirish",
  "watchlist.error": "Watchlist'ni yuklab bo'lmadi. Internetni tekshirib, qayta urining.",
  "watchlist.actionError": "O'zgarish saqlanmadi. Qayta urining.",

  // Movie DNA
  "dna.title": "Movie DNA",
  "dna.rateMore": "Movie DNA uchun yana {n} ta film baholang.",
  "dna.rateMoreCta": "Film baholash",
  "dna.noTaste":
    "Hali yoqqan filmingiz yo'q: DNA 5 dan yuqori baholangan filmlardan quriladi. Yoqqan filmlaringizni baholang.",
  "dna.summary": "Siz {a}, {b} va {c} kuchli bo'lgan filmlarni afzal ko'rasiz.",
  "dna.stats": "Statistika",
  "dna.statFilms": "Baholangan filmlar",
  "dna.statAverage": "O'rtacha baho",
  "dna.statGenre": "Eng ko'p janr",
  "dna.share": "Ulashish",
  "dna.shareText": "Mening Movie DNA'm: {traits}.",
  "dna.copied": "Nusxalandi",
  "dna.shareError": "Ulashib bo'lmadi. Matnni qo'lda nusxalang.",
  "dna.error": "Movie DNA'ni yuklab bo'lmadi. Internetni tekshirib, qayta urining.",

  // Profile / about
  "profile.title": "Profil",
  "profile.language": "Til",
  "profile.signOut": "Chiqish",
  "profile.delete": "Akkauntni o'chirish",
  "profile.deleteConfirm":
    "Barcha baholaringiz, watchlist va Movie DNA o'chiriladi. Buni qaytarib bo'lmaydi.",
  "profile.deleteYes": "Ha, o'chirish",
  "profile.deleteError": "Akkauntni o'chirib bo'lmadi. Qayta urining.",
  "lang.en": "English",
  "lang.uz": "O'zbek",
  "lang.ru": "Русский",
  "profile.about": "Loyiha haqida",
  "profile.tmdb": "Bu mahsulot TMDB API'dan foydalanadi, lekin TMDB tomonidan tasdiqlanmagan.",
  "profile.tmdbLink": "The Movie Database (TMDB)",

  "notFound.title": "Bunday sahifa yo'q",
  "notFound.cta": "Bosh sahifaga",

  // Traits: packages/shared/traits.json label_uz
  "trait.psychological_complexity": "Psixologik",
  "trait.plot_twist": "Syujet burilishi",
  "trait.mystery": "Sirlilik",
  "trait.character_depth": "Murakkab personajlar",
  "trait.emotional_intensity": "Hissiy zichlik",
  "trait.pacing": "Temp",
  "trait.humor": "Hazil",
  "trait.romance": "Romantika",
  "trait.action": "Ekshn",
  "trait.violence": "Zo'ravonlik",
  "trait.visual_style": "Vizual uslub",
  "trait.realism": "Realizm",
  "trait.darkness": "Qorong'ulik",
  "trait.ending_ambiguity": "Ochiq tugash",
};
