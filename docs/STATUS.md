# Holat — Movie Match

Oxirgi yangilanish: 2026-11-13 (**F4 tuzatishlari jonli (`556e676`)**: xabarga vaqt chegarasi — birinchi belgi 25 s, jami 45 s, aks holda "band" matni (TZ 1.28); faqat javob joylashtirgan kartochkalar; `genres` argumenti va kirish gapi (TZ 1.29). Deploy'dan keyingi 10 xabar: 10/10 `done`, birinchi belgi median **3.54 s** (11-12 da 20.2 s), janr so'rovlari to'g'ri, ortiqcha kartochka yo'q; FR-8 "2 s" mezoni hali bajarilmagan — pastda); 2026-11-11 (**F4 `main` da va jonli: migratsiya `0005` asosiy bazada (18 → 20 jadval), merge `b179b30`, `/health` shu commit'ni ko'rsatadi; qo'lda tekshiruv test akkauntlarini kutmoqda. Ikkala Supabase loyihasi to'xtagan edi: ping `/health` bazaga tegmaydi — ping `/health/db` ga o'tadi**, `docs/deploy.md` 4–5-bo'lim); 2026-11-11 (**F4 kodi tayyor, `f4-assistant` branch'ida, CI yashil (run 107)** — assistant provayder interfeysi orqali, Gemini 3.5 Flash-Lite, ADR 0009; tafsilot pastda); 2026-10-23 (**"sabab" yaqinlikni bildiradi**, TZ 1.27 + ADR 0008: sabab = kattalik ≤ 0.35 σ **va** yo'nalish ≥ 0.40 σ, farq = kattalik ≥ 1.0 σ, orasi jim; sabab prompti qayta yozildi, taqqoslash shakllari taqiqlandi; izoh keshi (15 qator) bekor qilindi. Sabab: jonli saytda "WHY IT SUITS YOU" ostida "much gentler than you usually prefer" turdi — ziddiyat qoidaning o'zida edi, chunki eski sabab yo'nalishni o'lchardi. O'lchov: eski qoidada `d394a840` uchun 500 filmdan 495 tasi sabab tomonida edi → yangi qoidada uch akkauntda 44.8 / 50.6 / 66.2%. gate 2026-10-23 da yashil (run 100) va `441211d` jonli; kesh deploy'dan keyin qayta tekshirildi — 0 qator, o'chirishga narsa yo'q — pastga qara); 2026-10-15 (**bitta simmetrik trait qoidasi**, TZ 1.23: sabab 0.5 σ, farq 1.0 σ, sabablar ustun, ikkalasi bo'lmasa jim; API `reasons` → `named_traits` + `trait_side`; farq uchun alohida prompt. Sabab: "Outside your usual taste" ostidagi filmda "sizga mos" izohi. O'lchov va asos: `docs/phase-2-status.md`. **5-bosqich ham shu bilan yopildi** — 82 va 85 orasidagi 3 ball endi sabab emas. **Izohlar jonli xizmatda yaratilyapti** — 2026-10-13 dagi "yaratilmayapti" yozuvi tasdiqlanmagan taxmin edi (Render log'i o'qilmagan): keshda `gemini-3.5-flash-lite` 2026-10-15 03:58–03:59 (UTC) da yozgan 3 qator bor edi (Aliens `en`, Godzilla `en` va `uz`) — ya'ni ziddiyat haqidagi xabardagi Godzilla jumlasi ham haqiqiy generatsiya, zaxira shablon emas. 10–13 oktabr orasidagi bo'shliq nosozlik emas, urinish bo'lmagani. Kesh endi bo'sh: 10 qator foydalanuvchi qarori bilan o'chirildi (eski qoida va eski prompt bilan yozilgan edi), har biri keyingi so'rovda ~$0.00013 ga qayta yaratiladi. Keyingi: 3-bosqich (qidiruv)); 2026-10-13 (**tester fikri**: zaxira jumlasi matni tuzatildi (`c70f1fc`), hero teginishda to'xtaydi (`f22d548`); tavsiyalarning eski tomonga og'ishi o'lchandi — ANN neytral, match 34%, **MMR 40%** — qaror kutilmoqda (`docs/phase-2-status.md`); recency jarimasi `w = 0.02` qo'yildi (TZ 1.21); izoh indikatori tuzatildi — API sababni beradi (TZ 1.22). **Ochiq:** NSFW bandi. ~~izohlar 2026-10-10 dan keyin yaratilmayapti~~ — **yopildi 2026-10-15**, pastga qara); 2026-10-10 (**uyqu: Render Starter o'rniga cron-job.org ping**, foydalanuvchi qarori); 2026-10-10 (**FR-3 bajarildi**: foydalanuvchi jonli saytda onboarding'dan o'tdi, kutish sezilmadi — alohida vaqt o'lchovi qilinmaydi, foydalanuvchi qarori); 2026-10-09 (**logo, yuklanish holatlari va o'tish effektlari tugadi**, dialog portal tuzatishi; oxirgi commit `a6dffc6`, CI run 61 yashil); 2026-10-08 (**F3 qo'lda tekshiruvi**: onboarding 3:10, (a) xatosi tuzatildi, tarmoq kechikishi va Lighthouse deploy'dan keyin; **deploy — F4 dan oldin alohida qadam**, tayyorgarlik `docs/deploy.md`); 2026-10-06 (**dizayn v2 yopildi**: 0–5 bosqich bajarildi va tasdiqlandi; keyingi qadam — F3 qo'lda tekshiruvi); 2026-10-06 (4-bosqich: Movie DNA radial diagrammasi; hero: "For you" 6-filmdan, mobil boshqaruv rasm ustida; 5-bosqich: qidiruv kartalari Home bilan bir xil; 3-bosqich yakuni: hero kicker va jumla, balandlik pasaytirildi; "good" interfeysdan olindi, TZ 1.16; 4-bosqich faqat radial DNA, TZ 1.15); 2026-10-05 (dizayn 3-bosqich: Home hero, `backdrop_path` har filmda); 2026-10-05 (film sahifasi: daraja — panel sarlavhasi; "yaxshi" 15%, TZ 1.14); 2026-10-05 (FR-5: match darajasi, TZ 1.13; dizayn 2-bosqich tuzatishlari); 2026-10-04 (dizayn 1-bosqich); 2026-10-02 · F1 ma'lumot qismi yopildi (500 film) · Tillar: en standart, uz, ru (TZ 1.8) · **LLM provayderi tanlanmagan** (ADR 0006)

Bitta sahifada: qaysi faza tugagan, nima chala, keyingi qadam. Tafsilotlar faza
hisobotlarida: `docs/phase-1-status.md`, `docs/phase-2-status.md`, `docs/phase-3-status.md`. Fazalar ro'yxati:
`docs/prompts/README.md`. Xarajatlar: `docs/costs.md`.

## Fazalar

| Faza | Holat |
|---|---|
| F0 — Poydevor | **Tugagan** (`b2a4d35`, gate o'tgan) |
| F1 — Ma'lumot va Movie DNA | **Kod tugagan, ma'lumot chala.** 1-bosqich bajarildi (2026-10-01): 50 film trait oldi (sync, 0 yiqildi), qo'lda ko'rik **o'tdi** — 50 dan 3 tasi bahsli, chegara 5. 2-bosqich: traitlar 500 / 500 (13 film Google filtri bilan bloklanib almashtirildi); 2-bosqich ≈ $0.28 standart tarifda, bepul tarifda $0. Embedding 500 / 500 (ikki run, $0.0182 standart, bepul tarifda $0); missing count 0. Qo'shnilar ko'rigi **o'tdi** (2026-10-02). **Ma'lumot qismi yopildi.** Ma'lum muammo: Spirited Away qo'shnilari studiya bo'yicha to'planadi (F2 qo'lda tekshiruvida qaraladi) |
| F2 — Tavsiya dvigateli | **Tugagan** (2026-10-02). Qo'lda tekshiruv **o'tdi** (foydalanuvchi xulosasi): "For you" dagi 20 filmdan deyarli hammasini ko'rardi; qolgan bo'limlar "yomonmas". Qo'lda match hisobi va 5 izohni sabablar bilan solishtirish **bajarilmadi** — formula testda (`test_match_is_recomputable_from_stored_numbers`, har commit'da), izohning mazmuni test qilinmagan. Izoh narxi o'lchangan: $0.00013 bittasi. Tekshiruvda topilgan `POST /watchlist` 500 xatosi tuzatilgan (`01d08f7`); izohlar limiti interfeysda ko'rinmaydi (backlog, TZ 1.9); feed 45 bahoda ~15 s (F5 ishi) |
| F3 — Web ilova | **Kod tugagan, `main` da (`66bc7a0`), CI yashil. Qo'lda tekshiruv chala.** Foydalanuvchi so'rovi bilan F2 qo'lda tekshiruvidan oldin boshlangan (prompt sharti bajarilmagan). Onboarding 3:10 (2026-10-08, maqsad < 3 daqiqa): 58 s — baho saqlashni kutish (Singapurgacha tarmoq). **FR-3 bajarildi (2026-10-10):** jonli saytda (deploy'dan keyin) foydalanuvchi onboarding'dan o'tdi, sahifalar orasida kutish sezilmadi; alohida vaqt o'lchovi qilinmaydi (foydalanuvchi qarori). Tekshiruvda topilgan (a) xato — eskirgan kesh onboarding'ga qaytarardi — tuzatildi (`3d7a976`). Tafsilot: `docs/phase-3-status.md` |
| Tillar (TZ 1.8, 2026-10-02) | **Kod tayyor.** Ingliz — standart til va kalitlar manbasi (`apps/web/src/i18n/en.ts`); o'zbek — ikkilamchi; rus — qo'shimcha, **ko'rilmagan qoralama**. Menyu: English, O'zbek, Русский; tanlov `localStorage` da saqlanadi, brauzer tili aniqlanmaydi. API: `lang` = `en` \| `uz` \| `ru`, standart `en`; izohlar rus tilida ham (har til alohida kesh). Film ma'lumoti ingliz tilida qoladi (backlog) |
| Dizayn v2 (`docs/ui.md`) | **Yopildi** (2026-10-06): 0–5 bosqich bajarildi va tasdiqlandi; oxirgi commit `e9a7f9f`, CI yashil |
| Logo, yuklanish, o'tishlar (`docs/ui.md`: Logo, Yuklanish holatlari, O'tish effektlari) | **Tugadi** (2026-10-09). Uch bosqich: logo, favicon, ikonkalar va manifest (`d84e09c`, run 58); belgi bilan yuklanish holatlari (`d692ec4`, run 59); qisqa o'tishlar (`f1125ad`, run 60); dialog `document.body` ga portal — Rate dialogi panellar ostida qolardi, oldindan bor nuqson (`a6dffc6`, run 61). Hammasi CI yashil. CLS 0, axe 0 (mock, haqiqiy Chrome); testlar 246. Sahifa o'tishi: `BrowserRouter` da `viewTransition` hech qachon ishlamagan — endi 120 ms opacity; to'liq o'tish backlog'da |
| Deploy (F4 dan oldin, alohida qadam) | **Ishlayapti** (2026-10-08). **2026-11-11: ikkala Supabase loyihasi faolsizlikdan to'xtagan edi** — jonli `/health` 200, `/health/db` 500; foydalanuvchi tikladi. Sabab: cron-job.org ping'i `/health` ga boradi, u bazaga tegmaydi; Frankfurt'ni CI ishlatmaydi (runner konteyneri), faqat mahalliy testlar. Yechim: ping manzili `https://movie-match-api-mgdn.onrender.com/health/db` (`SELECT 1`, 500 da cron-job.org xat yuboradi; Supabase buni yetarli deb hisoblashi kafolatlanmagan — ogohlantirish xati kelsa keyingi qadam), Frankfurt uchun ping yo'q, ataylab (`docs/deploy.md` 4–5-bo'lim). Avvalgi holat: web https://movie-match.pages.dev (Cloudflare Pages), API https://movie-match-api-mgdn.onrender.com (Render Free, Singapur). Tayyorgarlik (2026-10-08, foydalanuvchi qarori): fazalar tartibida deploy F5 ichida, F5 esa F4 gate'ini talab qiladi. Alohida qilinadi, chunki F3 ning ochiq o'lchovlari (FR-3 onboarding, feed tezligi, Lighthouse) faqat jonli URL'da o'lchanadi. API — Render Free, Singapur (`render.yaml`); web — Cloudflare Pages (keyin). F5 ning telemetriya, metrika, "wrong" tugmasi va testerlar qismi F5 da qoladi. Qadamlar: `docs/deploy.md` |
| F4 — AI assistant | **Kod tugagan, jonli, qo'lda tekshiruv o'tdi; FR-8 ning "birinchi belgi 2 s" mezoni bajarilmagan.** Jonli `556e676` (merge `f4-fixes-2`, 2026-11-12 19:27 UTC; birinchi merge `b179b30`, 2026-11-11). Qo'lda tekshiruv 2026-11-11: 72 xabar, 3 test akkaunti, $0.1086; off-topic va 3 injection hammasi `refusal: off_topic`; 6 xato (5 ta 503, 1 blocked). Keyin ikki tuzatish to'plami: `f4-fixes` (`84ac291`: 503 da bir marta qayta urinish, `reset` hodisasi, bosqich vaqtlari log'da) va `f4-fixes-2` (`556e676`: xabarga 25 s / 45 s chegara va "band" matni, to'xtab qolgan oqim qayta uriniladi, kesilgan chaqiruv tokenlari taxminan yoziladi — TZ 1.28; faqat javob joylashtirgan kartochkalar; `search_movies` ga `genres` va tool'dan oldin kirish gapi — TZ 1.29; ADR 0009 qo'shimchalari). Deploy'dan keyingi o'lchov (2026-11-12 19:33–19:34 UTC, 10 xabar): 10/10 `done`, xato 0, birinchi belgi median **3.54 s**, janr so'rovlarida hamma kartochka so'ralgan janrda. Zaxira model (1e) qilinmadi (foydalanuvchi qarori). Migratsiya `0005` asosiy bazada (pastda). Prompt sharti "F3 gate yashil" to'liq emas: film sahifasining jonli Lighthouse o'lchovi (F3 band 5) F4 bilan parallel o'lchanadi, foydalanuvchi qarori 2026-11-11. Assistant `LLM_PROVIDER` orqali ishlaydi, Claude Sonnet 5 o'rniga Gemini 3.5 Flash-Lite (ADR 0009, foydalanuvchi qarori). Limit 30 / UTC kun (TZ o'zgarmagan). Yangi: `POST /assistant/chat` (SSE), `recommend.search`, migratsiya `0005` (`assistant_turns`, `assistant_usage`), web `/assistant`. Fiksturalar Gemini stream shaklida qo'lda yozilgan, haqiqiy chaqiruvdan yozib olinmagan |
| F5 va keyingilari | Boshlanmagan |

## Oxirgi gate natijasi

| | |
|---|---|
| **Jonli o'lchov, `556e676` deploy'idan keyin (2026-11-12 19:33–19:34 UTC)** | Ruxsat etilgan 10 pullik xabar, har biri yangi suhbatda, 3 test akkaunti; mijoz tomonidagi o'lchov. **10/10 `done`**, `error` 0, `reset` 0. Birinchi belgi: 6.69, 10.11, 3.37, 3.54, 3.47, 3.12, 3.25, 13.49, 3.54, 4.03 s → **median 3.54 s**; jami median 4.15 s (eng uzuni 14.07 s). Kartochkalar: har javobda 2–3 ta, hammasi javob ichida joylashtirilgan. Janr: "A tense thriller" → 2/2 Thriller; "A musical I can sing along to" → 2/2 Music (The Sound of Music, The Chorus); "Мюзикл на вечер" → 3/3 Music (Whiplash ham — TMDB uni Music deydi); qo'rqinchli film (uz) → 3/3 Horror; romantik komediya (uz) → 2/2 Romance + Comedy; komediya → 3/3 Comedy; animatsiya (ru) → 3/3 Animation. Kirish gapi 10 javobning hammasida bor. **Render log'i (o'qildi 2026-11-13):** 10 ta `assistant timing` qatori, hammasi `end=done`, `retries` 0. Server tomonidagi median: `prepare` 0.01 s, birinchi chaqiruv **1.29 s** (0.80–10.31), `search` 0.08 s, ikkinchi chaqiruv **1.65 s** (1.09–8.20), birinchi belgi **2.55 s** (2.13–12.55), jami 3.16 s. Mijoz − server farqi median 0.99 s (tarmoq, JWT, limit yozuvi; birinchi xabarda 3.34 s). **Kirish gapi birinchi chaqiruvda kelmayapti:** 10 xabarning hammasida birinchi matn qidiruvdan keyin, ikkinchi chaqiruv ichida keldi (birinchi chaqiruv + qidiruvdan 0.8–7.9 s keyin) — ko'rinadigan kirish gapini ikkinchi chaqiruv yozmoqda, TZ 1.29 maqsadi (birinchi belgi qidiruvni kutmaydi) bajarilmagan. Narx: o'rtacha 4 713 / 169 token, **$0.00184** xabar — hammasi `new_conversation: true` bilan yuborilgan, ya'ni kontekstsiz; suhbat ichidagi o'rtacha ~$0.00193 (taxmin, `docs/costs.md`) |
| **CI va deploy (`f4-fixes-2`, 3 commit → `main` `556e676`)** | 2026-11-12: branch'da **gate run 113** yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/43288690962), coverage annotatsiyasi **`assistant.py` 98%**, **`app/services` 98%**; `main` da **gate run 114** yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/43290408031). `/health` → `556e67630a609a5c1eedf416d2f83487dc448eb9` (19:31:53 UTC), `/health/db` 200. Mahalliy (DB testlarisiz, Frankfurt to'xtagan): `ruff check` 0, `ruff format --check` 0, `mypy app scripts` 0 (51 fayl), pytest **382 o'tdi / 258 skip**; web `eslint` 0, `tsc` 0, `vitest` **336 / 336**, `npm run build` 0. Yangi integratsiya testlari (vaqt chegarasi 2, janr va kirish gapi 2) faqat CI'da yurdi |
| **Render log'i, 2026-11-12 16:27–16:34 UTC (`84ac291`, 10 xabar)** | 9 ta `assistant timing` qatori (birinchi xabar log nusxasida yo'q, qayta deploy paytiga tushgan). Median: `prepare` 0.02 s, birinchi chaqiruv **8.96 s** (5.87–19.09), `search` 0.09 s, ikkinchi chaqiruv **16.27 s** (6.09–40.21), birinchi belgi **17.68 s** (14.71–39.10), jami 33.32 s. Bizning kod ~0.1 s, qolgani Gemini kutishi. `retries` jami 2 (ikkalasi ikkinchi chaqiruvdagi 503; biri tiklandi). Xatolar: (1) 16:32:43 — ikkinchi chaqiruv birinchi so'zlardan keyin to'xtab qoldi, 30 s chegarada `TimeoutError`; xarajat qatorida `requests=1`, ya'ni kesilgan chaqiruv tokenlari yozilmagan; (2) 16:33:40 — ikkinchi chaqiruvda ikki marta `503 UNAVAILABLE` ("high demand"). Blocked yo'q |
| **CI va deploy (`f4-fixes` → `main` `84ac291`)** | 2026-11-12: branch'da **gate run 111** yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/43256399880), coverage `assistant.py` 98%, `app/services` 98%; `main` da gate run 112 yashil; `/health` → `84ac291…` |
| **F4 qo'lda tekshiruvi (2026-11-11 18:47–18:59 UTC, `b179b30`)** | 72 xabar, 3 test akkaunti (har birida 12 baho). Off-topic va 3 injection → `refusal: off_topic`. Birinchi belgi median 4.48 s (10 so'rov, 3.0–16.0 s). Narx (Render log'i): jami $0.1086, oddiy xabar $0.00164 (4 393 / 128 token), off-topic $0.00055, kesh 0. Xatolar 6: 5 ta `503 UNAVAILABLE` (hammasi ikkinchi chaqiruvda, oqim o'rtasida), 1 `blocked` (sabab log'da yo'q edi). Sifat: joylashtirilmagan kartochkalar, janr filtri yo'q edi (musical → Ratatouille, thriller → Bambi) |
| **Asosiy baza, migratsiya `0005` (2026-11-11)** | `migrate_db.py main` ga tegilmadi (u `users` bo'sh bo'lmasa to'xtaydi). Foydalanuvchi tasdiqlagan usul: `alembic upgrade 0004:head --sql` chiqargan SQL (2 `CREATE TABLE`, 1 indeks, `alembic_version` yangilanishi) bitta tranzaksiyada; `SET lock_timeout = '5s'`, `SHOW lock_timeout` sessiyada ham tranzaksiya ichida ham `5s`; `UPDATE 1`. Oldin: alembic `0004`, **18 jadval**, users 10, ratings 82, movies 5000, explanations 7, boshqa sessiyalarning `users` dagi lock'i 0, idle in transaction 0. Keyin (yangi ulanish): alembic `0005`, **20 jadval** (+ `assistant_turns`, `assistant_usage`, ikkalasi 0 qator), qolgan sonlar o'zgarmagan; `alembic current` → `0005 (head)` |
| **Deploy (`main`, `b179b30`, merge `f4-assistant`)** | 2026-11-11: Render `autoDeployTrigger: checksPass` bilan deploy qildi, ya'ni `main` dagi gate o'tgan; run raqami o'qilmadi (GitHub anonim limiti tugagan edi). `/health` → `commit b179b303885ee47eb2d68f2776b5eed2e5ebde01`, `/health/db` 200, `POST /assistant/chat` token'siz → 401 |
| **CI (`f4-assistant`, `9abeee8`, F4 — assistant, 8 commit)** | **Yashil**, 2026-11-11: **gate run 107**, https://github.com/smasheverybody99-hue/movie_match/actions/runs/43008824105 — hamma qadam o'tdi. Coverage CI annotatsiyasidan o'qildi (yangi: `::notice`, log login talab qiladi): **`app/services/assistant.py` 98%**, **`app/services/` 98%** (shart 85%). Testlar soni o'qilmadi (log yopiq). Oldin qizil: run 102 (`: any` tekshiruvi CSS'dagi `overflow-wrap: anywhere` ga tushdi), 103 va 104 (pytest; sababi log'da, o'qib bo'lmadi: numpy taste vektori `if` da va `test_auth` ro'yxatida `/assistant/chat` yo'q edi — ikkalasi tuzatildi), 105 (injection testidagi `"reveal"` sharti trait lug'atiga tushdi; test xatosi, shart aniq ibora bilan almashtirildi). Shu yerdan boshlab yiqilgan test CI'da `::error` annotatsiyasi bo'ladi va login'siz o'qiladi. Mahalliy: `ruff check` 0, `ruff format --check` 0, `mypy app scripts` 0 (51 fayl), unit + contract **353 / 353**; web `eslint` 0, `tsc` 0, `vitest` **333 / 333** (28 fayl), `npm run build` 0. **Mahalliy DB testlari yurmadi:** Frankfurt test bazasi yana to'xtagan (`tenant/user postgres.bixarelbydwinmfhmaka not found`, 2026-10-22 dagidek), assistant integratsiya testlari faqat CI'da yurdi |
| **CI (`main`, `441211d`, TZ 1.27 — "sabab" yaqinlikni bildiradi, 3 commit)** | **Yashil**, 2026-10-23: **gate run 100** (main), https://github.com/smasheverybody99-hue/movie_match/actions/runs/39911392499 — 20 / 20 qadam, `pytest` **550 / 550** (CI runner'ning pgvector konteyneri bilan, skip yo'q), `npm test` **321 / 321**, `app/services` coverage qadami (`--fail-under=85`) o'tdi. Oldin branch'da: **gate run 99** (`tz-127-closeness-reasons`), https://github.com/smasheverybody99-hue/movie_match/actions/runs/39909020070 — ham yashil, o'sha commit. Aniq coverage foizi yozilmadi: GitHub run log'ini anonim bermaydi (403), `gh` CLI o'rnatilmagan; mahalliy o'lchov (10 test yiqilgan yurishda) `app/services` uchun 798 satrdan 19 tasi qoplanmagan = **97.6%**. **Deploy tasdiqlandi:** API `/health` → `commit 441211db5f51807d1badbf7d40c0b45c7eb7cb8f`; web production bundle `/assets/index-CraZPu-J.js` + `/assets/index-7q-UyQ7Q.css`, ichida uch tilda yangi zaxira jumlasi bor ("this film sits at your level", "ayni sizning darajangizda", "стоит на вашем уровне") va eski taqqoslash matni yo'q. **Izoh keshi:** deploy'dan keyin qayta tekshirildi — **0 qator**, ya'ni 2026-10-22 dagi tozalashdan keyin eski qoida bilan bitta ham izoh yaratilmagan, o'chirishga narsa yo'q (zaxira: bo'sh massiv). **Branch o'chirildi** (`git push origin --delete tz-127-closeness-reasons`), lekin Cloudflare preview deploy'i o'chmaydi: `https://tz-127-closeness-reasons.movie-match.pages.dev` hamon 200 qaytaryapti — panelda Deployments'dan o'chirilishi kerak (foydalanuvchi qadami) |
| **Mahalliy, 2026-10-23, TZ 1.27 — chala, qayta yurgizilishi kerak** | **Test bazasi qaytarildi** (ulandi: 18 jadval, alembic `0004`) — 2026-10-22 dagi blokirovka yopildi. To'liq `pytest --cov=app/services --cov=app/pipelines` yurgizildi (44 daq 26 s): **540 o'tdi, 10 yiqildi**, hammasi `tests/integration/test_explanations_cache.py` da — fiksturasi eski cut'lar uchun qurilgan edi (TZ 1.27 shu testlar skip bo'lgani uchun ularni ko'rmagan). Coverage o'sha yurishda: `app/services` + `app/pipelines` **89%** (matching.py 100%, explain.py 89%). Fikstura tuzatildi (`c55d35a`), o'sha fayl endi **14 / 14** (1 daq 57 s). API: `ruff check` 0, `ruff format --check` 0 (111 fayl), `mypy app` 0 (47 fayl). Web: `eslint --max-warnings 0` → 0, `vitest` **321 / 321** (27 fayl, ketma-ket yurgizilganda flake yo'q), `npm run build` 0. **Chala:** to'liq `pytest` + coverage tuzatishdan keyin qayta yurgizilmadi (foydalanuvchi so'rovi bilan to'xtatildi) — gate shuning uchun yashil emas. CI run yo'q, push qilinmadi; `main` da mahalliy `554c14f` + `c55d35a` turadi. **Keyingi qadam:** to'liq pytest + coverage → yashil bo'lsa push → CI run va `/health` commit'ini shu jadvalga yozish |
| **Mahalliy, 2026-10-22, TZ 1.27 (ADR 0008)** | **Chala — test bazasi yo'q.** API: `ruff check` 0, `ruff format --check` 0 (111 fayl), `mypy app` 0 (47 fayl), `pytest` → **325 o'tdi, 225 o'tkazib yuborildi** (`TEST_DATABASE_URL` bo'sh qilib yurgizilganda). Web: `eslint --max-warnings 0` → 0; `vitest` → 27 fayl, **321 test**, hammasi o'tgan (to'liq to'plam bir marta 12 ta yiqildi — Onboarding va Feed, uch to'plam bir vaqtda ishlaganidan; alohida yurgizilganda 48 / 48 o'tdi). **`app/services/` coverage o'lchanmadi:** uni ikkita DB testi beradi. CI run **yo'q** — push qilinmadi |
| **Blokirovka: test bazasi javob bermaydi** (2026-10-22) | `TEST_DATABASE_URL` → Supabase, Frankfurt (`eu-central-1`), loyiha ref `bixarelbydwinmfhmaka`. Pooler javobi: `asyncpg.exceptions.InternalServerError: (ENOTFOUND) tenant/user postgres.bixarelbydwinmfhmaka not found` — ya'ni server loyihani topmayapti (bepul loyiha to'xtatilgan yoki o'chirilgan; oxirgi ishlatilishi ~2026-10-16). DNS ishlaydi, asosiy baza (Singapur, `pzuwzispquuxemqdjcjr`) ishlayapti. Shu sababli 225 ta DB testi (`db_session` bilan) va `test_migrations` yurgizilmadi, coverage o'lchanmadi. **Kerak:** Supabase panelida Frankfurt loyihasini qayta ishga tushirish (yoki yangi test loyihasi va yangi `TEST_DATABASE_URL`) — foydalanuvchi qadami |
| CI (`main`, `57503bf`, tester fikri + bitta simmetrik trait qoidasi, 10 commit) | **Yashil**, 2026-10-15: gate run 87, https://github.com/smasheverybody99-hue/movie_match/actions/runs/38729464822 (branch run 86 ham yashil: `tester-feedback-trait-rule`). **Deploy tasdiqlandi**: API `/health` → `commit 57503bf` (16:47, Render), web bundle'da "Something different" / "Boshqacha kinolar" / "Другое кино" bor, eski "Outside your usual taste" yo'q |
| CI (`main`, `a6dffc6`, dialog portal — logo, yuklanish va o'tishlar ishining oxirgi commit'i) | **Yashil**, 2026-10-09: gate run 61, https://github.com/smasheverybody99-hue/movie_match/actions/runs/37890967059 |
| CI (`main`, `f1125ad`, o'tish effektlari) | **Yashil**, 2026-10-09: gate run 60, https://github.com/smasheverybody99-hue/movie_match/actions/runs/37890208197 |
| CI (`main`, `d692ec4`, yuklanish holatlari) | **Yashil**, 2026-10-09: gate run 59, https://github.com/smasheverybody99-hue/movie_match/actions/runs/37884921901 |
| CI (`main`, `d84e09c`, logo) | **Yashil**, 2026-10-09: gate run 58, https://github.com/smasheverybody99-hue/movie_match/actions/runs/37879723011 |
| CI (`main`, `9b3d9d3`, F3 onboarding (a) tuzatishi `3d7a976` + hisobot) | **Yashil**, 2026-10-08: gate run 49, https://github.com/smasheverybody99-hue/movie_match/actions/runs/37735098960 |
| CI (`main`, `38a3cb4`, hero tuzatishlari) | **Yashil**, 2026-10-06: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37414071966 |
| CI (`main`, `5fd524e`, 5-bosqich) | **Yashil**, 2026-10-06: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37413183633 |
| CI (`main`, `963404b`, Home hero) | **Yashil**, 2026-10-05: gate run 43 |
| CI (`main`, `a4fb69a`, daraja — panel sarlavhasi, "yaxshi" 0.15) | **Yashil**, 2026-10-05: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37348808980 |
| CI (`main`, `d90cc6e`, FR-5 darajasi + STATUS) | **Yashil**, 2026-10-05: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37274508333 (`0874314` shu push bilan, alohida run'siz) |
| CI (`main`, `1033ed9`, dizayn 2-bosqich tuzatishlari) | **Yashil**, 2026-10-05: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37266785192 |
| CI (`main`, `b28b9da`, F2 yopilishi) | **Yashil**, 2026-10-02: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36989348804. `app/services/` coverage ≥ 85% (`--fail-under=85` qadami o'tgan). **Aniq raqam o'qilmadi** (log GitHub login talab qiladi) — keyingi to'liq mahalliy run'da yoziladi |
| CI (`main`, `4ccd878`) | **Yashil**, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36609806293 (provayder interfeysi, katalog 500, costs.md, Alembic log tuzatishi) |
| CI (`main`, `852c767`, provayder interfeysi) | **Qizil**, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36603649367 — `test_migrations` dan keyin `app.cost` logi o'chib qolgan; `4ccd878` da tuzatilgan |
| CI (`main`, `66bc7a0`, F3 merge) | Yashil, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36599220279 |
| CI (`main`, `e9a7f9f`, DNA sahifasi yakuni — dizayn v2 ning oxirgi commit'i) | **Yashil**, 2026-10-06: gate run 47, https://github.com/smasheverybody99-hue/movie_match/actions/runs/37419205987 |
| CI (`main`, `f406b9b`, 4-bosqich) | **Yashil**, 2026-10-06: https://github.com/smasheverybody99-hue/movie_match/actions/runs/37418075454 |
| Web testlari | Mahalliy, 2026-10-06 (4-bosqich yakuni: blok markazda, ixcham statistika): 17 fayl, **219 test**, hammasi o'tgan. Avvalgi (4-bosqich, DNA): 17 fayl, 219 test, hammasi o'tgan; lint 0, build 0; CLS eng yomoni 0, axe 0. Avvalgi (hero tuzatishlari): 16 fayl, 210 test, hammasi o'tgan; lint 0, build 0; CLS eng yomoni 0 (chegara 0.1). Avvalgi (5-bosqich): 16 fayl, 209 test, hammasi o'tgan; lint 0, build 0. CLS eng yomoni 0 (chegara 0.1), axe 0, 320 da scroll yo'q, rus tili sig'adi. Avvalgi (3-bosqich yakuni): 16 fayl, 207 test, hammasi o'tgan; lint 0, build 0. 3-bosqich o'lchovi: CLS eng yomoni 0.0001 (chegara 0.1; aylanishda 0), axe 0, 320 da gorizontal scroll yo'q, rus tilida hero 320 da sig'adi. Avvalgi (Home hero): 16 fayl, 205 test, hammasi o'tgan; lint 0, build 0. Avvalgi (daraja — panel sarlavhasi): 15 fayl, 192 test, hammasi o'tgan; lint 0, build 0. Avvalgi (2-bosqich tuzatishlari): 15 fayl, 189 test, hammasi o'tgan; lint 0, build 0. Onboarding beqarorligining sababi topildi va tuzatildi (`docs/ui.md`, "2-bosqich, ko'rikdan keyingi tuzatishlar"): ko'p tapli testlar CPU'ga bog'liq, muddati o'tgan test keyingi testning DOM'ida ishlab qolardi, baholash qadamida effekt poygasi bor edi. Sun'iy CPU yuki ostida: Onboarding 8 / 8, to'liq to'plam 3 / 3 yashil |
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

**F4 (2026-11-13).** Kod jonli (`556e676`), qo'lda tekshiruv va ikki tuzatish to'plami
bajarildi (yuqoridagi jadval). Qolgani:
1. ~~Render log'i~~ — o'qildi 2026-11-13: $0.00184 xabar, bosqich vaqtlari yuqoridagi
   jadvalda; `docs/costs.md` dagi taxmin o'lchov bilan almashtirildi.
2. **FR-8 "birinchi belgi 2 s" bajarilmagan:** eng yaxshi o'lchovda ham median 3.54 s
   (mijoz), 2.55 s (server). Kirish gapi birinchi chaqiruvda kelmayapti (yuqorida).
   Birinchi belgi birinchi chaqiruvning javobini kutadi (Gemini). Qaror foydalanuvchida.
3. F4 faza hisoboti va F4 gate'i — foydalanuvchi qarori bilan; F5 boshlanmagan.
4. F3 band 5: film sahifasining jonli Lighthouse o'lchovi (LCP + INP), foydalanuvchi qo'lda.
5. Ixtiyoriy: Supabase panelida Frankfurt test loyihasini qayta yoqish (mahalliy DB testlari
   uchun; CI unga bog'liq emas). Uning parolini almashtirish — foydalanuvchi qarori.
- ~~F4 qo'lda tekshiruvi~~ (2026-11-11), ~~migratsiya `0005` va merge~~ (2026-11-11),
  ~~cron-job.org ping `/health/db` ga~~ (foydalanuvchi almashtirdi) — bajarildi.

0. ~~Test bazasini qaytarish, keyin gate va push~~ — **bajarildi 2026-10-23**: test bazasi
   qaytarildi, gate run 99 (branch) va run 100 (`main`) yashil, `441211d` jonli (API `/health`
   va Pages production bundle'i tasdiqlangan; yuqoridagi jadval). **Qoldi (foydalanuvchi):**
   Cloudflare panelida `tz-127-closeness-reasons` preview deploy'ini o'chirish — branch
   o'chirilgan bo'lsa ham URL ochiq turadi. Mahalliy to'liq `pytest` boshqa yurgizilmaydi:
   mashinada xotira yetmaydi (fon jarayoni ikki marta to'xtatildi), bu CI'ning ishi.
1. **Jonli saytni tekshirish (foydalanuvchi)** — https://movie-match.pages.dev, Render
   oldindan uyg'otilgan holda (`docs/deploy.md`, 3-bo'lim): yangi logo, favicon, yuklanish
   holatlari va o'tishlar (onboarding qadam almashinuvi brauzerda o'lchanmagan — shu yerda
   ko'riladi). Keyin jonli URL'dagi F3 o'lchovlari: ~~onboarding vaqti (FR-3 verdikti), har
   baho saqlanishi~~ — bajarildi (2026-10-10, yuqorida), Lighthouse (mobil va desktop). Server uxlamaydi: cron-job.org ping
   (quyida, 2026-10-10). Keyin — F4.
   **F3 qo'lda tekshiruvi** (`docs/phase-3-status.md`): oltala band bajarildi (2026-10-08).
   2, 3, 4, 6 o'tdi; 1-band (FR-3) jonli saytda o'tdi (2026-10-10, foydalanuvchi); 5 (Lighthouse) — jonli URL'da.
2. **Dizayn v2 yopildi** (2026-10-06, foydalanuvchi tasdiqladi): olti bosqichning
   hammasi (0–5) bajarildi va tasdiqlandi; har bosqich natijasi `docs/ui.md` da.
   FR-5: interfeysda daraja ikki holatda — "Strong match" (qizil, eng yaqin 5 film) yoki
   neytral "You and this film"; "good" hisoblanadi, ko'rsatilmaydi (TZ 1.16). Asos —
   pastdagi "FR-5 o'lchovi" va "35% → 15%".
   Match foizi (FR-5) bo'yicha qaror hali ochiq. Oldin bajarildi (2026-10-02): **sabablar katalogga nisbatan** (TZ 1.12, FR-5; match
   foizi o'zgarmagan) — "Why you" endi har filmda bir xil uchta trait emas. Eski 20 ta
   izoh (bitta foydalanuvchi) ruxsat bilan o'chirildi; yangilari yangi sabablar bilan
   yoziladi. Mahalliy API qayta ishga tushirilishi kerak. Match foizi taqsimoti o'lchandi
   (`docs/phase-2-status.md`): yoqmagan va yoqqan filmlar bir xil (~85%), 60% chegarasi
   deyarli hech narsani filtrlamaydi — FR-5 formulasi bo'yicha alohida qaror kutilmoqda.
2. **Rus tili: foydalanuvchi ko'rib chiqdi (2026-10-09), tuzatishlar kiritildi.** Hali
   ko'rilmagan, agent yozgan qismlar: janr nomlari (`genre.*`, 19 ta, ru va uz),
   `label_ru` "Накал эмоций" (radarda "Эмоциональный" sig'magani uchun, foydalanuvchi
   qarori) va yangi umumiy matnlar ("Вход временно недоступен…").
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

- Test bazasi: Supabase, Frankfurt (`eu-central-1`) — **2026-10-22 dan javob bermayapti**
  (pooler: `tenant/user ... not found`), shuning uchun DB testlari yurgizilmayapti; tafsilot
  va kerakli qadam yuqoridagi "Oxirgi gate natijasi" jadvalida. Asosiy baza: Singapur
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

## Keyingi qadam (2026-10-08)

Deploy tugadi (2026-10-08): web https://movie-match.pages.dev, API
https://movie-match-api-mgdn.onrender.com; CORS va Supabase redirect yangilangan. Keyingi
qadam — yuqoridagi "Keyingi qadam" 1: foydalanuvchi jonli saytni tekshiradi.

**Uyqu: Render Starter o'rniga bepul yechim** (foydalanuvchi qarori, 2026-10-10;
2026-10-09 dagi "testerlardan oldin Starter" qarorini almashtiradi). cron-job.org har 10
daqiqada `/health` ga so'rov yuboradi: Free instance 15 daqiqa trafiksiz uxlardi va
uyg'onishi ~34 s edi (DevTools, `docs/phase-3-status.md`) — endi uxlamaydi. Narxi $0, lekin:
oyiga ~744 soat 750 lik bepul limitdan (zaxira 6 soat), shuning uchun **workspace'da boshqa
bepul servis bo'lmasligi shart** — soatlar bo'linadi, limit tugasa hamma bepul servis oy
oxirigacha to'xtaydi. CPU 0.1 qoladi: feed ~3.1 s o'zgarmaydi. Trafik 5 GB/oy. **Starter**
($7/oy, 0.5 CPU) haqiqiy foydalanuvchilar paydo bo'lganda yoki soat limiti tig'izlashganda
ko'rib chiqiladi. Zaxira: Google Cloud Run, Singapur (uyg'onish 1–3 s, karta kerak,
ko'chirish 1–2 soat). Tafsilot: `docs/costs.md`, `docs/deploy.md` 5-bo'lim. Max-Age 7200 qilindi (2026-10-10); feed keshi — backlog'da (TZ, 2-bo'lim).
