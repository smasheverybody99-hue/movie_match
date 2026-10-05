# Holat — Movie Match

Oxirgi yangilanish: 2026-10-05 (dizayn 3-bosqich: Home hero, `backdrop_path` har filmda); 2026-10-05 (film sahifasi: daraja — panel sarlavhasi; "yaxshi" 15%, TZ 1.14); 2026-10-05 (FR-5: match darajasi, TZ 1.13; dizayn 2-bosqich tuzatishlari); 2026-10-04 (dizayn 1-bosqich); 2026-10-02 · F1 ma'lumot qismi yopildi (500 film) · Tillar: en standart, uz, ru (TZ 1.8) · **LLM provayderi tanlanmagan** (ADR 0006)

Bitta sahifada: qaysi faza tugagan, nima chala, keyingi qadam. Tafsilotlar faza
hisobotlarida: `docs/phase-1-status.md`, `docs/phase-2-status.md`, `docs/phase-3-status.md`. Fazalar ro'yxati:
`docs/prompts/README.md`. Xarajatlar: `docs/costs.md`.

## Fazalar

| Faza | Holat |
|---|---|
| F0 — Poydevor | **Tugagan** (`b2a4d35`, gate o'tgan) |
| F1 — Ma'lumot va Movie DNA | **Kod tugagan, ma'lumot chala.** 1-bosqich bajarildi (2026-10-01): 50 film trait oldi (sync, 0 yiqildi), qo'lda ko'rik **o'tdi** — 50 dan 3 tasi bahsli, chegara 5. 2-bosqich: traitlar 500 / 500 (13 film Google filtri bilan bloklanib almashtirildi); 2-bosqich ≈ $0.28 standart tarifda, bepul tarifda $0. Embedding 500 / 500 (ikki run, $0.0182 standart, bepul tarifda $0); missing count 0. Qo'shnilar ko'rigi **o'tdi** (2026-10-02). **Ma'lumot qismi yopildi.** Ma'lum muammo: Spirited Away qo'shnilari studiya bo'yicha to'planadi (F2 qo'lda tekshiruvida qaraladi) |
| F2 — Tavsiya dvigateli | **Tugagan** (2026-10-02). Qo'lda tekshiruv **o'tdi** (foydalanuvchi xulosasi): "For you" dagi 20 filmdan deyarli hammasini ko'rardi; qolgan bo'limlar "yomonmas". Qo'lda match hisobi va 5 izohni sabablar bilan solishtirish **bajarilmadi** — formula testda (`test_match_is_recomputable_from_stored_numbers`, har commit'da), izohning mazmuni test qilinmagan. Izoh narxi o'lchangan: $0.00013 bittasi. Tekshiruvda topilgan `POST /watchlist` 500 xatosi tuzatilgan (`01d08f7`); izohlar limiti interfeysda ko'rinmaydi (backlog, TZ 1.9); feed 45 bahoda ~15 s (F5 ishi) |
| F3 — Web ilova | **Kod tugagan, `main` da (`66bc7a0`), CI yashil. Qo'lda tekshiruv chala.** Foydalanuvchi so'rovi bilan F2 qo'lda tekshiruvidan oldin boshlangan (prompt sharti bajarilmagan). Onboarding vaqti o'lchanmagan: Supabase kalitlari va trait'li filmlar kerak |
| Tillar (TZ 1.8, 2026-10-02) | **Kod tayyor.** Ingliz — standart til va kalitlar manbasi (`apps/web/src/i18n/en.ts`); o'zbek — ikkilamchi; rus — qo'shimcha, **ko'rilmagan qoralama**. Menyu: English, O'zbek, Русский; tanlov `localStorage` da saqlanadi, brauzer tili aniqlanmaydi. API: `lang` = `en` \| `uz` \| `ru`, standart `en`; izohlar rus tilida ham (har til alohida kesh). Film ma'lumoti ingliz tilida qoladi (backlog) |
| F4 va keyingilari | Boshlanmagan |

## Oxirgi gate natijasi

| | |
|---|---|
| CI (`main`, `a4fb69a`, daraja — panel sarlavhasi, "yaxshi" 0.15) | **Yashil**, 2026-10-05: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37348808980 |
| CI (`main`, `d90cc6e`, FR-5 darajasi + STATUS) | **Yashil**, 2026-10-05: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37274508333 (`0874314` shu push bilan, alohida run'siz) |
| CI (`main`, `1033ed9`, dizayn 2-bosqich tuzatishlari) | **Yashil**, 2026-10-05: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37266785192 |
| CI (`main`, `b28b9da`, F2 yopilishi) | **Yashil**, 2026-10-02: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36989348804. `app/services/` coverage ≥ 85% (`--fail-under=85` qadami o'tgan). **Aniq raqam o'qilmadi** (log GitHub login talab qiladi) — keyingi to'liq mahalliy run'da yoziladi |
| CI (`main`, `4ccd878`) | **Yashil**, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36609806293 (provayder interfeysi, katalog 500, costs.md, Alembic log tuzatishi) |
| CI (`main`, `852c767`, provayder interfeysi) | **Qizil**, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36603649367 — `test_migrations` dan keyin `app.cost` logi o'chib qolgan; `4ccd878` da tuzatilgan |
| CI (`main`, `66bc7a0`, F3 merge) | Yashil, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36599220279 |
| Web testlari | Mahalliy, 2026-10-05 (Home hero): 16 fayl, **205 test**, hammasi o'tgan; lint 0, build 0. Avvalgi (daraja — panel sarlavhasi): 15 fayl, 192 test, hammasi o'tgan; lint 0, build 0. Avvalgi (2-bosqich tuzatishlari): 15 fayl, 189 test, hammasi o'tgan; lint 0, build 0. Onboarding beqarorligining sababi topildi va tuzatildi (`docs/ui.md`, "2-bosqich, ko'rikdan keyingi tuzatishlar"): ko'p tapli testlar CPU'ga bog'liq, muddati o'tgan test keyingi testning DOM'ida ishlab qolardi, baholash qadamida effekt poygasi bor edi. Sun'iy CPU yuki ostida: Onboarding 8 / 8, to'liq to'plam 3 / 3 yashil |
| API testlari (tillar) | Mahalliy, 2026-10-02: unit + contract 277 o'tgan; o'zgargan integratsiya fayllari (`test_explanations_cache`, `test_recommendations`) 24 / 24. To'liq mahalliy run Frankfurt bazasida 30 daqiqalik chegaraga yetib to'xtatildi (natijasiz) — to'liq run CI'da |
| `app/services/` coverage | CI (`9b046e1`): ≥ 85% (`--fail-under=85` qadami o'tgan; aniq raqam run log'ida). Mahalliy to'liq run, 2026-09-28: **98.9%** (535 statement, 6 miss) |
| API testlari (Home hero, `backdrop_path`) | Mahalliy, 2026-10-05: o'zgarishga tegadigan fayllar — `test_recommendations` + unit: o'tgan (yangi backdrop testi bilan); `test_movies_api` + `test_watchlist_api`: 34 / 34 (birinchi run'da 5 tasi yiqildi — `MovieDetailOut` ga `backdrop_path` ikki marta berilgan edi, tuzatildi). To'liq run — CI'da |
| API testlari ("yaxshi" 0.15) | Mahalliy to'liq run, 2026-10-05: **505 o'tgan, 13 yiqilgan**, 48 daqiqa. 13 tasi hammasi `test_auth.py` da: Frankfurt bazasiga ulanish uzildi (`WinError 121 semaphore timeout`, "connection was closed in the middle of operation"), modul sessiyasi buzilib qolgan 12 test "session is in 'prepared' state" bilan yiqildi. `test_auth.py` alohida qayta: **60 / 60 o'tgan**. Coverage `app/services` + `app/pipelines`: **89%** (1 659 statement, 186 miss); `bands.py` 97%, `matching.py` 100%, `recommend.py` 99%. Unit 279 / 279, ruff 0 |
| API testlari (FR-5 darajasi) | Mahalliy to'liq run, 2026-10-05 (`0874314`): **518 o'tgan**, 0 yiqilgan, 38 daqiqa (Frankfurt test bazasi). Coverage `app/services` + `app/pipelines` birga: **89%** (1 659 statement, 185 miss); `bands.py` 97%, `matching.py` 100%, `recommend.py` 99% |
| API testlari | Mahalliy to'liq run, 2026-09-30 (`852c767` holatida): 424 o'tgan, 1 yiqilgan — CI'dagi o'sha log testi; tuzatishdan keyin u juftlik (migratsiya + provayder testlari) bilan qayta o'tgan |

CI Supabase'ga ulanmaydi: runner'dagi Postgres 17 + pgvector konteyneri ishlatiladi,
secret yo'q (`.github/workflows/gate.yml`).

## Chala

1. **Provayder tanlanmagan (ADR 0006).** Gemini Google Cloud'ning $50 karta hold talabi
   bilan yopiq. Kod provayder interfeysi orqasida; yangi provayder = bitta modul + bitta
   qator. Variantlar narxi bilan: `docs/costs.md`. Agar tanlangan provayderning
   embeddingi 1 536 o'lchamli bo'lmasa — migratsiya va qayta embed kerak (API bu holatda
   ishga tushmaydi, xato matni yo'lni aytadi).
2. **F1: ma'lum muammo — studiya to'planishi.** Spirited Away'ning 9 ta eng yaqin
   qo'shnisi Ghibli; Coraline 15-o'rinda, Pan's Labyrinth 56-o'rinda. Embedding matnida
   studiya maydoni yo'q. F2 qo'lda tekshiruvida alohida qaraladi
   (`docs/phase-1-status.md`). Masofalar siqilgan (median 0.275): absolyut chegara
   ishlamaydi, faqat tartib.
3. **F1: 50 filmlik ko'rik — o'tdi** (2026-10-01): 47 ok, 3 bahsli (Titanic action,
   Shawshank plot_twist, Frozen romance), chegara 5. Tafsilot: `docs/phase-1-status.md`.
4. **F2: qo'lda tekshiruv.** 30 ta baho qo'yib tavsiyalarni o'qish; bitta match'ni qo'lda
   hisoblash; 5 ta izohni o'qish (bir necha sent ulushi, provayder tanlangach, tasdiq bilan).
5. **F3: haqiqiy kirish hali sinalmagan.** Web kalitlari (`VITE_SUPABASE_URL`,
   `VITE_SUPABASE_ANON_KEY`) qo'yilgan. Loyiha ES256 signing keys'ga o'tgan; API endi
   tokenlarni JWKS bilan tekshiradi (ADR 0007) — `services/api/.env` ga
   `SUPABASE_PROJECT_URL` kerak, `SUPABASE_JWT_SECRET` bo'sh qolsin. Apple kirishi Apple
   Developer Program'ni talab qiladi ($99/yil) — foydalanuvchi qarori.
6. **F3: qo'lda tekshiruv chala.** Onboarding vaqti o'lchanmagan; Lighthouse dev serverda
   o'lchangan (LCP 2.1 s mobil, INP 80 ms) — production build va haqiqiy posterlar bilan
   qayta o'lchash kerak. axe: 0 buzilish, 320px: gorizontal scroll yo'q
   (`docs/phase-3-status.md`).
7. **Tezlik (TZ: tavsiya < 500 ms) o'lchanmagan.** Dev mashinadan bazagacha so'rov
   150–1000 ms; bazaga yaqin serverdan o'lchash kerak.

## Keyingi qadam

1. **FR-5: match darajasi joriy qilindi (TZ 1.13, 2026-10-05).** Interfeys foizni emas,
   darajani ko'rsatadi: "kuchli" (eng yaqin 5 film, qizil), "yaxshi" (eng yaqin **15%**,
   neytral; TZ 1.14 gacha 35%). Film sahifasida daraja — "Why you" panelining sarlavhasi,
   darajasiz — neytral "You and this film" (`docs/ui.md`). Foiz API'da ichki qoladi; "60% dan past" o'rniga eng uzoq 25% tavsiya
   qilinmaydi. Film sahifasida ring yo'q. Asos — pastdagi "FR-5 o'lchovi". Dizayn
   2-bosqich tuzatishlari va **3-bosqich (Home hero, `backdrop_path` har filmda)**
   bajarilgan (2026-10-05, `docs/ui.md`). Keyingisi: foydalanuvchi ko'rigi; ochiq savol —
   Home'da "yaxshi" daraja hali ham 3 sahifadan 2 tasida (pastda, "35% → 15%").
   Match foizi (FR-5) bo'yicha qaror hali ochiq. Oldin bajarildi (2026-10-02): **sabablar katalogga nisbatan** (TZ 1.12, FR-5; match
   foizi o'zgarmagan) — "Why you" endi har filmda bir xil uchta trait emas. Eski 20 ta
   izoh (bitta foydalanuvchi) ruxsat bilan o'chirildi; yangilari yangi sabablar bilan
   yoziladi. Mahalliy API qayta ishga tushirilishi kerak. Match foizi taqsimoti o'lchandi
   (`docs/phase-2-status.md`): yoqmagan va yoqqan filmlar bir xil (~85%), 60% chegarasi
   deyarli hech narsani filtrlamaydi — FR-5 formulasi bo'yicha alohida qaror kutilmoqda.
2. **Rus tilini ko'rib chiqish (foydalanuvchi).** `apps/web/src/i18n/ru.ts` (166 kalit)
   va `packages/shared/traits.json` dagi `label_ru` — agent yozgan, **ko'rilmagan
   qoralama**. Belgi (shu band va `ru.ts` sarlavhasi) foydalanuvchi ko'rib chiqmaguncha
   turadi. E'tibor: "Хочу посмотреть" (watchlist), ring ichida "СХОДСТВО" (joy 9px da
   ~65px, "СОВПАДЕНИЕ" sig'maydi), `dna.summary` jumla tuzilishi.
3. Batch uchun billing ochilsa — `TRAIT_MODE=batch` ga qaytish (yarim narx).

## FR-5 o'lchovi (2026-10-05) — match darajasi qarorining asosi

Bitta akkaunt (32 baho, 27 tasi traitli film; 8+ — 13, ≤ 5 — 12), 500 film, faqat o'qish
(`READ ONLY` tranzaksiya), LLM yo'q. Katalog statistikasi `reasons.trait_stats` dan.
Ajratish o'lchovi — **AUC**: tasodifiy 8+ film tasodifiy ≤ 5 filmdan yuqori turishi
ehtimoli (0.5 — tanga). Median farqi ham yozildi, lekin u shkala cho'zilsa o'sadi,
tartib o'zgarmasa ham — shuning uchun mezon AUC.

| Variant | 8+ median | ≤ 5 median | Median farqi | AUC | Butun 500: min–max |
|---|---|---|---|---|---|
| Hozirgi formula | 86 | 84.5 | 1.5 | 0.52 | 59–92 |
| Z (z-fazoda masofa, `100·e^(−d²/2)`) | 83 | 77 | 6 | 0.55 | 13–94 |
| Z (`100·(1 − d/3)`) | 80 | 76 | 4 | 0.55 | 32–89 |
| P (persentil, hozirgi tartibda) | 93 | 88.5 | 4.5 | 0.52 | 0–100 |
| P (persentil, Z tartibida) | 93 | 86.5 | 6.5 | 0.55 | 0–100 |

- **Leave-one-out** (yoqqan filmlar ta'm vektorining o'zida bor; har film o'zisiz qurilgan
  profilga qarshi): hozirgi 0.44, Z 0.50.
- 13 va 12 filmda AUC xatosi ±0.12: 0.55 tasodifdan farq qilmaydi. To'g'ri xulosa —
  **foiz bahoni bashorat qilishini ko'rsata olmadik**, "ma'nosiz" emas: u trait bo'yicha
  uzoqlikni o'lchaydi.
- Misollar: 2 baholangan film — 90% (P da yuqori 1%), 4 baholangan — 89%.
- **Traitlar bo'yicha** (8+ o'rtachasi − ≤ 5 o'rtachasi, katalog σ da; AUC): `realism`
  +0.59 (0.75), `emotional_intensity` +0.56 (0.73), `plot_twist` +0.55 (0.67),
  `character_depth` +0.41 (0.65), `visual_style` −0.33 (0.35); qolgan 9 tasi |0.21| dan
  kichik. Ikki guruh markazlari orasi o'rtacha 0.31 σ. 14 trait 25 filmda sinalgan —
  tasodif ham bo'lishi mumkin. Ta'm faqat yoqqan filmlardan quriladi (≤ 5 vazni 0) —
  ehtimoliy asosiy sabab (TZ backlog, 2026-10-05).
- **Daraja chegaralari** (o'sha akkaunt): top 10% bo'lsa 500 dan 50 "kuchli" va Home
  birinchi ekranida (1440, 12 karta) 11 qizil — "For you" va "Because you loved" ta'rifan
  eng yuqori o'rinlardan tuziladi. Kuchli = top 5% → 6, 2% → 4, **1% (5 film) → 2**; ulush
  katalog o'sganda (5 000) yana 11 ga qaytadi, shuning uchun kuchli — mutlaq N = 5. Yaxshi
  (top 35%): 125 film; unrated 473 dan 115. Kuchli 5 talikning ikkitasi allaqachon
  baholangan (biri 9, biri 2).
- **Pastki chegara:** "60% dan past" 473 dan 2 ta filmni chiqarardi; eng uzoq 25% (o'rin
  > 375) bugun Home'dan hech narsani chiqarmaydi (eng uzoq karta — 315-o'rin, "Under 90").
- Narx: chegaralar har foydalanuvchiga 500 filmda 4 ms, 5 000 da 68 ms (o'lchangan);
  katalog vektorlari 10 daqiqa, chegaralar `taste_updated_at` bo'yicha keshlanadi
  (`services/bands.py`).

## "Yaxshi" 35% → 15% o'lchovi (2026-10-05, TZ 1.14)

O'sha akkaunt (32 baho), 500 traitli film, `READ ONLY` tranzaksiya, LLM yo'q. Daraja
`matching.band_cuts` bilan, API qanday hisoblasa shunday; Home — `recommend()` ning
o'zi (5 bo'lim, 50 karta).

| | 0.35 | 0.15 |
|---|---|---|
| Katalog: darajali film sahifalari | 175 / 500 (**35%**) | 75 / 500 (**15%**) |
| Baholanmagan filmlar sahifalari | 153 / 473 (32.3%) | 60 / 473 (12.7%) |
| Home'dagi filmlar sahifalari (barcha bo'limlar) | 45 / 50 (**90%**; 3 kuchli, 42 yaxshi) | 34 / 50 (**68%**; 3 kuchli, 31 yaxshi) |
| Home birinchi ikki qatori (2 × 6) | 12 / 12 | 12 / 12 |
| Watchlist pill'lari | — | — |

- **Watchlist o'lchab bo'lmadi:** bazada bitta ham watchlist yozuvi yo'q (hamma
  akkauntlarda 0). Agar ro'yxat Home'dan to'ldirilsa, ulush Home'dagidek bo'ladi —
  bu taxmin, o'lchov emas.
- **Muhim:** katalog bo'yicha yorliq 3 baravar kamaydi, lekin foydalanuvchi ochadigan
  sahifalarning asosiy manbai — Home, u esa ta'rifan eng yuqori o'rinlardan tuziladi:
  u yerda daraja hali ham 3 sahifadan 2 tasida, birinchi qatorlarda hammasida. "Har
  uchinchi sahifa" muammosi qidiruv va to'g'ridan-to'g'ri havolalarda hal bo'ldi, Home
  yo'lida emas. Keyingi qaror (ulushni yana kamaytirish, mutlaq N, yoki Home'da
  "yaxshi" ni ko'rsatmaslik — kartada u allaqachon yo'q) foydalanuvchida.

## Muhit

- Test bazasi: Supabase, Frankfurt (`eu-central-1`). Asosiy baza: Singapur
  (`ap-southeast-1`), 5 000 film — testlar unga hech qachon ulanmaydi.
- Ikkala baza ham migratsiya `0004` (head) da, 2026-09-29 dan. Asosiy bazada
  `lock_timeout = 5s` bilan, COMMIT'dan keyin yangi ulanishda tekshirilgan; `movies`
  5 000 → 5 000. Vosita: `services/api/scripts/migrate_db.py` (testlari backlog'da).
- Web'ni kalitsiz ko'rish: `VITE_MOCK_API=1 npm run dev` (xotiradagi API va soxta sessiya,
  `src/dev/mock.ts`; production build'ga kirmaydi).
- Node: `apps/web/.nvmrc` (24); CI ham shuni o'qiydi. Python: 3.12 (`pyproject.toml`).
- **Hal qilingan: Windows Smart App Control (SAC).** 2026-09-29 gacha SAC shu dev
  mashinada `alembic.exe`, `mypy`, `npm run build` va `npm run dev` ni bloklagan edi
  (oxirgi ikkalasi rollup'ning `rollup.win32-x64-msvc.node` fayli sababli). Microsoft'ning
  Smart App Control FAQ'iga ko'ra, SAC yoqilgan holda alohida faylga istisno qo'shib
  bo'lmaydi, shuning uchun SAC o'chirildi. O'chirish qaytariladi: SAC'ni Windows
  Security ichidan qayta yoqish mumkin, lekin **qayta yoqilsa, o'sha bloklar qaytadi.**
  - O'chirilgandan keyin tekshirilgan (2026-09-29): `npm run dev` — sahifa HTTP 200
    bilan ochildi; `npm run build` — exit 0; `mypy app scripts` — exit 0 (39 fayl);
    `alembic.exe --version` va `python -m alembic --version` — ikkalasi ishladi.
