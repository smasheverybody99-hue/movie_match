# Holat — Movie Match

Oxirgi yangilanish: 2026-11-27, Google OAuth (**consent screen tekshirildi** (foydalanuvchi): loyiha "Default Gemini Project" (`gen-lang-client-0014845015`), Publishing status = **Testing**, test users 4 ta / 100; **qaror: alfa Testing'da qoladi**, har tester Gmail'i Test users'ga qo'shiladi (foydalanuvchi), "Publish app" hozir bosilmaydi; F9a sharti: launch'dan oldin "In production"; brend tekshiruvi istalgan, majburiy emas, qaror — foydalanuvchi, 2026-12-08 gacha; scope'lar `email` + `profile`; pages.dev domeni va Supabase callback — `docs/prompts/phase-09a-web-launch.md`); 2026-11-24, alfa tayyorgarligi (**`mobile-reconnect` → `main` merge `fa16b7a`** (foydalanuvchi ruxsati): gate 175 va android run 19 yashil (release, imzo mos), `/health` → `fa16b7a` (16:42 UTC); **testerlar uchun APK: android run 19, `movie-match-fa16b7aca02c720d9d44ac6417fca001b9198e6e`** (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45438451887, 2026-12-08 gacha); `f6-mobile` va `mobile-reconnect` branch'lari o'chirildi; "Alfa tayyorgarligi (2026-11-29)" bo'limi qo'shildi; testerlar hozir 5+); 2026-11-24, F6 `main` da (**`f6-mobile` → `main` merge `d708751`** (foydalanuvchi ruxsati; API va web kodiga o'zgarish yo'q): gate 172 va android run 17 yashil (release, imzo mos), `/health` → `d708751` (16:23 UTC); android run 17 APK; **~7 s tuzatishi `mobile-reconnect`** (`32fd246`) — keyin merge qilindi, pastga qara); 2026-11-24, telefon sinovi (**F6 telefonda sinovdan o'tdi** — foydalanuvchi, Samsung Galaxy S9 (SM-G960F), Android 10 (API 29), One UI 2.5, xavfsizlik yamog'i 2022-03-01, android run 16 release APK: data notice, onboarding (kutish sezilmadi), feed, film sahifasi, qidiruv, assistant, DNA va Share, watchlist swipe, til, Google kirish ✅; samolyot rejimi — qulamadi, lekin internet qaytgach ~7 s javob yo'q (tekshirilmoqda); sovuq start normal; hisobot `docs/phase-6-status.md`; **`f6-mobile` → `main` merge'ga ruxsat**); 2026-11-24, kirish ishladi (**telefonda Google bilan kirish ishlaydi** — foydalanuvchi: Supabase **asosiy** loyihada Redirect URLs'da `com.moviematch.moviematch://login-callback` yo'q edi, 2026-11-24 da qo'shildi; `docs/setup-android.md`, "Muammo bo'lsa: kirish"; `test_data_notice_api.py` `main` kodida (`f24db17`) Frankfurt test bazasida **6 / 6**); 2026-11-24, API flag jonli (**`main` ga merge `f24db17`** (foydalanuvchi tasdig'i bilan; `cb6c6a7`, 5 fayl, `f6-mobile` dan hech narsa kirmadi): gate 168 yashil, `/health` → `f24db17` (15:25 UTC, merge'dan ~1 daqiqa keyin), `/me` token'siz → 401, jonli `/openapi.json` da `MeOut.assistant_enabled` (default true); branch o'chirildi; telefonda tab — foydalanuvchi tekshiradi; surib baholash — backlog, F8 sayqal); 2026-11-24, assistant (**F6 assistant `42afdb9`**, 243 test; android run 16 (release, imzo mos) va gate 164 yashil; tab `/me` `assistant_enabled` ga bog'liq); 2026-11-24, profil (**F6 profil commit'i `da618ce`**, 222 test; android run 13 (release) va gate 161 yashil; ikonka va qorong'i launch ekrani `e2880f9`); 2026-11-24, 9-commit (**F6 9-commit — Movie DNA `997f2b4`**, 211 test; android run 12 (release) va gate 160 yashil); 2026-11-24, 8-commit (**F6 8-commit — watchlist `6c9ba39`**, 192 test; android run 11 (release) va gate 159 yashil); 2026-11-24, 7-commit (**F6 7-commit — qidiruv va pastki menyu `0f48081`**, 174 test; android run 10 (release) va gate 157 yashil); 2026-11-24, kechroq (**F6 6-commit — film sahifasi `a14241f`**, 161 test; android run 9 (release, imzo mos) va gate 155 yashil); 2026-11-24, keyin (**F6 5-commit — feed `d37e822`**, 132 test; android run 8 va gate 153 yashil; **birinchi release APK**: sozlamalar ogohlantirishi yo'q, artifact `movie-match-d37e822…`, imzo `UPLOAD_CERT_SHA256` ga mos — foydalanuvchi `ANDROID_KEYSTORE_PASSWORD` ni keyin qo'shdi); 2026-11-24 (**F6 4-commit — onboarding `39678a8`**, 90 test, android run 7 va gate 150 yashil; **lekin APK debug**: run sozlamalarni ko'rmadi — `SUPABASE_URL` / `SUPABASE_ANON_KEY` variables ham, `ANDROID_KEYSTORE_*` secrets ham yo'q deb ogohlantirdi); 2026-11-23, tun, keyin (**F6 `main` ga merge `ae6f7ae`**, `/health` → `ae6f7ae`; release kaliti yaratildi; kirish ekrani `568fb47`, android run 6 yashil; **TZ 1.38**: web launch AI'siz — A varianti, kodi F9a da; F8 va F7 F9a dan keyin; release APK doimiy kalit bilan); 2026-11-23, tun (**TZ 1.37** (foydalanuvchi: karta bor, hozir $25 yo'q; testerlar 4 ta): alfa 2026-11-29 da kim bo'lsa, o'shalar bilan, 2026-12-06 gacha 12 bo'lmasa — "zaif signal"; Google Play (F9b) $25 topilguncha to'xtatilgan; testerlarga Android APK (`docs/testers-android.md`); web launch'ning pulsiz variantlari — tanlov kutilmoqda; **F6 boshlandi** (`f6-mobile`): Flutter 3.50.1 va Android SDK o'rnatildi, mahalliy debug build 15 daqiqada tugamadi (bo'sh RAM eng kami 181 MB) → APK CI'da, android run 1 yashil 5.0 daqiqa, gate 140 yashil); 2026-11-23, kech (**NSFW belgilandi** (foydalanuvchi, asosiy baza): `sensitive --apply --skip 255709,1232449` — belgilangan filmlar 0 → **14**, Hope va Young Hearts belgisiz; Oldboy, My Fault, Drawn Together belgilandi (testerlar orasida 18 dan kichiklar bo'lishi mumkin); **telefon rasmi: A qoladi, B yo'q** — LCP 2026-12-01 da qayta ko'riladi, barcha variantlar bilan (hero balandligi va joylashuvi ham); **Flutter 3.50** (CLAUDE.md, ADR 0001, README, `docs/setup-android.md`); yurist uchun ochiq masalalar "Web launch'dan oldin" bandida, birinchisi — ma'lumotlarni lokalizatsiya qilish); 2026-11-23 (**TZ 1.36**: `alpha_tester` kelgan hamma testerga (15 gacha), 70% va 15% hammasi bo'yicha; **bundle bo'lish** (`f3-perf-3`, `26f5e4e`): 161.6 → 155.4 KB gzip, harness 5 raund median 3.34 s / `main` 3.44 s, 3/5 tezroq — aniq emas, merge qilinmadi; matn 2.0–2.5 s da chiziladi, LCP TMDB rasmini kutadi; F6 o'rnatish rejasi `docs/setup-android.md` (o'rnatilmagan); maxfiylik siyosati, shartlar (uz, en) va TMDB xati qoralamalari `docs/legal-drafts/`, yurist uchun; NSFW `--apply` foydalanuvchi tanlovini kutadi); 2026-11-22 (**TZ 1.35 — testerlar 2026-11-29 gacha yig'iladi** (12 ta Android + Gmail, maqsad 15), alfa 2026-11-29 — 2026-12-13; qolgan sanalar +6 kun, oraliqlar o'zgarmagan: Play yopiq testi 8-dekabr (o'sha testerlar), alfa qarori 13-dekabr, web launch 15-dekabr, Play'ga ariza 22-dekabr, do'konda 29-dekabrdan oldin emas. Telefon rasmi C varianti (`f3-perf-2`, `ec173cc`) harness'da A dan tez emas — merge qilinmadi: Chrome kattalashtirilgan rasmni asl piksellari bo'yicha sanaydi, LCP baribir w780; `docs/phase-3-status.md`); **F3 band 5 qayta o'lchandi** (`f3-perf` dan keyin, jonli sayt): mobil LCP 5.2 / 3.5 / 3.5 s, median **3.5 s** (avval 4.6 s) — hali < 2.5 s emas; **INP median 96 ms** (5 o'lchov, eng yomoni 104 ms, Rate tugmasi) — **bajarildi**; F9a sharti: INP bor, LCP yo'q; `docs/phase-3-status.md`, "Re-measure after `f3-perf`"); **F5 `main` da**: migratsiya `0006` asosiy bazada (foydalanuvchi ruxsati, `0005` dagi usul: alembic 0005 → 0006, 20 → 22 jadval, mavjud qatorlar o'zgarmagan), `f5-alpha` merge qilindi — `6d5a4cf`, CI run 133 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45016443719), jonli: `/health` → `6d5a4cf`, web yangi bundle'da; `f3-perf` merge `0201d02`, CI run 132 yashil); 2026-11-18 (**F4 yopildi, TZ 1.34**: F3 band 5 o'lchandi (foydalanuvchi, 2026-11-17, jonli sayt, film sahifasi): mobil LCP 14.5 / 4.2 / 4.6 s, median **4.6 s** — talab < 2.5 s, **bajarilmadi**; desktop 1.4 s; INP o'lchanmagan. F4 ikki ochiq yozuv bilan yopildi: FR-8 birinchi belgi (TZ 1.33) va "film sahifasi mobil LCP 4.6 s, INP o'lchanmagan". Mobil LCP < 2.5 s va INP < 200 ms **F9a shartiga** ko'chdi. Rate / Save tugmalari telefonda joyida, nuqson emas: ular pastki menyu ustida qotirilgan panel. Sababi o'lchandi: zanjir "bundle → preflight + film so'rovi Singapurga → backdrop rasmi" ketma-ket; tuzatish `f3-perf` da — `docs/phase-3-status.md`, "Item 5 on the live site"); 2026-11-17 (**F5 kodi `f5-alpha` da** — foydalanuvchi qarori bilan Lighthouse kutilmadi; merge va `0006` asosiy bazaga ruxsatni kutadi; CI: run 128 yashil); 2026-11-17 (**TZ 1.33**: FR-8 mezoni boshqa yumshatilmaydi; F4 "FR-8 birinchi belgi mezoni bajarilmagan (33 xabar, median 3.62 s, 1 xato)" ochiq yozuvi bilan yopiladi, mezon **F9a shartiga** ko'chdi — pullik tarifda ≥ 30 xabar, ≥ 2 kun, o'tmasa web launch yo'q. Render log'i o'qildi: xato — Gemini'ning ketma-ket ikki 503 javobi, sekinlik Gemini'ning birinchi chaqiruvida (6.6–11.6 s); kod nuqsoni emas. F4 faqat Lighthouse raqamlarini kutmoqda); 2026-11-17 (**FR-8 mezoni TZ 1.32** — ≥ 30 xabar, ≥ 2 kun, median ≤ 3 s, p90 ≤ 15 s, xato 0; **ikkinchi kun o'lchovi**: 20 xabar, 1 xato, median 4.15 s; ikki kun birga 33 xabar, median **3.62 s** — **mezon bajarilmadi**, F4 yopilmagan. **Alfa Gemini bepul tarifida** — ADR 0004 istisnosi. **Sanalar +4 kun** (TZ 1.32): F4 19-noyabr, testerlar 23-noyabr, web launch 9-dekabr, Play'ga ariza 16-dekabr); 2026-11-13 (**F4 yakuniy o'lchovi**: `f56ffa5`, 10 xabar, xato 0, birinchi belgi median **2.95 s** — 2 s mezoni bajarilmadi, TZ (a) matni taklif qilindi; hisobot `docs/phase-4-status.md`; F4 yopilmagan. **TZ 1.31**: do'konga ariza F7/F8 ni kutmaydi, do'konda 19-dekabrdan oldin emas, iOS yanvarda, launch uchun 15% va 70%); 2026-11-13 (**roadmap tezlashtirildi, TZ 1.30**: F4 15-noyabr, testerlar 19-noyabr, web launch 5-dekabr, do'konlarga ariza 12-dekabr; qurish alfa paytida, ochiq launch alfadan keyin; F9 → F9a + F9b — "Keyingi qadam"); 2026-11-13 (**F4 tuzatishlari jonli (`556e676`)**: xabarga vaqt chegarasi — birinchi belgi 25 s, jami 45 s, aks holda "band" matni (TZ 1.28); faqat javob joylashtirgan kartochkalar; `genres` argumenti va kirish gapi (TZ 1.29). Deploy'dan keyingi 10 xabar: 10/10 `done`, birinchi belgi median **3.54 s** (11-12 da 20.2 s), janr so'rovlari to'g'ri, ortiqcha kartochka yo'q; FR-8 "2 s" mezoni hali bajarilmagan — pastda); 2026-11-11 (**F4 `main` da va jonli: migratsiya `0005` asosiy bazada (18 → 20 jadval), merge `b179b30`, `/health` shu commit'ni ko'rsatadi; qo'lda tekshiruv test akkauntlarini kutmoqda. Ikkala Supabase loyihasi to'xtagan edi: ping `/health` bazaga tegmaydi — ping `/health/db` ga o'tadi**, `docs/deploy.md` 4–5-bo'lim); 2026-11-11 (**F4 kodi tayyor, `f4-assistant` branch'ida, CI yashil (run 107)** — assistant provayder interfeysi orqali, Gemini 3.5 Flash-Lite, ADR 0009; tafsilot pastda); 2026-10-23 (**"sabab" yaqinlikni bildiradi**, TZ 1.27 + ADR 0008: sabab = kattalik ≤ 0.35 σ **va** yo'nalish ≥ 0.40 σ, farq = kattalik ≥ 1.0 σ, orasi jim; sabab prompti qayta yozildi, taqqoslash shakllari taqiqlandi; izoh keshi (15 qator) bekor qilindi. Sabab: jonli saytda "WHY IT SUITS YOU" ostida "much gentler than you usually prefer" turdi — ziddiyat qoidaning o'zida edi, chunki eski sabab yo'nalishni o'lchardi. O'lchov: eski qoidada `d394a840` uchun 500 filmdan 495 tasi sabab tomonida edi → yangi qoidada uch akkauntda 44.8 / 50.6 / 66.2%. gate 2026-10-23 da yashil (run 100) va `441211d` jonli; kesh deploy'dan keyin qayta tekshirildi — 0 qator, o'chirishga narsa yo'q — pastga qara); 2026-10-15 (**bitta simmetrik trait qoidasi**, TZ 1.23: sabab 0.5 σ, farq 1.0 σ, sabablar ustun, ikkalasi bo'lmasa jim; API `reasons` → `named_traits` + `trait_side`; farq uchun alohida prompt. Sabab: "Outside your usual taste" ostidagi filmda "sizga mos" izohi. O'lchov va asos: `docs/phase-2-status.md`. **5-bosqich ham shu bilan yopildi** — 82 va 85 orasidagi 3 ball endi sabab emas. **Izohlar jonli xizmatda yaratilyapti** — 2026-10-13 dagi "yaratilmayapti" yozuvi tasdiqlanmagan taxmin edi (Render log'i o'qilmagan): keshda `gemini-3.5-flash-lite` 2026-10-15 03:58–03:59 (UTC) da yozgan 3 qator bor edi (Aliens `en`, Godzilla `en` va `uz`) — ya'ni ziddiyat haqidagi xabardagi Godzilla jumlasi ham haqiqiy generatsiya, zaxira shablon emas. 10–13 oktabr orasidagi bo'shliq nosozlik emas, urinish bo'lmagani. Kesh endi bo'sh: 10 qator foydalanuvchi qarori bilan o'chirildi (eski qoida va eski prompt bilan yozilgan edi), har biri keyingi so'rovda ~$0.00013 ga qayta yaratiladi. Keyingi: 3-bosqich (qidiruv)); 2026-10-13 (**tester fikri**: zaxira jumlasi matni tuzatildi (`c70f1fc`), hero teginishda to'xtaydi (`f22d548`); tavsiyalarning eski tomonga og'ishi o'lchandi — ANN neytral, match 34%, **MMR 40%** — qaror kutilmoqda (`docs/phase-2-status.md`); recency jarimasi `w = 0.02` qo'yildi (TZ 1.21); izoh indikatori tuzatildi — API sababni beradi (TZ 1.22). **Ochiq:** NSFW bandi. ~~izohlar 2026-10-10 dan keyin yaratilmayapti~~ — **yopildi 2026-10-15**, pastga qara); 2026-10-10 (**uyqu: Render Starter o'rniga cron-job.org ping**, foydalanuvchi qarori); 2026-10-10 (**FR-3 bajarildi**: foydalanuvchi jonli saytda onboarding'dan o'tdi, kutish sezilmadi — alohida vaqt o'lchovi qilinmaydi, foydalanuvchi qarori); 2026-10-09 (**logo, yuklanish holatlari va o'tish effektlari tugadi**, dialog portal tuzatishi; oxirgi commit `a6dffc6`, CI run 61 yashil); 2026-10-08 (**F3 qo'lda tekshiruvi**: onboarding 3:10, (a) xatosi tuzatildi, tarmoq kechikishi va Lighthouse deploy'dan keyin; **deploy — F4 dan oldin alohida qadam**, tayyorgarlik `docs/deploy.md`); 2026-10-06 (**dizayn v2 yopildi**: 0–5 bosqich bajarildi va tasdiqlandi; keyingi qadam — F3 qo'lda tekshiruvi); 2026-10-06 (4-bosqich: Movie DNA radial diagrammasi; hero: "For you" 6-filmdan, mobil boshqaruv rasm ustida; 5-bosqich: qidiruv kartalari Home bilan bir xil; 3-bosqich yakuni: hero kicker va jumla, balandlik pasaytirildi; "good" interfeysdan olindi, TZ 1.16; 4-bosqich faqat radial DNA, TZ 1.15); 2026-10-05 (dizayn 3-bosqich: Home hero, `backdrop_path` har filmda); 2026-10-05 (film sahifasi: daraja — panel sarlavhasi; "yaxshi" 15%, TZ 1.14); 2026-10-05 (FR-5: match darajasi, TZ 1.13; dizayn 2-bosqich tuzatishlari); 2026-10-04 (dizayn 1-bosqich); 2026-10-02 · F1 ma'lumot qismi yopildi (500 film) · Tillar: en standart, uz, ru (TZ 1.8) · **LLM provayderi tanlanmagan** (ADR 0006)

Bitta sahifada: qaysi faza tugagan, nima chala, keyingi qadam. Tafsilotlar faza
hisobotlarida: `docs/phase-1-status.md`, `docs/phase-2-status.md`, `docs/phase-3-status.md`, `docs/phase-4-status.md`. Fazalar ro'yxati:
`docs/prompts/README.md`. Xarajatlar: `docs/costs.md`.

## Fazalar

| Faza | Holat |
|---|---|
| F0 — Poydevor | **Tugagan** (`b2a4d35`, gate o'tgan) |
| F1 — Ma'lumot va Movie DNA | **Kod tugagan, ma'lumot chala.** 1-bosqich bajarildi (2026-10-01): 50 film trait oldi (sync, 0 yiqildi), qo'lda ko'rik **o'tdi** — 50 dan 3 tasi bahsli, chegara 5. 2-bosqich: traitlar 500 / 500 (13 film Google filtri bilan bloklanib almashtirildi); 2-bosqich ≈ $0.28 standart tarifda, bepul tarifda $0. Embedding 500 / 500 (ikki run, $0.0182 standart, bepul tarifda $0); missing count 0. Qo'shnilar ko'rigi **o'tdi** (2026-10-02). **Ma'lumot qismi yopildi.** Ma'lum muammo: Spirited Away qo'shnilari studiya bo'yicha to'planadi (F2 qo'lda tekshiruvida qaraladi) |
| F2 — Tavsiya dvigateli | **Tugagan** (2026-10-02). Qo'lda tekshiruv **o'tdi** (foydalanuvchi xulosasi): "For you" dagi 20 filmdan deyarli hammasini ko'rardi; qolgan bo'limlar "yomonmas". Qo'lda match hisobi va 5 izohni sabablar bilan solishtirish **bajarilmadi** — formula testda (`test_match_is_recomputable_from_stored_numbers`, har commit'da), izohning mazmuni test qilinmagan. Izoh narxi o'lchangan: $0.00013 bittasi. Tekshiruvda topilgan `POST /watchlist` 500 xatosi tuzatilgan (`01d08f7`); izohlar limiti interfeysda ko'rinmaydi (backlog, TZ 1.9); feed 45 bahoda ~15 s (F5 ishi) |
| F3 — Web ilova | **Kod tugagan, `main` da (`66bc7a0`), CI yashil. Qo'lda tekshiruv chala.** Foydalanuvchi so'rovi bilan F2 qo'lda tekshiruvidan oldin boshlangan (prompt sharti bajarilmagan). Onboarding 3:10 (2026-10-08, maqsad < 3 daqiqa): 58 s — baho saqlashni kutish (Singapurgacha tarmoq). **FR-3 bajarildi (2026-10-10):** jonli saytda (deploy'dan keyin) foydalanuvchi onboarding'dan o'tdi, sahifalar orasida kutish sezilmadi; alohida vaqt o'lchovi qilinmaydi (foydalanuvchi qarori). Tekshiruvda topilgan (a) xato — eskirgan kesh onboarding'ga qaytarardi — tuzatildi (`3d7a976`). **F3 band 5 (Lighthouse, film sahifasi, jonli sayt, foydalanuvchi 2026-11-17): mobil LCP median 4.6 s (14.5 / 4.2 / 4.6 s) — bajarilmadi; desktop 1.4 s; INP o'lchanmagan.** TZ 1.34: F9a shartiga ko'chdi; tuzatish `f3-perf` (merge `0201d02`). **Qayta o'lchov 2026-11-22:** mobil LCP median **3.5 s** (5.2 / 3.5 / 3.5 s) — bajarilmadi; INP median **96 ms** (5 o'lchov) — bajarildi. Tafsilot: `docs/phase-3-status.md` |
| Tillar (TZ 1.8, 2026-10-02) | **Kod tayyor.** Ingliz — standart til va kalitlar manbasi (`apps/web/src/i18n/en.ts`); o'zbek — ikkilamchi; rus — qo'shimcha, **ko'rilmagan qoralama**. Menyu: English, O'zbek, Русский; tanlov `localStorage` da saqlanadi, brauzer tili aniqlanmaydi. API: `lang` = `en` \| `uz` \| `ru`, standart `en`; izohlar rus tilida ham (har til alohida kesh). Film ma'lumoti ingliz tilida qoladi (backlog) |
| Dizayn v2 (`docs/ui.md`) | **Yopildi** (2026-10-06): 0–5 bosqich bajarildi va tasdiqlandi; oxirgi commit `e9a7f9f`, CI yashil |
| Logo, yuklanish, o'tishlar (`docs/ui.md`: Logo, Yuklanish holatlari, O'tish effektlari) | **Tugadi** (2026-10-09). Uch bosqich: logo, favicon, ikonkalar va manifest (`d84e09c`, run 58); belgi bilan yuklanish holatlari (`d692ec4`, run 59); qisqa o'tishlar (`f1125ad`, run 60); dialog `document.body` ga portal — Rate dialogi panellar ostida qolardi, oldindan bor nuqson (`a6dffc6`, run 61). Hammasi CI yashil. CLS 0, axe 0 (mock, haqiqiy Chrome); testlar 246. Sahifa o'tishi: `BrowserRouter` da `viewTransition` hech qachon ishlamagan — endi 120 ms opacity; to'liq o'tish backlog'da |
| Deploy (F4 dan oldin, alohida qadam) | **Ishlayapti** (2026-10-08). **2026-11-11: ikkala Supabase loyihasi faolsizlikdan to'xtagan edi** — jonli `/health` 200, `/health/db` 500; foydalanuvchi tikladi. Sabab: cron-job.org ping'i `/health` ga boradi, u bazaga tegmaydi; Frankfurt'ni CI ishlatmaydi (runner konteyneri), faqat mahalliy testlar. Yechim: ping manzili `https://movie-match-api-mgdn.onrender.com/health/db` (`SELECT 1`, 500 da cron-job.org xat yuboradi; Supabase buni yetarli deb hisoblashi kafolatlanmagan — ogohlantirish xati kelsa keyingi qadam), Frankfurt uchun ping yo'q, ataylab (`docs/deploy.md` 4–5-bo'lim). Avvalgi holat: web https://movie-match.pages.dev (Cloudflare Pages), API https://movie-match-api-mgdn.onrender.com (Render Free, Singapur). Tayyorgarlik (2026-10-08, foydalanuvchi qarori): fazalar tartibida deploy F5 ichida, F5 esa F4 gate'ini talab qiladi. Alohida qilinadi, chunki F3 ning ochiq o'lchovlari (FR-3 onboarding, feed tezligi, Lighthouse) faqat jonli URL'da o'lchanadi. API — Render Free, Singapur (`render.yaml`); web — Cloudflare Pages (keyin). F5 ning telemetriya, metrika, "wrong" tugmasi va testerlar qismi F5 da qoladi. Qadamlar: `docs/deploy.md` |
| F4 — AI assistant | **Kod tugagan, jonli, qo'lda tekshiruv bajarildi; FR-8 ning birinchi belgi mezoni (TZ 1.32: ≥ 30 xabar, ≥ 2 kun, median ≤ 3 s, p90 ≤ 15 s, xato 0) bajarilmagan — 33 xabarda median 3.62 s, 1 xato. TZ 1.33: shu ochiq yozuv bilan yopiladi, mezon F9a shartiga ko'chdi. Yopildi 2026-11-18 (TZ 1.34)**, ikkinchi ochiq yozuv bilan: F3 band 5 — film sahifasi mobil LCP 4.6 s, INP o'lchanmagan; u ham F9a shartiga ko'chdi. Hisobot: `docs/phase-4-status.md`. Jonli **`f56ffa5`** (merge `f4-fixes-4`, 2026-11-13: intro nuqtasi; avval `f4-fixes-3` → `f930295`: kirish gapi tool'ning `intro` argumentida, so'rov oldi vaqtlari log'da, yozayotganda ulanish ochiladi). Yakuniy o'lchov 2026-11-13 14:11 UTC: 10/10 `done`, median 2.95 s. Render kaliti Gemini bepul tarifida (15 RPM). Avval jonli `556e676` (merge `f4-fixes-2`, 2026-11-12 19:27 UTC; birinchi merge `b179b30`, 2026-11-11). Qo'lda tekshiruv 2026-11-11: 72 xabar, 3 test akkaunti, $0.1086; off-topic va 3 injection hammasi `refusal: off_topic`; 6 xato (5 ta 503, 1 blocked). Keyin ikki tuzatish to'plami: `f4-fixes` (`84ac291`: 503 da bir marta qayta urinish, `reset` hodisasi, bosqich vaqtlari log'da) va `f4-fixes-2` (`556e676`: xabarga 25 s / 45 s chegara va "band" matni, to'xtab qolgan oqim qayta uriniladi, kesilgan chaqiruv tokenlari taxminan yoziladi — TZ 1.28; faqat javob joylashtirgan kartochkalar; `search_movies` ga `genres` va tool'dan oldin kirish gapi — TZ 1.29; ADR 0009 qo'shimchalari). Deploy'dan keyingi o'lchov (2026-11-12 19:33–19:34 UTC, 10 xabar): 10/10 `done`, xato 0, birinchi belgi median **3.54 s**, janr so'rovlarida hamma kartochka so'ralgan janrda. Zaxira model (1e) qilinmadi (foydalanuvchi qarori). Migratsiya `0005` asosiy bazada (pastda). Prompt sharti "F3 gate yashil" to'liq emas: film sahifasining jonli Lighthouse o'lchovi (F3 band 5) F4 bilan parallel o'lchanadi, foydalanuvchi qarori 2026-11-11. Assistant `LLM_PROVIDER` orqali ishlaydi, Claude Sonnet 5 o'rniga Gemini 3.5 Flash-Lite (ADR 0009, foydalanuvchi qarori). Limit 30 / UTC kun (TZ o'zgarmagan). Yangi: `POST /assistant/chat` (SSE), `recommend.search`, migratsiya `0005` (`assistant_turns`, `assistant_usage`), web `/assistant`. Fiksturalar Gemini stream shaklida qo'lda yozilgan, haqiqiy chaqiruvdan yozib olinmagan |
| F5 — yopiq alfa | **Kod `main` da va jonli (merge `6d5a4cf`, 2026-11-22; CI run 133 yashil, https://github.com/smasheverybody99-hue/movie_match/actions/runs/45016443719; `/health` → `6d5a4cf`), migratsiya `0006` asosiy bazada (2026-11-22).** F4 yopilguncha merge qilinmadi (foydalanuvchi qarori 2026-11-17). 10 commit: migratsiya `0006`, `POST /events` va server hodisalari, `pipelines/metrics.py`, `POST /feedback`, web telemetriya, "Not right?", NSFW, izohlar limiti xabari, ma'lumot ogohlantirishi. Gate: CI run 128 yashil (`2c02942`, https://github.com/smasheverybody99-hue/movie_match/actions/runs/44152166586); run 127 (`44dce61`) bitta testda yiqilgan edi — `test_sensitive` fiksturasida oddiy film floor chegarasidan pastda qolgan, kod nuqsoni emas. Hisobot: `docs/phase-5-status.md`. Kutilmoqda (har biri foydalanuvchi ruxsati bilan): `sensitive --apply` (ro'yxatni foydalanuvchi ko'radi), 12 testerning `alpha_tester` belgisi |
| F6 — Android ilova | **Boshlandi 2026-11-23**, branch `f6-mobile`. **`main` ga merge `ae6f7ae`** (2026-11-23; `6d04b66` da android run 4 va gate 146 yashil), `/health` → `ae6f7ae`. Keyin: release imzosi `6d04b66` (kalit repo'dan tashqarida, secret'lar foydalanuvchida), **3-commit — kirish va ma'lumot ogohlantirishi `568fb47`** (59 test; android run 6 va gate 148 yashil; `f6-mobile` da, merge yo'q). **4-commit — onboarding `39678a8`** (2026-11-24): tanlash → baholash → tayyor, web tartibida; baholar navbati (web `ratingQueue.ts` porti), progress telefonda saqlanadi va qayta ishga tushirishda tiklanadi, `onboarding_step` hodisasi; `flutter analyze` 0, `flutter test` 90 (toza worktree'da ham). android run 7 yashil, 5.0 daqiqa (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45334884073), gate 150 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45334884272). **Artifact debug** (`movie-match-debug-39678a8…`): run ogohlantirishlari — "No signing secrets: building the debug APK" va "SUPABASE_URL / SUPABASE_ANON_KEY variables are not set". Ya'ni foydalanuvchi qo'shgan to'rt sozlamadan Actions'ga ikkala guruh ham yetmagan (Supabase Redirect URL CI'dan tekshirilmaydi); qayerga qo'shilgani tekshiriladi, release APK shundan keyin. **5-commit — feed `d37e822`** (2026-11-24): hero ("For you" ning 5 tasi, 7 s aylanish, barmoq ushlaydi, boshqarilsa to'xtaydi), qatorlar ("For you" 6-filmdan), bo'sh bo'lim chizilmaydi, faqat "strong" belgisi; Save (darhol, xatoda qaytadi), "Not right?" (pastki oyna, 4 sabab), `recommendation_shown` / `recommendation_clicked`; telefon farqlari: slaydlar suriladi, pull to refresh, kartada tezkor Rate/Save yo'q, bo'sh holatda "Search films" qidiruv commit'igacha yo'q, `/movie/:id` film sahifasigacha vaqtinchalik. `flutter analyze` 0, `flutter test` 132 (toza worktree'da ham). **android run 8 yashil, 5.7 daqiqa** (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45348308590): sozlamalar ogohlantirishi va "No signing secrets" yo'q, release qadami (imzo tekshiruvi bilan) o'tdi, artifact `movie-match-d37e8221ed3bb278894a1897a1fe9bc9dceff67e` (26.7 MB zip, 2026-12-08 gacha); annotatsiyalarda faqat GitHub'ning Node 20 / `setup-java@v4` eskirish ogohlantirishlari. gate 153 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45348308599). Run 7 (debug) sababi: `ANDROID_KEYSTORE_PASSWORD` o'shanda qo'shilmagan edi (foydalanuvchi, 2026-11-24). **6-commit — film sahifasi `a14241f`** (2026-11-24): backdrop, poster va sarlavha, Rate / Save; "why you" (band sarlavha, API tomoni bo'yicha jumla, 3 tagacha trait o'qda), overview va credits, yana 6 trait taqqoslash; izoh keshdan yoki bepul shablon, `no_generator` / `daily_cap` / `no_taste` (yoki ikki `failed`) dan keyin shu ishga tushirishda so'ralmaydi; baho optimistik, xatoda oldingisiga qaytadi; sezgir film avval ogohlantiradi; baholash shkalasi va backdrop umumiy widget'larga ko'chdi. Telefon farqlari: baholash pastki oynada, yuklanishda bosilgan kartaning backdrop'i. `flutter analyze` 0, `flutter test` 161 (toza worktree'da ham). android run 9 yashil, 6.5 daqiqa (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45352150566): release, artifact `movie-match-a14241fc6f7d01424bfed5baa42d46ab6a3e990d` (26.8 MB zip, 2026-12-08 gacha); gate 155 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45352150392). `main` ga merge foydalanuvchining telefondagi sinovidan keyin. **7-commit — qidiruv `0f48081`** (2026-11-24): mashhur filmlar, yozish to'xtaganda bitta so'rov (250 ms), oldingi natijalar yangisi kelguncha qoladi; yil (4 raqam), davomiylik va "kuchli" trait filtrlari, Clear filters; to'rt holat. **Pastki menyu** (web bottom-nav): Home va Search, har bo'limning o'z stack'i; film sahifasi menyuni yopadi; Assistant bo'limi foydalanuvchi qarorini kutadi (TZ 1.38). Feed bo'sh holatida "Search films". `flutter analyze` 0, `flutter test` 174 (toza worktree'da ham). android run 10 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45357980958): release, artifact `movie-match-0f4808107285cd691fb78db8ccd5cc8f43a025f5`; gate 157 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45357980920). **8-commit — watchlist `6c9ba39`** (2026-11-24): Watch next / Under 90 min / Watched chiplari, API band'i, Watched va Remove (darhol, rad etilsa "That change wasn't saved" bilan qaytadi), to'rt holat va bo'sh guruh. Watchlist holati bitta kutilayotgan o'zgarishlar qatlami (qo'shish, o'chirish, ko'rildi) — feed, film sahifasi va shu ekran uchun umumiy; pastki menyuga Watchlist. Poster: kichik posterda katta shriftda fallback matni toshib chiqmaydi. Telefon farqlari: qator o'ngga surilsa Watched, chapga — Remove (paritet jadvali), tugmalar TalkBack uchun qoladi; chiplar yon tomonga aylanmaydi, o'raladi (telefonda uchinchisi ko'rinmasdi). `flutter analyze` 0, `flutter test` 192 (toza worktree'da ham). android run 11 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45360030873): release, artifact `movie-match-6c9ba399318c9cd1aaaf20f35698b379de694dc9`; gate 159 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45360031280). **9-commit — Movie DNA `997f2b4`** (2026-11-24): jumla (API'niki yoki eng kuchli uchta trait), radial diagramma (har trait — doimiy burchakdagi nur, uzunlik qiymatga chiziqli, eng kuchli uchtasi to'liq oq, 50 va 100 halqalari, uchlardan o'tgan kontur; nurlar birinchi chizishda o'sadi, animatsiya o'chiq bo'lsa yo'q), baholangan filmlar, o'rtacha baho, asosiy janr, Numbers ostida aniq qiymatlar; 10 bahodan kam bo'lsa "yana N ta", yoqqan film bo'lmasa nima yetishmasligi; pastki menyuga Movie DNA (web tartibida Watchlist'dan oldin). Telefon farqlari: Share — Android share sheet (MainActivity.kt dagi kichik kanal, paket o'rnatilmadi), bo'lmasa matn nusxalanadi; diagrammada faqat eng kuchli uchta yorliq (web 640 px dan pastda shunday). `flutter analyze` 0, `flutter test` 211 (toza worktree'da ham). android run 12 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45364600804): release, artifact `movie-match-997f2b44a23aa8574e7e96370bdb4dded48e71d8`; gate 160 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45364600815). **Assistant ekrani foydalanuvchi qarorini kutadi** (alfada qanday bo'lishi; TZ 1.38 web launch'da yashiradi). **Profil `da618ce`** (2026-11-24; assistant qarorgacha rejadagi navbatdagi ekran): email, til (English, O'zbek, Русский — telefonda `mm.lang` kalitida, web bilan bir xil), Sign out (feed'dan profilga ko'chdi), Delete account tasdiq bilan (xatoda aytadi, chiqarmaydi), About — TMDB atributsiyasi; `/about` ochiq, Welcome'dan havola. Telefon farqlari: profil har bo'lim yuqori panelidagi odam ikonkasidan ochiladi; TMDB havolasi brauzerda Share bilan bir kanal orqali (`movie_match/android`: share, open) — URL paketi o'rnatilmadi. `flutter analyze` 0, `flutter test` 222 (toza worktree'da ham). android run 13 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45376927760): release, artifact `movie-match-da618ce0519e1116ccc4269e24bf091a9034b033`; gate 161 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45376927746). **Ikonka va launch ekrani `e2880f9`**: launcher ikonkasi — Movie Match belgisi (Android 8+ adaptiv vektor, 66 dp xavfsiz doira ichida, Android 13 monoxrom qatlami; 8 dan past — web `icon-512.png` dan kichraytirilgan PNG), launch ekrani yorug' rejimda ham qorong'i (oldin oq oyna chaqnardi), Android 12+ splash ham shu rang va belgi. android run 14 `e2880f9` da yiqildi: `values/colors.xml` izohida `--bg` — XML izohida `--` mumkin emas; tuzatildi `7302370`, android run 15 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45379647943), gate 163 yashil. **Assistant `42afdb9`** (foydalanuvchi qarori 2026-11-24: web'dagidek 5-tab, ko'rinishini server boshqaradi): SSE oqim — matn, kartochkalar qatori, 2–3 follow-up; "Looking through your films…"; refusal, reset; server 25/45 s chegarasida `timeout` → "busy", xato yoki uzilgan oqim → "failed", ikkalasida Try again ("blocked" da yo'q); 429 — tiklanish vaqti va maydon yopiladi; New conversation serverda ham yangi; kartochka filmni ochadi va `assistant` manbali click; bepul tarif eslatmasi; yozayotganda `/health` bilan ulanish isitiladi. Tab uchinchi o'rinda va faqat `/me` `assistant_enabled: true` bo'lsa; maydon yo'q yoki false — tab yo'q, server o'chirsa ilova Home'ga qaytadi. **API'da bu maydon hali yo'q** → APK'da tab ko'rinmaydi; taklif: `ASSISTANT_ENABLED` sozlamasi (default true), `/me` da `assistant_enabled`, migratsiyasiz — foydalanuvchi ruxsatini kutadi. `flutter analyze` 0, `flutter test` 243 (toza worktree'da ham). android run 16 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45382617744): release, artifact `movie-match-42afdb9370edd55b414b8275c4811fc2b706638d`; gate 164 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45382617726). O'rnatildi: JDK 17, Flutter 3.50.1, Android SDK (`docs/setup-android.md`, o'lchovlar bilan). Commit'lar: skelet `a339d45`, sozlash `7286b65` (material_ui, shriftlar, `API_URL`, `tokens_test`), CI `074cf82`, API klient va modellar `b843713` + `1977512` (39 test). android run 1 yashil, 5.0 daqiqa (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45206744999); gate 140 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45206745008). **android run 2 yiqildi** (`b843713`, `flutter analyze`): root `.gitignore` dagi `data/` qoidasi `apps/mobile/lib/data/` ni yashirgan, fayllar commit'ga kirmagan; tuzatildi `1977512`. **android run 3 yashil, 4.3 daqiqa**, APK artifact 79.1 MB zip, 2026-12-07 gacha (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45216461890); gate 143 yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45216461947). APK hozircha bo'sh ilova (ekranlar 3-commit'dan). Mahalliy build 15 daqiqada tugamadi — APK CI'dan. Testerlarga APK, Play'siz (TZ 1.37). **Telefonda Google bilan kirish ishladi** (foydalanuvchi, 2026-11-24): sabab — Supabase asosiy loyihada Redirect URL yo'q edi, qo'shildi; `docs/setup-android.md`, "Muammo bo'lsa: kirish" |
| F7 va keyingilari | Boshlanmagan |

## Oxirgi gate natijasi

| | |
|---|---|
| **Jonli o'lchov, ikkinchi kun (2026-11-17 04:17–04:24 UTC) — TZ 1.32 verdikti** | `/health` → `da726cb` (`f56ffa5` dan keyin faqat docs). 20 xabar (11-13 dagi 10 lik to'plam + 10 yangi, en/uz/ru), ochiq ulanish, har xabar javobdan ≥ 10 s keyin. **19 `done`, 1 `error`** ("Bugun kechqurun oilaviy multfilm": intro 4.34 s, `reset`, keyin `failed` 15.0 s da; sababi Render log'ida). Birinchi belgi: 4.11, 2.29, 1.89, 1.97, 12.69, 10.91, 4.20, 3.81, 4.67, 4.85, 9.24, 4.34, 11.35, 1.94, 9.33, 2.03, 2.34, 1.93, 7.51, 2.22 s → **median 4.15 s**. Javob boshlanishi 0.70–1.31 s (ikkitasi 2.67 va 3.29 s). **Ikki kun birga** (11-13 dagi 14:11 to'plami + starterlar, 13 xabar): 33 xabar, median **3.62 s**, p90 11.35 s, xato 1 → **mezon bajarilmadi**. Tafsilot: `docs/phase-4-status.md` |
| **Jonli o'lchov, `f56ffa5` (2026-11-13 14:11–14:17 UTC) — F4 yakuniy** | 10 xabar (19:33 dagi to'plam), ochiq ulanish, xabar boshlari ≥ 10 s, javobdan keyin ≥ 5 s (bepul tarif 15 RPM). **10/10 `done`, xato 0.** Birinchi belgi: 11.64, 2.17, 1.82, 2.15, 2.29, 13.67, 10.72, 5.08, 3.62, 1.86 s → **median 2.95 s** — 2 s mezoni bajarilmadi. Ikki sekin xabarda javob boshlanishi 8.11 va 3.97 s (qolganlari 0.39–0.85 s) — server bosqichlari o'qilmagan (Render log'i kerak). Keyin hisobot uchun 7 xabar: starterlar 1.78 / 1.72 / 3.19 s, off-topic va 3 injection → `refusal: off_topic`. Intro'lar hammasi nuqta bilan tugadi. Bugungi 21 javob: median 2.17 s, p90 10.7 s. Tafsilot va so'zma-so'z javoblar: `docs/phase-4-status.md` |
| **CI va deploy (`f4-fixes-4` → `main` `f56ffa5`)** | 2026-11-13: branch'da **gate run 120** yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/43428201282), coverage annotatsiyasi `assistant.py` 98%, `app/services` 98%; `main` da **gate run 121** yashil (https://github.com/smasheverybody99-hue/movie_match/actions/runs/43428706789). `/health` → `f56ffa542b4707e6ae6102a311af468264e08dcc` (12:55 UTC), `/health/db` 200. Mahalliy (DB testlarisiz): `ruff check` 0, `ruff format --check` 0 (129 fayl), `mypy app` 0 (49 fayl), pytest **384 o'tdi / 259 skip** |
| **Jonli o'lchov, `f930295` (2026-11-13 06:17–06:18 UTC) va Render log'i** | 10 xabar, ochiq ulanish, oraliqsiz (~40 s): 8 `done`, **2 ta `error: failed`** — sabab log'da: Gemini 429 `generate_content_free_tier_requests`, limit 15/daqiqa, "retry in 51.8s" (kalit bepul tarifda; kod mo'ljallanganidek qayta urinmadi). Birinchi belgi 8 ta javobda median 1.78 s. Server (8 ta `done`): `jwt` 0.00 (deploy'dan keyingi birinchisida 0.83), `user` 0.01, `claim` 0.015, `forget` 0.01, birinchi chaqiruv 1.38 s, `search` 0.05, birinchi belgi **1.40 s**; mijoz − server ~0.38 s (11-12 da 0.99 s). Narx: o'rtacha 4 847 / 159 token, $0.00185 xabar |
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

0. **Assistant flag'i — jonli (2026-11-24).** `api-assistant-flag` (`cb6c6a7`) `main` ga
   merge qilindi `f24db17` (foydalanuvchi tasdig'i; diff faqat 5 fayl). gate 168 yashil
   (https://github.com/smasheverybody99-hue/movie_match/actions/runs/45424341976); Render
   deploy: `/health` → `f24db17` (15:25 UTC); `GET /me` token'siz → 401; jonli
   `/openapi.json` da `MeOut.assistant_enabled`, default `true` (Render'da
   `ASSISTANT_ENABLED` qo'shilmagan — foydalanuvchi qarori). Branch lokal va remote'da
   o'chirildi. **Qoldi (foydalanuvchi):** telefonda ilovani qayta ochish → pastki menyuda
   uchinchi **Assistant** tab'i (token bilan `/me` ni agent tekshira olmaydi). F9a da
   o'chirish: `docs/prompts/phase-09a-web-launch.md`, "The switch is `ASSISTANT_ENABLED`".

**Tartib (TZ 1.30, 1.31), sanalar TZ 1.35 (2026-11-22: testerlar 29-noyabrgacha, qolgani +6 kun,
oraliqlar o'zgarmagan; avval TZ 1.32 da +4 kun).** Doira o'zgarmadi. Tartib va sanalar: `docs/TZ.md` §2 "Tartib va maqsad
sanalar", `docs/prompts/README.md`, `docs/roadmap.html`. Qisqasi: F4 yopish 19-noyabr → F5
alfa kodi 22-noyabr (bajarildi) → testerlar 29-noyabrgacha (12 Android + Gmail, maqsad 15) →
F6 Android (alfa paytida), Play yopiq testi 8-dekabr (o'sha testerlar) → alfa qarori 13-dekabr → F9a web launch 15-dekabr → F9b Google Play'ga ariza
22-dekabr (do'konda **29-dekabrdan oldin emas**; F7 va F8 ni kutmaydi) → F8, keyin F7 —
do'kondan keyin yangilanish. iOS hozir rejalanmaydi (alohida qaror, yanvar). Launch uchun
15% ham, 70% ham shart: 15% yiqilsa dvigatel, 70% yiqilsa onboarding qayta ishlanadi. 15%
faqat 7 kunlik oynasi yopilgan tavsiyalar bo'yicha (13-dekabrdagi qarorda 6-dekabrgacha
ko'rsatilganlar). F5 darvozasi: 12 tester, 2 hafta, 5 suhbat.

**TZ 1.37 (foydalanuvchi, 2026-11-23): karta bor, hozir $25 yo'q; testerlar 4 ta.** (1) Alfa
2026-11-29 da kim bo'lsa, o'shalar bilan boshlanadi, taklif davom etadi; 2026-12-06 gacha 12
tester bo'lmasa, 2026-12-13 dagi qaror o'sha son bilan, **"zaif signal"** deb belgilanadi;
15% va 70% o'zgarmaydi. (2) Google Play (F9b) $25 topilguncha to'xtaydi; yopiq test — pul va
12 tester bo'lganda. (3) F6 davom etadi; testerlar Android ilovani APK fayl sifatida oladi
(`docs/testers-android.md`). (4) Web launch'ning pulsiz yo'li — pastda, "Web launch pulsiz",
tanlov foydalanuvchida. Yuqoridagi 8-dekabr, 22-dekabr va 29-dekabr sanalari shu bilan
bekor; yangi jadval:

| Sana | Nima | Holat |
|---|---|---|
| 2026-11-29 | Alfa boshlanadi, kim bo'lsa o'shalar bilan (2026-11-23 da 4), web'da; taklif davom etadi | TZ 1.37 |
| ~2026-11-30 | Testerlarga birinchi foydali APK (kirish, onboarding, feed) | F6 rejasi, taxmin |
| 2026-12-01 | Film sahifasi LCP qayta ko'riladi, barcha variantlar bilan | foydalanuvchi qarori |
| 2026-12-05 | F6: barcha ekranlar APK'da | F6 rejasi, taxmin |
| 2026-12-06 | Testerlar soni: < 12 bo'lsa — "zaif signal"; 15% uchun shu kungacha ko'rsatilgan tavsiyalar | TZ 1.31, 1.37 |
| 2026-12-08 dan | F6: offline (`isar_community`) va haftalik push, yangilanish sifatida | foydalanuvchi qarori |
| 2026-12-13 | Alfa qarori (15% va 70%) | TZ 1.35 |
| 2026-12-15 | F9a web launch, **AI'siz** (assistant yashirin, izoh keshdan yoki shablondan) | TZ 1.38 |
| — | Play yopiq testi: $25 va 12 tester bo'lganda → 14 kun → F9b ariza → Google ko'rigi (odatda ≤ 7 kun) → do'kon | TZ 1.37, sana yo'q |
| F9a dan keyin | F8, keyin F7 | TZ 1.38 |
| 2027-01 | iOS qarori | TZ 1.31 |

1. ~~**F4 yopish (19-noyabr)**~~ — **yopildi 2026-11-18 (TZ 1.34)**, ikki ochiq yozuv bilan
   (ikkalasi F9a sharti): FR-8 birinchi belgi va F3 band 5. Lighthouse (foydalanuvchi,
   2026-11-17, jonli sayt, The Dark Knight Rises): mobil LCP 14.5 / 4.2 / 4.6 s, median
   **4.6 s** (< 2.5 s kerak) — bajarilmadi; desktop 1.4 s; INP o'lchanmagan. Mobil LCP va
   INP F9a da qayta o'lchanadi: jonli saytda, mobil 3 o'lchov mediani, LCP < 2.5 s, INP
   < 200 ms; o'tmasa web launch yo'q. Tuzatish `f3-perf` → `main` (`0201d02`). **2026-11-22
   qayta o'lchov:** LCP median 3.5 s (bajarilmadi), INP median 96 ms (bajarildi); qolgan
   dastak — telefonda rasm hajmi. **Qaror (foydalanuvchi, 2026-11-23): hozircha A (w780),
   B yo'q; LCP 2026-12-01 da qayta ko'riladi** — o'shanda agent barcha variantlarni beradi:
   rasm hajmi, hero balandligi va joylashuvi ham. Avvalgi yozuv — hisobot:
   `docs/phase-4-status.md`. FR-8 mezoni (TZ 1.32): ≥ 30 xabar, ≥ 2 kun, median ≤ 3 s,
   p90 ≤ 15 s, xato 0. 33 xabarda (2026-11-13 va 11-17) median **3.62 s**, p90 11.35 s,
   xato 1 — **bajarilmadi**. **TZ 1.33 (foydalanuvchi, 2026-11-17):** mezon boshqa
   yumshatilmaydi; F4 "FR-8 birinchi belgi mezoni bajarilmagan (33 xabar, median 3.62 s,
   1 xato)" ochiq yozuvi bilan yopiladi; mezon F9a shartiga ko'chdi (pastda, Gemini tarifi
   6-qadam). Render log'i (04:17–04:24 UTC) o'qildi: xato — Gemini'ning ketma-ket ikki 503
   javobi ("high demand"), kod mo'ljallanganidek bitta qayta urinishdan keyin to'xtadi;
   sekin oltita xabarda vaqt Gemini'ning birinchi chaqiruvida (6.6–11.6 s, tez yarmida
   1.0–1.5 s), bizning bosqichlar 0.06 s. Kod nuqsoni emas, kod o'zgarmadi.
2. ~~**Gemini tarifi**~~ — **qaror (2026-11-17): alfa bepul tarifda**, istisno ADR 0004 da;
   ogohlantirish ekrani F5 kodida. Web launch'dan (15-dekabr) oldin pullik tarif shart.
3. **F5 alfa kodi (22-noyabr):** `docs/prompts/phase-05-alpha.md`. Testerlardan oldin
   backlog'dan faqat NSFW va izohlar limiti xabari (TZ 1.31). **Qaror (foydalanuvchi,
   2026-11-17): F5 kodi hozir boshlanadi, Lighthouse kutilmaydi** — ikkalasi bir-biriga
   bog'liq emas. Ish `f5-alpha` branch'ida; **F4 yopilmaguncha `main` ga merge qilinmaydi**. **2026-11-22: F4 yopilgan, foydalanuvchi ruxsati bilan migratsiya `0006` asosiy bazaga qo'llandi (0005 → 0006, 20 → 22 jadval, qatorlar o'zgarmagan) va `f5-alpha` `main` ga merge qilindi.**
   Migratsiya `0006` ni asosiy bazaga qo'llash va merge — har biri uchun alohida ruxsat.
   Pullik so'rov yo'q. F5 savollari bo'yicha yettala tavsiya qabul qilindi (2026-11-17):
   NSFW hamma ro'yxatdan yashiriladi, to'g'ridan-to'g'ri havolada ogohlantirish bilan;
   belgi — `PROHIBITED_CONTENT` + qo'lda ro'yxat (TMDB reytingi alfadan keyin);
   ogohlantirish kirishdan keyin bir marta, rozilik serverda, assistantda eslatma; rad
   etsa — chiqib ketadi; metrika faqat `users.alpha_tester` belgili 12 kishi bo'yicha;
   "noto'g'ri" — Home va assistant kartochkalarida, sababi chiplar bilan, film faqat
   joriy ko'rinishdan olinadi; "ko'rildi" = "ko'rdim" belgisi va baho, alohida; "ko'rsatildi"
   = kartochka 1 s davomida yarmidan ko'pi ko'rinsa, juftlik bir marta; D1/D7 istalgan
   hodisa bo'yicha; izohlar limiti matni uch tilda; `0006` asosiy bazaga `alembic --sql`
   bilan. **Kod yozildi (2026-11-17), `f5-alpha`, CI: run 128 yashil, https://github.com/smasheverybody99-hue/movie_match/actions/runs/44152166586** — `docs/phase-5-status.md`.
   Deploy tartibi: (1) `0006` asosiy bazaga (faqat qo'shadi, jonli kod unga ta'sirlanmaydi)
   → (2) F4 yopilgach merge → (3) `python -m app.pipelines.sensitive` ro'yxatini
   foydalanuvchi ko'radi, keyin `--apply --skip ...` (Google rad etganlar orasida Oldboy,
   Young Hearts kabi ochiq bo'lmagan filmlar bor) — **bajarildi 2026-11-23**:
   `--skip 255709,1232449` (Hope, Young Hearts), 14 film belgilandi (0 → 14); Oldboy, My
   Fault va Drawn Together ham belgilandi: testerlar orasida 18 dan kichiklar bo'lishi mumkin → (4) testerlar kirgach (kim bo'lsa, TZ 1.36/1.37) `alpha_tester`
   belgisi. Har bir bosqich — foydalanuvchi ruxsati bilan.
4. **F6 Android — boshlandi 2026-11-23**, `f6-mobile`. O'rnatish foydalanuvchi ruxsati bilan
   bajarildi (`docs/setup-android.md`: hajmlar, "Qaytarish" ro'yxati). Mahalliy debug build
   15 daqiqada tugamadi (5.8 GB RAM, swap) — APK CI'da (`.github/workflows/android.yml`).
   Reja tasdiqlandi (foydalanuvchi, 2026-11-23): ~14 commit, ekranlar web tartibida (kirish,
   onboarding, feed, film, qidiruv, watchlist, DNA, assistant, profil), keyin release va CI;
   offline va push 2026-12-08 dan keyin; Isar o'rniga `isar_community`; "film chiqdi" push'i
   backlog'da; Supabase redirect URL 3-commit'da foydalanuvchiga aytiladi. Bajarildi: 1–3
   commit va CI. Google Play akkaunti F9b ga ko'chdi (TZ 1.37). **Foydalanuvchi qadamlari
   (2026-11-23) — bajarildi:** Supabase Redirect URLs'ga `com.moviematch.moviematch://login-callback`
   (**asosiy** loyihada; 2026-11-24 da qo'shildi — undan oldin brauzer kirishdan keyin web
   saytga ketardi; telefonda Google bilan kirish ishladi); GitHub Actions variables
   `SUPABASE_URL`, `SUPABASE_ANON_KEY` va secrets `ANDROID_KEYSTORE_BASE64`,
   `ANDROID_KEYSTORE_PASSWORD` (birinchi release APK — android run 8). **Telefon sinovi
   o'tdi** (2026-11-24, Galaxy S9; `docs/phase-6-status.md`), `f6-mobile` merge'ga ruxsat.
   **F6 gate'ida yopildi:** "kamida bitta eski Android" — Galaxy S9 (SM-G960F), Android 10
   (API 29). **Ochiq:** 4 xil telefon (hozir bittasi), sekin
   telefonda sovuq start < 2 s (o'lchanmagan), tester APK'ni `docs/testers-android.md` dan
   o'zi o'rnatishi, internet qaytgach ~7 s (ehtimoliy sabab — tizimning TCP ulanish qayta
   urinishlari 1 + 2 + 4 s, 15 s connectTimeout ichida; telefon log'i bilan tasdiqlanmagan;
   tuzatish `32fd246` `main` da — merge `fa16b7a`, android run 19 yashil; telefonda qayta
   sinov foydalanuvchida), offline (Isar) va push (FCM) +
   `offline_test.dart` — 2026-12-08 dan keyin.

### Alfa tayyorgarligi (2026-11-29)

Ro'yxat (2026-11-24); bajarilgani — faqat OAuth holati tekshiruvi (2026-11-27). Testerlar
hozir **5+** (foydalanuvchi, 2026-11-24; maqsad 12–15).

**Google OAuth (tekshirildi 2026-11-27, foydalanuvchi).** Google Cloud loyiha "Default Gemini
Project" (`gen-lang-client-0014845015`), Google Auth Platform → Audience: Publishing status =
**Testing**, test users **4 ta**, chegara 100. **Qaror (foydalanuvchi): alfa Testing'da qoladi**;
har bir testerning Gmail'i Test users'ga qo'shiladi — **foydalanuvchining qadami**, 2026-11-29
gacha va har yangi tester kelganda. "Publish app" hozir bosilmaydi; "In production" ga o'tish —
F9a sharti (`docs/prompts/phase-09a-web-launch.md`, "Google sign-in in production").
Brend tekshiruvi — **istalgan, majburiy emas, qaror qilinmagan**: usiz ham "In production"
mumkin (consent screen'da faqat domen ko'rinadi); qaror — foydalanuvchi, **2026-12-08 gacha**
(yurist va domen holatiga qarab).

**Scope'lar (tekshirildi 2026-11-27, faqat o'qish).** Web (`apps/web/src/lib/supabase.ts`) ham,
Android (`apps/mobile/lib/auth/auth_client.dart`) ham `signInWithOAuth` ni `scopes` siz chaqiradi;
Supabase Auth'ning Google standarti — `email` va `profile` (supabase/auth,
`internal/api/provider/google.go`; Supabase hujjati: userinfo.email va userinfo.profile "added by
default", `openid` faqat qo'lda). Ya'ni faqat ism, email, profil. Google
(https://support.google.com/cloud/answer/15549945): bunday so'rovda "your users do not need to be
in the trusted user list, they will not see a warning message, and their authorizations will not
expire after 7 days". **Demak Testing'da ham ro'yxatdan tashqaridagilar kira oladi**, Google
yozishicha **ogohlantirishsiz** (consent screen'da ilova nomi o'rniga `<ref>.supabase.co`).
Shunga qaramay **Test users'ga qo'shish davom etadi** (foydalanuvchi).

**`alpha_tester` belgisi.** Faqat `users.alpha_tester = true` foydalanuvchilar metrikaga
kiradi (TZ 1.36); voqealar hamma uchun yoziladi, belgi faqat kim sanalishini hal qiladi.
Tartib: tester bir marta kiradi (birinchi `/me` da `users` qatori paydo bo'ladi) →
foydalanuvchi Gmail manzillarini beradi → agent Supabase `auth.users` dan id'larni topadi
(o'qish) → ro'yxatni ko'rsatadi → **foydalanuvchi ruxsati bilan, har safar** asosiy bazada
bitta `UPDATE users SET alpha_tester = true WHERE id IN (...)`, bitta tranzaksiya, o'zgargan
qatorlar soni commit'dan oldin tekshiriladi. Kechroq qo'shilgan testerga ham keyin qo'yish
mumkin; 15% uchun 2026-12-06 gacha qo'yilgani yaxshi.

**Testerlarga (foydalanuvchi yuboradi, masalan Telegram):** android run 19 APK
(`app-release.apk`, masalan `movie-match-2026-11-29.apk` deb nomlab); `docs/testers-android.md`
(o'rnatish yo'riqnomasi); telefonsizlar uchun web: https://movie-match.pages.dev;
ma'lumot ogohlantirishi bir qatorda (ilova va web birinchi kirishda o'zi ko'rsatadi:
assistant va izohlar Gemini'ning bepul tarifida, shaxsiy narsa yozmang); assistant kuniga
30 xabar, "band" deyishi mumkin (bepul tarifda butun servisga ~7 xabar/daqiqa).

**Metrikalar** — `services/api/app/pipelines/metrics.py`, faqat o'qish, asosiy baza,
faqat `alpha_tester`: **15%** — testerga ko'rsatilgan tavsiya (birinchi
`recommendation_shown`) 7 kun ichida watched yoki baholangan, faqat 7 kuni yopilganlar;
**70%** — `onboarding_done` / hamma sanalgan testerlar; ikkalasi 95% Wilson oralig'i bilan.
**Metrika tekshiruvlari (o'qish) foydalanuvchidan so'ramasdan bajariladi, natija aytiladi**
(foydalanuvchi, 2026-11-24); bazaga yozish (`alpha_tester`) — har safar ruxsat bilan.

| Sana | Nima | Kim |
|---|---|---|
| 2026-11-25 | Samolyot rejimi qayta sinovi, android run 19 APK | foydalanuvchi |
| 2026-11-27 | ~~Google OAuth consent screen holati~~ — **tekshirildi**: Testing, 4 / 100; qaror — Testing'da qoladi | foydalanuvchi |
| 2026-11-29 gacha, keyin har yangi testerda | Testerning Gmail'i → Google Auth Platform → Audience → Test users | foydalanuvchi |
| 2026-11-28 | Testerlar ro'yxati (ism + Gmail; hozir 5+, maqsad 12–15); taklif davom etadi | foydalanuvchi |
| 2026-11-29 | APK, yo'riqnoma, web havola, ogohlantirish qatori yuboriladi; testerlar kiradi | foydalanuvchi |
| 2026-11-29 – 12-06 | Gmail → id'lar → ruxsat → `alpha_tester` UPDATE | foydalanuvchi + agent |
| 2026-11-30 | Birinchi metrika tekshiruvi: `python -m app.pipelines.metrics --all-users --from 2026-11-29 --to 2026-11-30` — voqealar kelyaptimi (web va telefon: `onboarding_step`, `recommendation_shown`) | agent (o'qish, so'ramasdan) |
| 2026-12-06 | Testerlar soni (< 12 → "zaif signal"), oraliq metrika | agent + foydalanuvchi |
| 2026-12-06 – 12-13 | 5 ta 20 daqiqalik suhbat, yozuvlar `docs/research/alpha-interviews.md` | foydalanuvchi |
| 2026-12-13 | Alfa qarori: `--from 2026-11-29 --to 2026-12-06 --as-of 2026-12-13T00:00Z` (15% va 70%) | foydalanuvchi |

### Pul talab qiladigan qarorlar (TZ 1.30, 1.31; sanalar TZ 1.35)

Narx va manbalar: `docs/costs.md`. Hech biri agent tomonidan ochilmaydi (CLAUDE.md).

| Nima | Qancha | Qaysi sanadan oldin | Nega o'sha sana |
|---|---|---|---|
| Gemini pullik tarifi (billing, Tier 1) | Hisob ochishda Google Cloud **$50 karta hold** (foydalanuvchi ma'lumoti, 2026-09-30). Ishlatish: 12 tester × 20 xabar ≈ $0.47/oy, 20 suhbat ≈ $1.27/oy; eng yomoni (har kuni 30 xabar) ≈ $21/oy + izohlar ≤ $1/oy | Web launch'dan oldin emas (TZ 1.38: launch AI'siz). Assistant qaytishidan oldin; FR-8 qayta o'lchovi ikki kun talab qiladi | Alfa bepul tarifda (foydalanuvchi qarori 2026-11-17, ADR 0004 istisnosi): 12 tester, rozilik bilan. Ochiq launch'dan oldin pullik tarif, aks holda launch yo'q. Pullik tarifda FR-8 birinchi belgi mezoni ham o'tishi shart (TZ 1.33). Bepul tarifda 15 RPM butun servisga (~7 xabar/daqiqa) |
| Google Play developer akkaunti | $25 bir marta | **To'xtatilgan (TZ 1.37): hozir pul yo'q.** Yopiq test — pul va 12 tester bo'lganda | Yopiq test + 14 kun = ariza; tasdiq muddati sahifada yo'q |
| Apple Developer Program, iOS bulutli build | 99 USD/yil; Codemagic 500 daqiqa/oy bepul (M2), keyin $0.095/daqiqa | — | iOS hozir rejalanmaydi (TZ 1.31), qaror yanvarda |
| Yurist | Narx noma'lum (mintaqaga bog'liq) | Foydalanish shartlari va maxfiylik siyosati — **2026-12-15** dan oldin (web launch); Character Match — flag yoqilishidan oldin | `docs/legal.md` §2–3. Play yopiq testi uchun maxfiylik siyosati kerakmi — tekshirilmagan |
| Render Starter | $7/oy | **2026-12-15** dan oldin qaror (web launch) | Free: 0.1 CPU, feed ~3.1 s, 750 soatdan ~744 ishlatiladi |

Boshqa, shu jadvaldan tashqari: F7 personaj traitlari (LLM run, 2–3 ming personaj) —
alohida smeta va tasdiq bilan.

### Web launch pulsiz — **qaror: A, AI'siz (foydalanuvchi, 2026-11-23, TZ 1.38)**

Kodi F9a vaqtida yoziladi, hozir emas. Pul topilganda: pullik tarif → FR-8 o'lchovi
(TZ 1.33, pullik, ruxsat bilan) → assistant qaytadi. Variantlar (TZ 1.37), yozuv uchun:

F9a sharti — Gemini pullik tarifi ($50 karta hold) va unda FR-8 mezoni (TZ 1.33). Pul
bo'lmasa:

- **A. AI'siz launch.** Assistant yashiriladi; yangi izoh yozilmaydi — keshdagi izoh bo'lsa
  ko'rinadi, bo'lmasa `named_traits` dan shablon jumla (DNA'dagi kabi). Tavsiya, match, DNA,
  qidiruv, watchlist LLM'siz ishlaydi (trait'lar hisoblangan). Gemini xarajati $0, Google'ga
  foydalanuvchi matni ketmaydi. Kerak: TZ o'zgarishi (FR-8 web launch shartidan chiqadi,
  assistant keyin yangilanish bo'ladi) va kichik kod (flag + shablon izoh). Kamchiligi:
  launch'da "AI" qismi yo'q.
- **B. Bepul tarifda, AI bilan.** Alfadagidek ogohlantirish (Google kiritilgan matnni
  ishlatishi mumkin); ADR 0004 istisnosi launch'ga cho'ziladi. Butun loyihaga 15 so'rov/daqiqa
  — foydalanuvchi ko'paysa "band" xabari tez-tez. FR-8 mezoni bepul tarifda bajarilmagan
  (33 xabar, median 3.62 s), TZ 1.33 esa "mezon yumshatilmaydi" deydi — bu ziddiyatni
  foydalanuvchi hal qiladi. Maxfiylik siyosati bepul tarif shartlarini yozishi kerak.
- **C. Launch pul bo'lguncha suriladi, alfa kengayadi.** Web taklif bo'yicha qoladi (bepul
  tarif + ogohlantirish, hozirgidek), testerlar ko'payadi. 15-dekabr pul kelgan kunga
  bog'lanadi.

Uchala variantda ham boshqa pul masalalari qoladi: Render Starter ($7/oy, qaror 15-dekabrdan
oldin) va yurist (narx noma'lum).

### Gemini tarifi — **qaror: alfa bepul tarifda (foydalanuvchi, 2026-11-17)**

Ikkinchi yo'l tanlandi. Istisno ADR 0004 da yozildi ("Exception, 2026-11-17"): faqat 12
tester, ogohlantirishni o'qib rozilik bilan; alfa 2026-11-29 — 2026-12-13; web launch'dan
(2026-12-15) oldin pullik tarifga o'tiladi, aks holda launch bo'lmaydi. Ogohlantirish
ekrani — F5 kodi. Pastdagi ikki yo'l tarix va launch oldidagi qadamlar uchun qoldi.

**(1) Pullik tarifga o'tish** — foydalanuvchi qadamlari:
1. AI Studio → Projects: Render'dagi kalit qaysi loyihada ekanini ko'rish. Limit loyiha
   bo'yicha, kalit almashmaydi, Render'da hech narsa o'zgarmaydi.
2. O'sha loyihada billing'ni yoqish ("Set up billing" → Cloud Billing hisobi, karta; ilgari
   aytilgan $50 hold). Free → Tier 1 odatda darhol (rate-limits sahifasi, 2026-11-13).
3. Projects sahifasida tier "Tier 1" ekanini tekshirish. Tier 1: billing tier cap $250,
   10 daqiqalik oynada $10 xarajat chegarasi.
4. Cloud Billing → Budgets & alerts: oylik ogohlantirish (masalan $5). U to'xtatmaydi,
   faqat xat yuboradi.
5. Agent keyin: Render log'idagi keyingi 429 da `free_tier` yo'qligini va cost qatorlarini
   tekshiradi; `docs/costs.md` dagi "bepul tarifda" yozuvlarini yangilaydi. Eslatma: billing
   loyihaning hamma chaqiruviga tegadi — izohlar (~$0.00013 dona) va trait/embedding run'lar
   ham pullik bo'ladi.
6. **FR-8 qayta o'lchovi (TZ 1.33, F9a sharti):** pullik tarifda, mijoz tomonida, ulangan
   sahifada, ≥ 30 xabar, ≥ 2 xil kun: median ≤ 3 s, p90 ≤ 15 s, xato 0. Pullik run, agent
   avval so'raydi (~30 × $0.00185 ≈ $0.06). O'tmasa web launch bo'lmaydi; mezon boshqa
   yumshatilmaydi.

**(2) Bepul tarifda qolish** — testerlarga ko'rsatiladigan matn (assistant ekranida birinchi
xabardan oldin va taklif xatida; interfeysga qo'yish — F5 kodi, foydalanuvchi qarori bilan):

- uz: "Sinov davrida assistant va film izohlari Google Gemini'ning bepul tarifida ishlaydi.
  Assistantga yozgan xabarlaringiz va baholaringizdan olingan ta'm ma'lumoti Google'ga
  yuboriladi; Google ularni o'z mahsulotlarini yaxshilash uchun ishlatishi va xodimlari
  o'qishi mumkin. Shaxsiy yoki maxfiy ma'lumot yozmang. Assistant hamma uchun daqiqasiga
  taxminan 7 ta xabarga javob beradi — band bo'lsa, bir daqiqadan keyin qayta urinib ko'ring."
- en: "During the test, the assistant and the film explanations run on Google Gemini's free
  tier. What you write to the assistant, and taste data drawn from your ratings, is sent to
  Google, which may use it to improve its products and may have people read it. Don't write
  anything personal or confidential. The assistant answers about 7 messages a minute for
  everyone together — if it's busy, try again in a minute."
- ru: "Во время теста ассистент и пояснения к фильмам работают на бесплатном тарифе Google
  Gemini. То, что вы пишете ассистенту, и данные о вкусе из ваших оценок отправляются в
  Google; Google может использовать их для улучшения своих продуктов, и их могут читать
  сотрудники. Не пишите ничего личного или конфиденциального. Ассистент отвечает примерно на
  7 сообщений в минуту на всех — если он занят, попробуйте через минуту."

ADR 0004 ga istisno (qo'shimcha sifatida, foydalanuvchi tanlasa):

> **Istisno, yopiq alfa (2026-11-29 — 2026-12-13; ADR 0004 ga yozildi 2026-11-17).** Assistant va izohlar bepul tarif
> kalitida ishlaydi. Shartlar: (1) faqat taklif qilingan 12 tester, har biri yuqoridagi
> ogohlantirishni o'qib rozilik bergan; (2) ochiq launch'dan (F9a, 2026-12-15) oldin pullik
> tarifga o'tiladi, aks holda launch bo'lmaydi; (3) EEA, Shveytsariya va Buyuk Britaniyada
> Google pullik shartlarni har qanday tarifda qo'llaydi (ADR 0004 manbasi); (4) 15 RPM alfa
> hajmiga yetadi deb qabul qilinadi. Uzoq kutishli 429 hozir umumiy "javob bera olmadi"
> matni bilan tugaydi; uni "band" matniga o'tkazish — alohida kichik tuzatish.

### Web launch'dan oldin (2026-12-15): yurist uchun ochiq masalalar

Manba: `docs/legal-drafts/README.md`, "Gaps the lawyer and the user must see" (2026-11-23).
Hech biri tuzatilmagan. Tartib — foydalanuvchi (2026-11-23): lokalizatsiya birinchi.

1. **Ma'lumotlarni lokalizatsiya qilish (O'zbekiston).** "Shaxsga doir ma'lumotlar
   to'g'risida"gi qonun (O'RQ-547, 2021 yildagi o'zgartirishlar bilan) O'zbekiston
   fuqarolarining shaxsiy ma'lumotlarini O'zbekistondagi serverlarda qayta ishlash va
   saqlashni talab qiladi, deb tushuniladi. Baza (Supabase) va API (Render) Singapurda.
   **Yurist buni birinchi tekshiradi:** u matnni emas, bazaning joyini o'zgartirishi mumkin.
2. **Kirish yozuvi akkaunt o'chirilgach qoladi.** `DELETE /me` ilova qatorlarini o'chiradi,
   Supabase Auth'dagi identifikator (email bilan) qoladi (`services/users.py`). Siyosat
   to'liq o'chirishni va'da qiladi: launch'dan oldin yo kod Auth foydalanuvchisini ham
   o'chiradi, yo siyosat boshqacha yozadi.
3. **Ma'lumotni eksport qilish yo'q.** `docs/legal.md` §3: eksport "haqiqatan ishlashi
   kerak". Qoralamalar funksiya bo'lguncha email orqali so'rovda qo'lda bajarishni va'da
   qiladi.
4. **Minimal yosh** — bo'sh qoldirilgan: 13, 16 yoki 18, yurist qo'llaydigan qonunga qarab.
5. **Alfaning bepul tarif istisnosi** (ADR 0004): alfa paytida Google assistantga
   yuborilganni ishlatishi mumkin. Launch siyosati pullik tarifni nazarda tutadi; alfa
   xatboshisi belgilangan va launch'da olib tashlanadi.
6. **Log'lardagi IP manzillar.** Render, Cloudflare va Supabase so'rov log'larini IP bilan
   saqlaydi; saqlash muddati har provayderniki, bo'sh qoldirilgan.
7. **TMDB atributsiyasi** About ekranida bo'lishi kerak (`docs/legal.md` §1); shartlarda bor.
8. **Ziddiyat:** `CLAUDE.md` TMDB tijorat litsenziyasini "public launch'dan oldin" deydi,
   `docs/legal.md` va ADR 0002 — "mahsulot pul topishidan oldin" (bepul launch notijorat).
   Yurist yoki foydalanuvchi hal qiladi; TMDB xati qoralamasi
   (`docs/legal-drafts/tmdb-licence-request.en.md`, yuborilmagan) TMDB'dan to'g'ridan-to'g'ri
   so'raydi.

### Backlog'dagi "F5 dan oldin" bandlari — qaror (foydalanuvchi, TZ 1.31)

- **Testerlardan oldin:** NSFW / ekstremal filmlar; izohlar limiti tugaganini aytish.
- **Alfadan keyin** (alfa paytida dvigatel va onboarding o'zgarmaydi): recency sifat
  chegarasi (`tmdb_vote_count`); onboarding chiplari filmga xos.
- **F5 dan keyin:** Movie DNA AI xulosasi; DNA ulashish server rasmi; izoh keshi kalitiga
  sabablar; film ma'lumotini tarjima.

### F6 uchun o'rnatish — hech narsa o'rnatilmaydi (foydalanuvchi, 2026-11-13)

F5 kodi tugagach agent **Android Studio'siz** eng yengil yo'lni taklif qiladi: noutbuk xotirasi
kam, emulyator o'rniga haqiqiy telefon. Hozirgi holat (faqat o'qib tekshirildi,
2026-11-13): `flutter`, `dart`, `java`, `adb` yo'q, Android SDK yo'q; Git 2.55 bor, C: da
240 GB bo'sh. Flutter hujjatidagi to'liq ro'yxat (Android Studio bilan) ma'lumot uchun:
Flutter SDK va PATH; SDK Platform API 36, Build-Tools, Command-line Tools, Platform-Tools
(Emulator, CMake, NDK ham sanalgan); `flutter doctor --android-licenses`; telefonda Developer
options va USB debugging, ishlab chiqaruvchining USB drayveri.
Manba: [docs.flutter.dev/platform-integration/android/setup](https://docs.flutter.dev/platform-integration/android/setup)
(o'qildi 2026-11-13).

### Sanalardagi ziddiyatlar — qarorlar (TZ 1.31; sanalar TZ 1.32 bo'yicha +4 kun)

1. F4 19-noyabr (avval 15) — **yopildi 2026-11-18** (TZ 1.34) ikki ochiq yozuv bilan: FR-8 birinchi belgi (TZ 1.33) va film sahifasi mobil LCP 4.6 s / INP o'lchanmagan; ikkalasi F9a shartida.
2. Testerlar 23-noyabr (avval 19) — Gemini tarifi hal qilindi: alfa bepul tarifda. **TZ 1.35:** testerlar
   hali yo'q — 29-noyabrgacha yig'iladi, qolgan sanalar +6 kun.
3. Do'konga ariza F7 va F8 ni kutmaydi; ular do'kondan keyin yangilanish. **Qaror.**
4. Play 14 kun, zaxira nol — qabul qilindi, o'zgarish yo'q. Do'konda ko'rinish 29-dekabrdan
   (TZ 1.35; avval 23, undan oldin 19) oldin emas. **Qaror.**
5. iOS hozir rejalanmaydi, yanvarda alohida qaror. **Qaror.**
6. Launch uchun 15% ham, 70% ham shart; 70% yiqilsa onboarding tuzatiladi va qayta
   o'lchanadi, dvigatel emas. **Qaror.**
7. F8 dagi tezlik va qulaylik web launch'dan keyin — qabul qilindi, o'zgarish yo'q.
8. 15% faqat 7 kunlik oynasi yopilgan tavsiyalar bo'yicha, hisobotda soni bilan. **Qaror.**
9. Android ilova F5 hodisalarini yozadi (phase-06) — qabul qilindi.

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
