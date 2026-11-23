# Movie Match — Texnik topshiriq (TZ)

Versiya 1.36 · 2026-11-23 · Holat: tasdiqlangan

Bu hujjat nima qurilishini belgilaydi. Qanday qurilishini `docs/architecture.md`,
qachon qurilishini `docs/roadmap.html`, qanday ko'rinishini esa dizayn tizimi hujjati
belgilaydi. Ziddiyat bo'lsa — shu TZ ustun.

---

## 1. Mahsulot

**Muammo.** Odam nima ko'rishni tanlashga filmni ko'rishdan ko'ra ko'proq vaqt sarflaydi.
Mavjud tizimlar nimani ko'rganini biladi, lekin **nega yoqqanini** bilmaydi. Shuning uchun
"trillerlar yoqadi" degan ikki xil odamga bir xil ro'yxat beradi.

**Yechim.** Har filmni 14 o'lchovli **trait vektori** bilan tavsiflash, foydalanuvchi
baholaridan uning ta'm vektorini qurish, va ikkisini taqqoslab tavsiya berish —
har tavsiyaga oddiy tilda sabab bilan.

**Asosiy da'vo.** Movie Match odamning ta'mini shunchalik tushunadiki, u haqiqatan
ko'radigan film tavsiya qiladi. Butun mahsulot shu bitta da'voga xizmat qiladi.

**Foydalanuvchi.** Kino ko'rishni yaxshi ko'radigan, yiliga 30+ film ko'radigan, tanlovga
vaqt sarflaydigan odam. Tasodifiy tomoshabin emas.

---

## 2. Doira

### MVP ichida (F0–F5)

1. Ro'yxatdan o'tish va kirish
2. Film bazasi va qidiruv
3. Onboarding — ta'mni o'rganish
4. Baholash, sevimlilar, watchlist
5. Shaxsiylashtirilgan tavsiyalar + match darajasi (foiz ichki)
6. "Nega sizga yoqadi" izohi
7. Movie DNA profili
8. AI assistant (tabiiy tilda so'rov)
9. Web ilova (React)

### MVP dan keyin (F6–F8)

10. Flutter mobil ilova
11. Character Match
12. Smart Watchlist guruhlari
13. Group Match

### Doiradan tashqarida (V3+)

Taste Twin (1000+ faol foydalanuvchisiz ishlamaydi) · TV/anime/kitob · ijtimoiy tasma ·
izohlar · reyting agregatori · striming ichida ko'rish

Bu ro'yxatga yangi funksiya **faqat yangi TZ versiyasi bilan** qo'shiladi.

### Tartib va maqsad sanalar (TZ 1.30, sanalar TZ 1.35)

Doira o'zgarmagan, faqat tartib (foydalanuvchi qarori, 2026-11-13). **TZ 1.32
(2026-11-17):** hamma maqsad sana 4 kunga surildi — reja 2026-11-13 dan emas, 2026-11-17
dan hisoblanadi; oraliqlar o'zgarmagan (alfa 14 kun, Play yopiq testi 14 kun, ariza
ko'rigi 7 kun). **TZ 1.35 (2026-11-22):** testerlar hali yo'q — ular **2026-11-29 gacha**
yig'iladi (12 ta Android telefon + Gmail, maqsad 15); alfa shu kundan 14 kun. Qolgan sanalar
+6 kun, oraliqlar o'zgarmagan; Play yopiq testi ham shu testerlar bilan. Faza raqamlari
identifikator bo'lib qoladi: tartib endi raqamlar ketma-ketligiga mos emas. F9 ikkiga
bo'lindi: F9a — web launch, F9b — do'kon launch'i. **TZ 1.37 (2026-11-23):** alfa
2026-11-29 da kim bo'lsa, o'shalar bilan boshlanadi (2026-11-23 da 4 tester), taklif davom
etadi; Google Play (F9b) $25 topilguncha to'xtaydi; testerlar Android ilovani APK fayl
sifatida oladi; web launch'ning pulsiz yo'li foydalanuvchi tanlovini kutadi. **TZ 1.38:** web launch
AI'siz; F8 va F7 F9a dan keyin.

| # | Faza | Maqsad sana | Shart |
|---|---|---|---|
| 1 | F4 — AI assistant, yopish | 2026-11-19 | **Yopildi 2026-11-18** (TZ 1.34), ikki ochiq yozuv bilan: FR-8 birinchi belgi (TZ 1.33) va F3 band 5 — film sahifasi mobil LCP 4.6 s, INP o'lchanmagan. Ikkalasi F9a shartiga ko'chdi |
| 2 | F5 — alfa kodi (telemetriya, metrika, "noto'g'ri" tugmasi) | 2026-11-22 | F4 yopilgan |
| 3 | F5 — testerlar yig'iladi, alfa boshlanadi | 2026-11-29: kim bo'lsa, o'shalar bilan (TZ 1.37) | F5 texnik gate'i yashil (2026-11-22); maqsad 12 ta Android telefon + Gmail, 15 gacha (TZ 1.35); taklif davom etadi; 2026-12-06 gacha 12 bo'lmasa — qaror o'sha son bilan, "zaif signal" (TZ 1.37) |
| 4 | F6 — mobil ilova, **Android birinchi**, alfa ketayotgan paytda | ekranlar 2026-12-05 gacha (reja); testerlarga APK fayl, Play'siz (TZ 1.37) | F5 texnik gate'i; mahsulot darvozasini kutmaydi. Play yopiq testi F9b ga ko'chdi (TZ 1.37) |
| 5 | F5 — alfa qarori (mahsulot darvozasi) | 2026-12-13 | 2 hafta ma'lumot (29-noyabrdan) |
| 6 | F9a — web launch tayyorligi va ochiq web launch | 2026-12-15, **AI'siz** (TZ 1.38) | **F5 mahsulot darvozasi o'tgan** (15% va 70%); **AI'siz (TZ 1.38):** assistant yashirin, film sahifasidagi izoh faqat keshdan yoki shablondan (`named_traits`), so'rovda Gemini chaqirilmaydi; Gemini pullik tarifi va FR-8 mezoni (TZ 1.33) — assistant qaytishidan oldin, launch uchun emas; film sahifasi jonli saytda mobil LCP < 2.5 s (3 o'lchov mediani) va INP < 200 ms (TZ 1.34) |
| 7 | F9b — do'konga ariza (Google Play) | **to'xtatilgan, $25 topilguncha** (TZ 1.37). Play yopiq testi — pul va 12 tester bo'lganda; ariza — 12-tester qo'shilgandan 14 kun keyin; do'konda — Google ko'rigidan keyin (odatda 7 kungacha) | F6 gate'i, F9a, Play yopiq testi 14 kun (TZ 1.31: F7 va F8 ni kutmaydi) |
| 8 | F8 — Smart Watchlist + Group Match (va sayqal) | F9a (web launch) dan keyin (TZ 1.38) | F9a |
| 9 | F7 — Character Match, yurist ko'rigigacha flag ortida | F8 dan keyin, yangilanish sifatida | F8 gate'i |
| — | iOS | **hozir rejalanmaydi**; alohida qaror, 2027-yil yanvar | Avval Android (TZ 1.31) |

**Qurish alfa paytida ketadi, ochiq launch alfa natijasidan keyin.** F6 va F9a ishlari
alfa davomida (2026-11-29 — 2026-12-13) quriladi; ochiq launch (web ham, do'kon ham)
F5 mahsulot darvozasi o'tgandan keyin bo'ladi. 15% metrikasi yiqilsa — dvigatel qayta
ishlanadi va launch to'xtaydi (§8).

**TZ 1.31 (foydalanuvchi qarori, 2026-11-13):** do'konga ariza (F9b) F7 va F8 ni kutmaydi —
sharti F6 gate'i, F9a va Play yopiq testi; F8 va F7 do'kon launch'idan keyin yangilanish
bo'lib chiqadi (TZ 1.38: F8 va F7 F9a dan keyin boshlanadi, do'konni kutmaydi). Google ariza ko'rigi odatda 7 kungacha, shuning uchun do'konda ko'rinish
**2026-12-29 dan oldin emas** (sana TZ 1.35; TZ 1.37 dan beri F9b to'xtatilgan, sana yo'q). iOS hozir rejalanmaydi: avval Android, iOS — alohida qaror,
2027-yil yanvar.

### Backlog

Keyinga qoldirilgan ishlar: texnik qarz va keyingi fazaga tegishli g'oyalar
(CLAUDE.md: joriy fazaga sig'maydigan narsa shu yerga yoziladi). Funksiya emas —
yuqoridagi doiraga ta'sir qilmaydi.

| Band | Qachongacha | Qo'shilgan |
|---|---|---|
| **Sabab traitlarining takrorlanishi** (FR-5/FR-6, TZ 1.27). Sabab tomonida nomlanadigan traitlar hovuzi akkauntga qat'iy biriktirilgan: yo'nalishi ≥ 0.40 σ bo'lgan traitlar, uchta akkauntda **3 / 4 / 6 ta**. Natijada eng ko'p nomlangan trait sabab tomonidagi filmlarning **64.3 / 51.8 / 43.5%** ida uchraydi, ya'ni "nega mos" matni doim bir xil jihatlar haqida. Kesimlar bilan hal bo'lmaydi (o'lchandi, ADR 0008): 0.30 σ da hovuz kengayadi, lekin aynan tuzatilgan nuqson qaytadi. Saralash tartibi ham ta'sir qilmaydi — sabab tomonidagi filmlarning 96–100% ida nomzod uchtadan ko'p emas. **Ta'sir qiladigan tugmalar:** `WHY_TRAITS` (hozir 3), jumla matni, yoki filmlar bo'yicha nomlangan traitni almashtirish. Qaror foydalanuvchida; o'lchov va raqamlar `docs/decisions/0008-closeness-reasons.md` | Alohida qaror | 2026-10-22 |
| `services/api/scripts/migrate_db.py` ga testlar (himoyalar: `lock_timeout`, COMMIT'dan keyin yangi ulanishda tekshiruv, `movies` soni). Hozircha faqat qo'lda sinalgan | Keyingi migratsiyadan oldin | 2026-09-29 |
| `services/api/scripts/select_catalogue.py` ga testlar (`select`: o'n yillik kvotasi, til chegarasi, ikkinchi o'tish, traitli filmlarning majburan kirishi va kvotaga hisoblanishi, sanasiz filmlar). Hozircha faqat qo'lda sinalgan (2026-10-01) | 2-bosqichdan keyin, ro'yxat qayta tuzilishidan oldin | 2026-10-01 |
| Embedding tokenlarini **guruhlab** sanash: har filmga alohida `count_tokens` o'rniga 25 ta matnni bitta chaqiruvda sanash; `tokens=reported` saqlanadi, hujjatda guruhlangan son per-request yig'indisidan ~0.56% kam ekani qayd etiladi (2026-10-02, 25 film: 4 265 vs 4 289). **Nega namuna (har 25-film) + kalibrlangan nisbat emas:** chaqiruvlar soni bir xil, lekin guruhda har filmning o'zi sanaladi; nisbat (4.6 belgi/token) shu 25 filmda jami +2%, alohida filmda 9% gacha xato berdi va til tarkibi o'zgarsa (yangi katalog) qayta kalibrlashni talab qiladi, natija esa `tokens=estimated` bo'lib qoladi. Maqsad: run vaqti — har film uchun bitta tarmoq so'rovi kamayadi. 2026-10-02 dan `count_tokens` xatosi run'ni to'xtatmaydi, shuning uchun bu shoshilinch emas | 5 000 film bosqichidan oldin | 2026-10-02 |
| Movie DNA AI xulosasi (FR-7). Hozir web uchta eng kuchli traitdan shablon jumla quradi; `/me/dna` `summary: null` qaytaradi. AI versiyasi uchun kesh jadvali (migratsiya) va narx qarori kerak | Keyin, F5 dan keyin (TZ 1.31) | 2026-09-29 |
| DNA ulashish uchun server tomonda rasm (FR-7). Ulashish rasmining o'zi brauzerda yasaladi (dizayn brifi v2, `docs/ui.md`, 2026-10-02); server varianti **link preview** (ommaviy havola ochilganda ko'rinadigan rasm) uchun keyin kerak. Ommaviy havola (token, maxfiylik) dizayni kerak | Keyin, F5 dan keyin (TZ 1.31) | 2026-09-29 |
| Movie DNA: **Wrapped tuzilmasi** (vertikal "hikoya" bloklari: baholar soni, eng kuchli tomon, gul, xulosa, statistika, ulashish) va **brauzerda chiziladigan ulashish rasmi** (`canvas`, 1080×1920, `navigator.share`). Dizayn 4-bosqichidan ko'chirildi (foydalanuvchi qarori, 2026-10-06): 4-bosqichda faqat radial DNA diagrammasi quriladi. Tavsifi `docs/ui.md`, 6-bo'lim — o'zgarishsiz qoladi | 4-bosqichdan keyin, alohida qaror | 2026-10-06 |
| Qidiruvda striming provayderi filtri (F3 prompti). Katalogda provayder ma'lumoti yo'q — avval ingestion (TMDB watch providers). **2026-10-12:** keyingi band bilan birga — UZ uchun ma'lumot yo'q | Keyingi band bilan | 2026-09-29 |
| Onboarding: film tanlashdan baholashga o'tishda CLS **0.021** (mock, 390 px, ru; 2026-10-12, onboarding saqlash xatosini tekshirayotganda ko'rildi). Manbai aniqlanmagan: qadam slayd-animatsiyasi, poster yoki sticky foot bo'lishi mumkin — avval layout-shift manbalarini (`sources`) o'lchash kerak. Kichik, lekin "CLS 0" qoidasiga zid | 6-bosqichda yoki alohida | 2026-10-12 |
| **"Qayerdan ko'rish mumkin" — hozir qurilmaydi** (foydalanuvchi qarori, 2026-10-12: asosiy bozor uchun doim bo'sh chiqadi). TMDB/JustWatch O'zbekistonni qo'llamaydi: TMDB'ning 139 region ro'yxatida UZ yo'q, KZ, KG, TJ, TM ham yo'q; qo'shnilardan faqat UA, BY, AZ. **O'lchov** (2026-10-12): katalogdagi 500 tadan 100 ta tasodifiy film (`random.Random(20261012)`), `GET /movie/{id}/watch/providers` — qamrov US 97/100, TR 65, RU 63, **UZ 0**. **Variantlar:** (a) foydalanuvchiga region tanlatish va RU/TR ni ko'rsatish — avval Kinopoisk/Okko O'zbekistondan amalda ishlashini tekshirish kerak, **tekshirilmagan**; (b) mahalliy xizmatlar ro'yxatini qo'lda yuritish; (c) litsenziyali mahalliy striming xizmati bilan hamkorlik. Shartlari: `docs/costs.md`, 3-bo'lim | Testerlardan "qayerdan ko'rasiz?" savoliga javob kelgandan keyin | 2026-10-12 |
| Onboardingda "nimasi yoqdi?" chiplari 14 ta traitning hammasini ko'rsatadi; dizaynda filmga xos ~5 ta. Filmning kuchli traitlarini onboarding javobiga qo'shish kerak | **Alfadan keyin** (2026-12-13 dan keyin; alfa paytida dvigatel va onboarding o'zgarmaydi; TZ 1.31) | 2026-09-29 |
| Izohlarning kunlik limiti (FR-6, `explanation_daily_calls_per_user` = 20) tugaganda foydalanuvchi buni bilmaydi: film sahifasi jim zaxira matnga ("Ta'mingiz og'gan jihatlarda bu film ko'p filmlardan kuchliroq: …") o'tadi. Interfeys limit tugaganini aytishi kerak (masalan, "Bugungi izohlar tugadi, ertaga yangilanadi"), yoki zaxira matnga o'tish aniq belgilanishi kerak. **Yarmi bajarildi (2026-10-13):** API endi sababni beradi — `ExplanationOut.reason` (`no_generator`, `daily_cap`, `no_taste`, `no_traits`, `nothing_named`, `failed`, `rejected`), va interfeys endi jumla kelmasligi aniq bo'lganda indikatorni ko'rsatmaydi (`lib/explanations.ts`). **Qolgani:** limit tugaganini foydalanuvchiga **aytish** — uch tilda matn kerak, shuning uchun alohida qadam. F2 qo'lda tekshiruvida topildi (2026-10-02): ~20 ta izoh yaratilgan, limitga yetilgan, keyin zaxira matn. Narx muammo emas (o'lchangan, 2026-10-02, 19 ta cost qatori): izoh o'rtacha 187 kirish / 29.6 chiqish tokeni → standart tarifda ($0.30 / $2.50) $0.00013; limit to'liq ishlatilsa oyiga 600 ta ≈ $0.08 — TZ §5 maqsadi ($0.20) ichida | **Testerlardan oldin** (2026-11-23; TZ 1.31) | 2026-10-02 |
| Izoh keshining kalitiga sabablar: `explanations` qatorida izoh qaysi sabablar bilan yozilgani saqlanadi, sabablar o'zgarsa (yangi qoida, katalog o'sishi, ta'm o'zgarishi) — kesh o'tkazib yuboriladi va izoh qayta yoziladi. Migratsiya kerak. Hozircha qoida o'zgarganda eski izohlar qo'lda o'chiriladi (2026-10-02: bitta foydalanuvchining izohlari, ruxsat bilan; 2026-10-22: TZ 1.27 da sabab tomonidagi qatorlar, ruxsat bilan — ADR 0008) | Keyin, F5 dan keyin (TZ 1.31) | 2026-10-02 |
| Traitlarni qayta baholash (trait ta'riflari va prompt): `visual_style` (o'rtacha 75.8, σ 14.3) va `emotional_intensity` (72.5, σ 14.3) deyarli hamma filmda baland — trait ajratmaydi; promptga "oddiy film = 50" kabi shkala ko'rsatmasi kerak. **Arzon, lekin jarayon qimmat:** 500 film ≈ $0.28 standart tarifda (bepul tarifda $0), lekin qayta baholash 50 filmlik qo'lda ko'rikni bekor qiladi (qayta o'tkaziladi) va barcha embeddinglarni qayta hisoblashni talab qiladi (embedding matnida trait xulosasi bor) | Alohida qaror; 5 000 film bosqichidan oldin | 2026-10-02 |
| Film ma'lumotini tarjima qilish (nom, tavsif) o'zbek va rus tillariga. Hozir interfeys uch tilda, film matni esa ingliz tilida (TMDB `en-US`). Variantlar: TMDB'ning `translations` ma'lumoti (rus tilida ko'p, o'zbekchada kam) yoki LLM tarjimasi (pul, kesh kerak). **Foydalanuvchi so'rovi (2026-10-09):** rus tili uchun TMDB `language=ru-RU`, hozircha backlog'da qoldi (foydalanuvchi qarori). Janr nomlari shu kuni interfeys lug'ati orqali tarjima qilindi (§5). Kerak bo'ladi: tarjimalar jadvali va migratsiya, ingestion'da har film uchun til bo'yicha so'rov, API'ga `lang` parametri, qidiruv ruscha nom bo'yicha | Keyin, F5 dan keyin (TZ 1.31) | 2026-10-02 |
| **Ta'm yoqmagan filmlardan ham o'rgansin** (FR-5). Ta'm vektori faqat yoqqan filmlardan quriladi; 5 va past baholar vazni 0 — bu foiz bahoni bashorat qila olmasligining ehtimoliy asosiy sababi (2026-10-05: AUC 0.52, leave-one-out 0.44). Alohida traitlarda signal bor (bitta akkaunt: `realism` AUC 0.75, `emotional_intensity` 0.73, `plot_twist` 0.67), lekin 14 traitli masofada ular suyulib ketadi; 25 filmda 14 trait sinalgani uchun bu tasodif ham bo'lishi mumkin. **Nima kerak:** foydalanuvchida kamida 30 ta 8+ va 30 ta ≤ 5 baho (13 va 12 da AUC xatosi ±0.12, 30 va 30 da ±0.07); 14 ta vaznni foydalanuvchining o'zidan o'rganish uchun ~150 baho. **Qanday o'lchanadi:** 8+ va ≤ 5 guruhlari bo'yicha AUC, leave-one-out bilan (har film o'zisiz qurilgan profilga qarshi); muvaffaqiyat — AUC ≥ 0.70 va 95% ishonch oralig'ining pastki chegarasi 0.5 dan yuqori. Hozirgi o'lchov skripti tavsifi: `docs/STATUS.md` | Alohida qaror; baholar to'plangach | 2026-10-05 |
| ~~500 filmni o'n yillik/til kvotasi bilan tanlash (FR-2). Bazadagi 5 000 film 5 000 uchun rejalashtirilgan; `traits submit --limit 500` eng mashhurlarini oladi va o'n yillik taqsimoti buzilishi mumkin. Yechim: `ingest --plan-only --target 500` (TMDB, bepul) ro'yxatini `traits submit --ids` ga berish~~ **Bajarildi (2026-10-01):** `services/api/scripts/select_catalogue.py` kvota siyosatini bizning 5 000 lik katalogimizga qo'llaydi, traitli 50 film majburan kiradi; ro'yxat `docs/catalogue-500.md` (54% ingliz, 26 til). `ingest --plan-only` (TMDB) varianti rad etildi: kunlik o'zgaradi, 75% ingliz chiqdi | 1-bosqichdan keyin, 500 ga o'tishdan oldin | 2026-09-30 |
| Feed keshi foydalanuvchi bo'yicha: `recommend()` natijasi xotirada, kalit — `taste_updated_at`, ko'rilgan filmlar to'plami (baho, watched, dismiss) va 10 daqiqalik muddat; izohlar har so'rovda yangidan. Kutilgan natija: kesh topilganda server ~0.1–0.3 s, topilmaganda o'zgarmaydi. Render Starter qaroridan keyin qaytiladi: Starter'da (0.5 CPU) keshsiz ham feed ~1 s bo'lishi kutiladi va kesh foydasi kamayadi | Render Starter qaroridan keyin | 2026-10-09 |
| To'liq sahifa o'tishi (eski sahifa so'nadi, yangisi 8px ko'tariladi, qobiq qimirlamaydi): `createBrowserRouter` + `RouterProvider` ga o'tish kerak — `BrowserRouter` da React Router'ning `viewTransition` ishlamaydi (`docs/ui.md`, 7). ~1–1.5 soat. 2026-10-09 da qilinmadi: router o'zgarishi marshrutlar va kirish himoyasiga tegadi, yakunlash kunida xavfli. Hozir: 120 ms opacity paydo bo'lish | Ochiq | 2026-10-09 |
| Dialog qatlami uchun avtomatik brauzer testi: telefon va keng ekranda ochiq dialog yuqori panel, pastki menyu va qidiruv qatori ustida turishini `elementFromPoint` bilan tekshirish. jsdom'da layout yo'q, shuning uchun brauzer test vositasi kerak (Playwright) — o'rnatish alohida qaror. Hozircha qo'lda brauzer o'lchovi (`docs/ui.md`, "Topilgan va tuzatilgan nuqson", 2026-10-09) | Ochiq | 2026-10-09 |
| Baho chiplari ("nimasi yoqdi?") faqat 8.0 dan yuqori baholarda chiqadi — FR-3 qabul mezoni shunday yozilgan. **Tester e'tirozi (2026-10-13):** 9–10 da chiqdi, 7–8 da chiqmadi, natijada Movie DNA kam signaldan quriladi. **FR-3 o'zgarmadi** (foydalanuvchi qarori, 2026-10-13): hamma baholarda ko'rsatish TZ o'zgarishini talab qiladi, va past baholardagi javob hozir hech qayerda ishlatilmaydi — ta'm vektori faqat yoqqan filmlardan quriladi (≤ 5 vazni 0), shuning uchun chip yig'ilib, hech narsaga ta'sir qilmaydi. Sharti — pastdagi "Ta'm yoqmagan filmlardan ham o'rgansin" bandi: u bajarilsa, past baholarda "nimasi yoqmadi?" chiplari ma'noga ega bo'ladi | "Ta'm yoqmagan filmlardan ham o'rgansin" bandi bilan birga | 2026-10-13 |
| Tavsiyalar eski tomonga og'adi (tester, 2026-10-13: Interstellar, Oppenheimer, Dark Knight, Whiplash, Gone Girl → Drunken Angel 1948, Lawrence of Arabia 1962, The Wages of Fear 1953, High and Low 1963, Pickpocket 1959). **O'lchandi** (`docs/phase-2-status.md`, "Recommendations skew old"): ANN neytral (26%, katalog bilan bir xil), trait match 34% ga ko'taradi, **MMR 40% ga** — eng katta qadam, chunki xilma-xillik embedding masofasi bilan o'lchanadi va 1948 yilgi film zamonaviy filmdan eng uzoq. Katalogning o'zi 26% pre-1980 (`decade_quotas`), shuning uchun neytral tartibda ham har to'rtinchi film eski. **Variant:** MMR relevantligiga recency jarimasi (`match/100 − w·(1 − (yil−1920)/106)`) — match foiziga tegmaydi, FR-5 qo'lda tekshirilishi saqlanadi; `w = 0.02` → 30% (ikki film tushadi), 0.05 → 15%, 0.10 → 5%. Yoki katalog kvotalarini qayta tuzish (qimmat: trait qayta to'lanadi, 1-bosqich ko'rigi bekor bo'ladi). Popularity muammo emas (bo'lim mediani 21.9, katalog 19.6). **Bajarildi (2026-10-13, foydalanuvchi qarori):** `recency_weight = 0.02` (`app/config.py`, `recommend.recency_penalty`, TZ 1.21); jonli katalogda tekshirildi — 30%, yil mediani 2009. **Ochiq qolgani:** sifat chegarasi — 2026 yilgi notanish filmlar (Disclosure Day, Elize) bo'lim o'ninchi o'rniga chiqadi, `tmdb_vote_count` (katalog mediani 4 072) shu uchun vosita | Sifat chegarasi: **alfadan keyin** (2026-12-07 dan keyin; TZ 1.31) | 2026-10-13 |
| NSFW/ekstremal filmlar ogohlantirishsiz chiqadi (tester, 2026-10-13: Baise-moi, Caligula, Irreversible). Qidiruv faqat TMDB `adult` ni filtrlaydi, u esa amalda pornografiya uchun — bu filmlar `adult = false`. Tavsiyalarga tushmaydi (trait vektori bo'lmasa `movie_traits` join'i chiqarib tashlaydi), lekin qidiruv, Home'dagi "mashhur" va to'g'ridan-to'g'ri havola ko'rsatadi. Bazada **bor** signallar: `trait_failures.last_error` (`PROHIBITED_CONTENT` — 500 lik tanlovda 13 film, `docs/catalogue-500.md`), `violence` traiti (faqat traitli filmlarda), janrlar. **Yo'q:** yosh reytingi — TMDB `release_dates` dan `certification` ni ingestion qilish kerak (migratsiya + ingestion qadami). Qaror kerak: filtrlash (yashirish) yoki ogohlantirish (ko'rsatish, belgi bilan) | **Testerlardan oldin** (2026-11-23; TZ 1.31) | 2026-10-13 |
| Push: "watchlist'dagi film chiqdi" (F6 prompti, FCM). Katalogda film qayerda va qachon ko'rish mumkinligi haqida ma'lumot yo'q ("Qayerdan ko'rish mumkin" — hozir qurilmaydi, yuqorida), shuning uchun bu push'ni qurib bo'lmaydi. Haftalik tavsiya push'i F6 da qoladi (2026-12-08 dan keyin) | ko'rish ma'lumoti paydo bo'lganda | TZ 1.37 (2026-11-23, foydalanuvchi) |

---

## 3. Trait vektori — mahsulotning yadrosi

14 o'lchov, har biri 0–100. To'liq ro'yxat va ta'riflar:
`packages/shared/traits.json`. Tartib hech qachon o'zgarmaydi.

| # | Kalit | O'zbekcha | Izoh |
|---|---|---|---|
| 1 | `psychological_complexity` | Psixologik murakkablik | Ichki holat, ishonchsiz idrok |
| 2 | `plot_twist` | Syujet burilishi | Oldingi voqealarni qayta ma'nolantiruvchi ochilish |
| 3 | `mystery` | Sirlilik | Ma'lumotni yashirish, tomoshabinni yechimga jalb qilish |
| 4 | `character_depth` | Personaj chuqurligi | Axloqiy noaniqlik, ichki dunyo |
| 5 | `emotional_intensity` | Hissiy zichlik | Hissiy ta'sirga tayanish darajasi |
| 6 | `pacing` | Temp | 0 = sekin, 100 = to'xtovsiz |
| 7 | `humor` | Hazil | Komediya miqdori va markaziyligi |
| 8 | `romance` | Romantika | Romantik chiziq og'irligi |
| 9 | `action` | Ekshn | Jismoniy sahnalar, quvish, jang |
| 10 | `violence` | Zo'ravonlik | Ochiqligi va chastotasi (filtr uchun ham) |
| 11 | `visual_style` | Vizual uslub | Operatorlik va dizayn o'ziga xosligi |
| 12 | `realism` | Realizm | 0 = fantastik, 100 = hayotiy |
| 13 | `darkness` | Qorong'ulik | 0 = yorug', 100 = umidsiz |
| 14 | `ending_ambiguity` | Ochiq tugash | 0 = to'liq yechilgan, 100 = ataylab ochiq |

**Qoidalar:**
- Trait sifatni o'lchamaydi. "Yaxshi film" degan o'lchov yo'q.
- 50 — "o'rtacha film uchun normal", "noma'lum" emas.
- Yangi o'lchov qo'shish = `traits.json` ga qo'shish + `app/traits.py` ga qo'shish +
  butun bazani qayta hisoblash. Bu qimmat, shuning uchun ro'yxat boshidan to'liq.

---

## 4. Funksional talablar

Har talabning qabul mezoni bor. Mezon bajarilmasa, talab bajarilmagan hisoblanadi.

### FR-1 · Autentifikatsiya

Foydalanuvchi Google, Apple yoki email (magic link) orqali kiradi.

**Qabul mezoni:**
- Uchala usul ham ishlaydi va bir xil foydalanuvchi profiliga olib keladi.
- Token muddati tugaganda avtomatik yangilanadi, foydalanuvchi qayta kirmaydi.
- Akkauntni o'chirish barcha ma'lumotni 30 kun ichida butunlay o'chiradi.
- Mehmon rejimi yo'q — tavsiya uchun profil shart.

### FR-2 · Film bazasi

**500 film** birinchi versiyada: nomi, yili, davomiyligi, tavsifi, janrlari,
aktyorlari, rejissyori, kalit so'zlari, posteri.

Son `catalogue_target` sozlamasida turadi, kodda emas — ko'tarish bitta qator o'zgarishi.
20 000 dan 5 000 ga (v1.2), keyin 5 000 dan 500 ga (v1.5) tushirildi: trait va embedding
narxi film soniga to'g'ri proporsional (`docs/costs.md`), provayder hali tanlanmagan, va
birinchi maqsad — mahsulot ishlashini tasdiqlash. Kamroq mashhurlari shundan keyin
qo'shiladi. Bazada 5 000 film allaqachon yuklangan; ulardan faqat trait'lisi tavsiya va
onboarding'da qatnashadi.

**Qabul mezoni:**
- TMDB'dan kunlik sinxronizatsiya, uzilishdan keyin davom eta oladi.
- Har filmda trait vektori va embedding bor (100% qamrov).
- Katalog o'n yilliklar bo'ylab taqsimlanadi va bitta til bir o'n yillik kvotasining
  55% dan ortig'ini egallamaydi — aks holda katalog faqat so'nggi yillardagi Gollivud bo'lib qoladi.
- Qidiruv 300 ms ichida javob beradi.
- Ma'lumot manbai `app/pipelines/tmdb.py` dan tashqariga sizib chiqmaydi.
- TMDB bepul tarifida quriladi; tijorat litsenziyasi monetizatsiyadan oldin kerak (ADR 0002).
- MovieLens va IMDb datasetlari ishlatilmaydi — litsenziyalari tijoratni taqiqlaydi.

### FR-3 · Onboarding

Yangi foydalanuvchi uchta qadamdan o'tadi: filmlar tanlash → baholash → tayyor.

**Qabul mezoni:**
- Kamida 10 ta film baholanmaguncha tavsiya ko'rsatilmaydi.
- Butun jarayon 3 daqiqadan kam vaqt oladi (o'lchanadi). **Holat (2026-10-10):** bajarildi deb
  hisoblanadi — foydalanuvchi jonli saytda o'tdi, kutish sezilmadi; alohida vaqt o'lchovi
  qilinmaydi (foydalanuvchi qarori). Deploy'dan oldin 3:10 edi, 58 s i baho saqlash kutishi.
- 8.0 dan yuqori baho qo'yilganda "nimasi yoqdi?" chiplari chiqadi.
- Yarim yo'lda chiqib ketgan foydalanuvchi qaytganda o'sha joydan davom etadi.

### FR-4 · Baholash va ro'yxatlar

Foydalanuvchi film baholaydi (0.5–10.0), watchlistga qo'shadi, ko'rilgan deb belgilaydi.

**Qabul mezoni:**
- Baho darhol saqlanadi, optimistik UI, xatolikda orqaga qaytariladi.
- Bitta film bitta foydalanuvchida bitta bahoga ega (qayta baholash yangilaydi).
- Baho qo'yilgach ta'm vektori 5 soniya ichida qayta hisoblanadi.

### FR-5 · Tavsiyalar

Foydalanuvchi bosh sahifada sababli bo'limlarga ajratilgan tavsiyalar oladi.

**Qabul mezoni:**
- Har tavsiyada match foizi (0–100, **ichki**: tartiblash, qo'lda tekshirish va nosozlik
  tahlili uchun; interfeys raqamni ko'rsatmaydi), **match darajasi** (quyida) va sabab
  traitlari (0–3 ta, quyidagi qoida bo'yicha). Film hech bir traitda ajralib turmasa,
  ro'yxat bo'sh — interfeys "umuman mos" deydi.
- Foydalanuvchining katalogdagi eng uzoq 25% filmi tavsiya qilinmaydi (`match_floor_share`;
  1.13 gacha "60% dan past match ko'rsatilmaydi" edi — u 473 filmdan 2 tasini chiqarardi).
- Ko'rilgan va rad etilgan filmlar chiqmaydi.
- Bir bo'limda bitta rejissyordan 2 tadan ko'p film bo'lmaydi (xilma-xillik).
- **Recency jarimasi** (1.21, 2026-10-13): bo'lim ichida film yoshi uni ozgina pastga
  tortadi — `jarima = w · (hozirgi yil − yil) / (hozirgi yil − 1920)`, `w =
  recency_weight` (standart **0.02**), sanasi yo'q film to'liq jarima oladi. **Faqat MMR
  relevantligida:** match foizi (quyidagi formula) va daraja uni ko'rmaydi, shuning uchun
  match saqlangan sonlardan qo'lda hisoblanishi saqlanadi. Asos — o'lchov
  (`docs/phase-2-status.md`): MMR xilma-xillikni embedding masofasi bilan o'lchagani
  uchun bo'limdagi pre-1980 ulushini 32% dan 40% ga ko'tarardi, katalogning o'zi esa 26%;
  `w = 0.02` da 30% (jonli tekshirildi: 20 filmdan 6 tasi pre-1980, yil mediani 2009).
- Javob 500 ms ichida (kesh bilan 100 ms).

**Match formulasi** — ochiq va qo'lda tekshirilishi mumkin:

```
w[i]     = foydalanuvchining i-o'lchovdagi izchilligi (0..1)
d        = sqrt( Σ w[i] * (taste[i] - movie[i])² / Σ w[i] ) / 100
match    = round( 100 * (1 - d) )
```

Izchillik: foydalanuvchi yuqori baholagan filmlarda o'lchov qiymatlari qanchalik
bir joyda to'planganidan kelib chiqadi. Tarqoq bo'lsa — o'sha o'lchov shu odam uchun
muhim emas, vazni past.

**Match darajasi** (1.13, 2026-10-05) — interfeys ko'rsatadigan yagona match signali.
Foiz bahoni bashorat qilishini ko'rsata olmadik (bitta akkaunt, 13 ta 8+ va 12 ta ≤5
film: AUC 0.52, leave-one-out 0.44; `docs/STATUS.md`), lekin u trait bo'yicha uzoqlikni
o'lchaydi. Muammo raqamning soxta aniqligi edi. Daraja — rostgo'y da'vo: "katalogda sizga
eng yaqinlaridan biri".

```
raw[f]   = 100 * (1 - d)   — match foizining yaxlitlanmagan qiymati, katalogdagi har bir
                             traitli film f uchun shu foydalanuvchiga
o'rin    = raw bo'yicha kamayish tartibida (1 — eng yaqini); teng qiymat chegarada ichkarida
kuchli   : o'rin <= N                    N = match_strong_top_n   (standart 5)
yaxshi   : o'rin <= ceil(0.15 * katalog) match_good_share         (standart 0.15; 1.14 gacha 0.35)
           — hisoblanadi va API javobida qoladi, interfeysda ko'rsatilmaydi (1.16)
pastki   : o'rin >  ceil(0.75 * katalog) match_floor_share        (standart 0.25)
```

**Interfeysda daraja ikki holatda** (1.16): **"STRONG MATCH"** (qizil) — eng yaqin N=5
film; qolgan hammasi — neytral kicker **"YOU AND THIS FILM"**. "Yaxshi" hisoblanadi va
API'da `band: "good"` bo'lib qoladi (tartiblash va keyingi qaror uchun; sozlama ham
qoladi), lekin film sahifasi, Home (hero va kartalar) va watchlist uni chizmaydi.
Sabab — o'lchov: Home ta'rifan eng yaqin filmlardan tuziladi, shuning uchun "yaxshi"
Home'dagi film sahifalarining 68% ida (0.15 da; 0.35 da 90%) chiqardi — hech narsani
ajratmaydigan yorliq shovqin (`docs/STATUS.md`, "35% → 15%").

"Kuchli" — mutlaq son (ulush emas): Home'dagi qizil belgilar katalog o'sganda ham kam
qoladi (5 da bitta akkauntning birinchi ekranida 2–3 ta; 10% bo'lsa 11 ta edi). Qizil —
faqat "kuchli". Film sahifasida ring yo'q: sarlavha (kicker) "Why you" panelining
yuqorisida, jumla asosiy signal; Home hero'da ham xuddi shu kicker. Chegaralar har foydalanuvchi uchun saqlangan
sonlardan qayta hisoblanadi (`users.taste_*`, `movie_traits.vector`).

**Sarlavha jumlani nomlaydi** (1.25, 2026-10-16) — sarlavha avvalo band'ni emas, ostidagi
jumlaning turini aytadi. Band va tomon (`trait_side`, 1.23) boshqa o'lchovlar: film band
bo'yicha "good", tomon bo'yicha "difference" bo'lishi mumkin (Godzilla, 2026-10-15), va
band'ni ko'rsatish foydalanuvchiga jumla maqtovmi yoki farq bayonimi — aytmaydi.

| Holat | Sarlavha | Rang |
|---|---|---|
| band `strong`, tomon `difference` **emas** | "STRONG MATCH" | qizil |
| tomon `reason` | "WHY IT SUITS YOU" | neytral |
| tomon `difference` (band `strong` bo'lsa ham) | "HOW IT DIFFERS" | neytral |
| hech narsa nomlanmagan (band `strong` emas), yoki match yo'q | "YOU AND THIS FILM" | neytral |

**Qizilni faqat farq tomoni bosadi.** `strong` + `difference` holatida qizil "STRONG MATCH"
ustida farq jumlasi turardi — 1.23/1.24 da olib tashlangan ziddiyat qaytib kelardi. Hozir
katalogda bunday film yo'q (8 akkauntda `strong` filmlar 100% sabab tomonida), lekin
katalog o'sgach paydo bo'ladi. **Jimlik esa ziddiyat emas:** jumla yo'q, lekin band rost,
va qizil sarlavha aynan band'ni aytadi; hech narsa nomlanmagan film 14 traitning hammasida
o'rta oraliqda turadi (1.27), bu esa moslikka qarshi dalil emas — shuning uchun `strong` +
jim holatida qizil qoladi. Matnlar uch tilda va qabul mezoni: `docs/ui.md`,
"Kicker qoidasi".

**Trait qoidasi** (1.27, 2026-10-22; match foiziga ta'sir qilmaydi) — qaysi traitlar
ko'rsatiladi va **qaysi tomonda**. Bitta masofa o'lchovi, ikki tomonda teskari ma'no:

```
μ[i], σ[i] = katalogdagi barcha traitli filmlarning i-o'lchov bo'yicha o'rtachasi va
             standart og'ishi (populyatsiya)
kattalik[i]  = |movie[i] - taste[i]| / σ[i]   film foydalanuvchidan qancha narida
yo'nalish[i] = |taste[i] - μ[i]|     / σ[i]   foydalanuvchi oddiy filmdan qancha narida

sabab : kattalik <= 0.35  VA  yo'nalish >= 0.40     (ikkisi ham sozlama)
farq  : kattalik >= 1.0                             (sozlama)
boshqa holda: hech narsa

sabablar: eng KICHIK kattalik birinchi (eng yaqin trait yetakchi), 3 tasi
farqlar : eng KATTA w[i]·kattalik birinchi, 3 tasi
```

**Sabab — yaqinlik.** "Sizga mos" degan da'vo moslikni o'lchashi kerak: film
foydalanuvchining o'z darajasida turishi. **Yo'nalish — qo'riqchi, ma'no emas:** yaqinlik
faqat foydalanuvchining aniq ta'mi bor traitida gapiradi, chunki katalog o'rtachasida
turgan traitda ustma-ust tushish foydalanuvchi haqida hech narsa aytmaydi.

**Sabablar ustun:** filmda bitta sabab bo'lsa ham, farqlar yozilmaydi. Farq faqat sabab
umuman bo'lmaganda chiqadi; ikkalasi ham bo'lmasa — panel hech narsa yozmaydi (eski
"ta'mingizga umuman mos" jumlasi olib tashlandi: u ortida hech narsa bo'lmagan da'vo edi).
**Jimlik ma'nosi:** hech bir trait na yetarlicha yaqin va aniq, na 1 σ narida — film o'rta
oraliqda (1.23 dagi "14 traitda eng yaqin" ma'nosi bu qoidada o'rinli emas).

Bu qoida **1.23 ning kesimlarini almashtiradi** (sabab 0.5 σ "bir xil tomonda"). Nega:
jonli saytda (2026-10-22, `d394a840`, Up) "WHY IT SUITS YOU" sarlavhasi ostida "much
gentler than you usually prefer" jumlasi turdi — ikkisi ham qoidaga ko'ra rost, chunki
foydalanuvchi `violence` da o'rtachadan 2.3 ball narida (yo'nalish 0.08 σ), film esa
undan 16.7 ball narida (0.61 σ): eski qoida buni "mos" deb atardi. Natijada 500 filmdan
**495 tasi** sabab tomonida edi va haqiqiy tafovutlar (Up: `humor` 1.12 σ) jim qolardi.
Yangi qoidada uchta akkauntda sabab **44.8 / 50.6 / 66.2%**, farq **55.2 / 49.4 / 33.8%**,
jim **0%**. To'liq o'lchov, rad etilgan variantlar va kesimlarning tanlanishi:
`docs/decisions/0008-closeness-reasons.md`.

Har bir trait qo'lda tekshiriladi: ikki sonni ayirib σ ga bo'lish.

Interfeys: `named_traits` (trait kalitlari) va `trait_side` (`reason` | `difference` |
`null`); `trait_side` aynan `named_traits` bo'sh bo'lmaganda to'ldiriladi.

### FR-6 · "Nega sizga yoqadi"

**TZ 1.38:** web launch'da (F9a) yangi izoh yozilmaydi: `explanations` keshida bo'lsa o'sha, bo'lmasa `named_traits` dan shablon jumla. Gemini pul topilganda qaytadi.

Har tavsiyaga 1–2 jumlalik oddiy tildagi izoh.

**Qabul mezoni:**
- Izoh faqat haqiqiy trait mosligiga asoslanadi, umumiy maqtov emas.
- **Izoh trait qoidasining tomonini kuzatadi** (1.23): sabab tomonda — "nega mos" matni;
  farq tomonda — **boshqa prompt** (`DIFFERENCE_SYSTEM_PROMPT`), u farqni betaraf
  bayon qiladi va modelga "sizga yoqadi / tavsiya qilaman / sinab ko'ring" ma'nosidagi
  hech narsa yozmaslik aytiladi. Hech narsa nomlanmasa — izoh so'ralmaydi.
- **Farq jumlasi taqqoslash bo'lishi shart** (1.26): har jumlada ikki yarim bo'lishi kerak
  — foydalanuvchi odatda nimani tanlashi **va** film shunga qarshi qayerda turishi. Faqat
  filmni ta'riflagan jumla mezonni bajarmaydi (jonli misol, 2026-10-16: Casablanca uchun
  "keeps things surprisingly straightforward and wraps up neatly" — foydalanuvchi umuman
  eslanmagan; Godzilla uchun "deeper into dark and heavy dread than you usually look for" —
  to'g'ri). Farqni baholovchi so'zlar ("surprisingly", "refreshingly", "oddly") taqiqlanadi:
  farq yaxshi ham, yomon ham emas.
- Har (foydalanuvchi, film) juftligi uchun bir marta generatsiya qilinadi va keshlanadi.
- Kesh bo'lmasa ham ekran bloklanmaydi — skeleton ko'rsatiladi.

### FR-7 · Movie DNA

Foydalanuvchi o'z ta'm profilini 14 o'lchovda va bitta jumlalik xulosada ko'radi.

**Qabul mezoni:**
- 10 tadan kam baho bo'lsa — "yana N ta baholang" ekrani.
- Profil har yangi bahodan keyin yangilanadi.
- Ulashish uchun server tomonda rasm generatsiya qilinadi.

### FR-8 · AI Assistant

**TZ 1.38:** web launch'da (F9a) assistant yashiriladi — Gemini pullik tarifiga pul yo'q. Pul topilganda assistant qaytadi va pastdagi qabul mezoni (TZ 1.32/1.33) o'shanda, pullik tarifda o'lchanadi.

Tabiiy tildagi so'rov strukturali qidiruvga aylantiriladi.

**Qabul mezoni:**
- "90 daqiqam bor, miyamni portlatsin" kabi so'rov ishlaydi.
- Javob oqim bilan keladi. Birinchi belgi — mijoz tomonida, sahifa API bilan ulangan
  holda o'lchanadi — kamida 30 xabarda, kamida ikki xil kunda: **median ≤ 3 s** va
  **90-persentil ≤ 15 s**, `error` bilan tugagan xabar 0. 2 s — maqsad, mezon emas.
  25 s / 45 s chegarasi (keyingi band) o'zgarmaydi (TZ 1.32).
  **TZ 1.33:** mezon boshqa yumshatilmaydi. F4 uni bajarmasdan, ochiq yozuv bilan
  yopiladi (2026-11-13 va 11-17: 33 xabar, median 3.62 s, 1 xato). Mezon **F9a shartiga
  ko'chdi**: Gemini pullik tarifiga o'tgandan keyin kamida 30 xabar, kamida ikki xil
  kun, o'sha mezon. O'tmasa web launch bo'lmaydi.
- "Thriller", "musical" kabi janr so'ralsa, faqat shu janrdagi filmlar chiqadi (tool'ning
  `genres` argumenti, TMDB janr nomlari; bir nechta berilsa, film hammasiga ega bo'ladi).
- Birinchi belgi 25 soniyagacha kelmasa yoki javob 45 soniyada tugamasa, xabar "assistant
  band" degan aniq matn va "Qayta urinish" tugmasi bilan tugaydi; bunday xabar ham kunlik
  limitdan hisoblanadi. Uzoq kutish ko'rinmas bo'lib qolmaydi.
- Foydalanuvchiga kuniga 30 ta so'rov; limit tugaganda aniq matn ko'rsatiladi.
- Kino mavzusidan tashqari savolga javob bermaydi.
- Prompt injection urinishi tizim ko'rsatmasini o'zgartira olmaydi.

### FR-9 · Character Match (F7)

Foydalanuvchi ta'mi va ixtiyoriy quiz asosida personaj moslik natijasi.

**Qabul mezoni:**
- Quizsiz ham natija beradi (faqat ta'm asosida).
- Natijada **rasm yo'q** — faqat matn nomi va emoji.
- Disclaimer har doim ko'rinadi.
- "Bu personajga o'xshash filmlar" tugmasi tavsiyaga qaytaradi.
- Umumiy mulkdagi personajlar bazada ustunlik qiladi.

---

## 5. Nofunksional talablar

| Kategoriya | Talab | Qanday o'lchanadi |
|---|---|---|
| Tezlik (web) | LCP < 2.5s, INP < 200ms | Lighthouse, mobil, 3 o'lchov mediani; film sahifasi uchun F9a sharti (TZ 1.34) |
| Tezlik (API) | p95 < 300ms, tavsiya < 500ms | Load test |
| Tezlik (mobil) | Sovuq start < 2s | Profil rejimi |
| Ishonchlilik | 99.5% uptime | Uptime monitor |
| Xavfsizlik | Kalitlar faqat env'da, JWT tekshiruvi har so'rovda | Kod ko'rigi + test |
| Maxfiylik | Eksport va o'chirish ishlaydi | Qo'lda test |
| Qulaylik | Kontrast 4.5:1, klaviatura navigatsiyasi, 44px tegish | axe + qo'lda |
| Tillar | Ingliz — standart til va barcha kalitlarning manbasi; o'zbek — ikkilamchi; rus — qo'shimcha variant. Standart har doim ingliz (brauzer tili aniqlanmaydi); o'zbek va rus faqat til menyusidan tanlanadi, tartib: English, O'zbek, Русский. Tanlov saqlanadi va keyingi kirishda shu tilda ochiladi. Interfeys tarjima qilinadi; film ma'lumoti (nom, tavsif, trait xulosasi) TMDB'dan ingliz tilida keladi. Janr nomlari — TMDB'ning qat'iy ro'yxati (19 ta), interfeys lug'atida tarjima qilinadi (`genre.*`), yangi janr kalit olguncha inglizcha ko'rinadi | i18n kaliti qattiq kodlanmaydi; uchala lug'atda kalitlar to'plami bir xil (test, CI) |
| Xarajat | LLM har foydalanuvchiga oyiga < $0.20 | Hisoblagich |

---

## 6. API shartnomasi (asosiy)

To'liq shartnoma — `services/api/app/schemas.py` va `/docs` (OpenAPI).

| Metod | Yo'l | Vazifa | Auth |
|---|---|---|---|
| GET | `/health` | Tiriklik | yo'q |
| GET | `/movies?q=&year_from=&year_to=&max_runtime=&trait=key:min` | Qidiruv va filtrlar | yo'q |
| GET | `/movies/{id}` | Film detali; token bilan shaxsiy match, daraja va sabablar | ixtiyoriy |
| POST | `/ratings` | Baho qo'yish | ha |
| GET | `/ratings` | O'z baholari | ha |
| DELETE | `/ratings/{movie_id}` | Bahoni olib tashlash | ha |
| GET | `/watchlist` | Watchlist (har qatorda shaxsiy match va daraja) | ha |
| POST | `/watchlist` | Qo'shish | ha |
| DELETE | `/watchlist/{movie_id}` | O'chirish | ha |
| POST | `/watchlist/{movie_id}/watched` | Ko'rildi deb belgilash | ha |
| GET | `/recommendations` | Tavsiyalar | ha |
| GET | `/recommendations/{movie_id}/explanation` | "Nega sizga yoqadi" (kesh yoki yangi, kunlik limit) | ha |
| POST | `/dismissals` | "Men uchun emas" | ha |
| DELETE | `/dismissals/{movie_id}` | Rad etishni bekor qilish | ha |
| GET | `/onboarding/films?limit=&offset=` | Onboarding uchun filmlar | ha |
| GET | `/me` | Akkaunt xulosasi | ha |
| DELETE | `/me` | Akkaunt ma'lumotini o'chirish | ha |
| GET | `/me/dna` | Movie DNA: ta'm vektori, statistika | ha |
| POST | `/assistant/chat` | Assistant (SSE oqim) | ha |
| GET | `/character/match` | Character Match | ha |

Xato formati bir xil: `{"detail": "..."}`. Status kodlar standart.

---

## 7. Test strategiyasi va faza darvozasi

Bu bo'lim ishlash tartibini belgilaydi va majburiy.

### Darvoza qoidasi

Har faza oxirida shu buyruqlar ishga tushiriladi:

```bash
# API
cd services/api && ruff check . && ruff format --check . && pytest -q

# Web
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test

# Mobil (F6 dan boshlab)
cd apps/mobile && flutter analyze && flutter test
```

**Keyingi fazaga o'tish sharti — barchasi 100% muvaffaqiyatli.** Bitta test yiqilsa
ham keyingi faza boshlanmaydi. Tuzatiladi, qayta ishga tushiriladi, so'ng o'tiladi.

### Testlar zaif bo'lib qolmasligi uchun

100% o'tish o'z-o'zidan sifat kafolati emas — test yozmasang, hammasi o'tadi.
Shuning uchun har fazada qo'shimcha shartlar bor:

1. **Qamrov:** `services/api/app/services/` va `app/pipelines/` uchun kamida **80%**.
   Router qatlami uchun kamida bitta test har endpoint'ga.
2. **Har faza promptida majburiy testlar ro'yxati** bor — ular yozilmasa, faza tugamagan.
3. **Salbiy holatlar majburiy:** har endpoint uchun auth yo'q, noto'g'ri kirish,
   topilmadi holatlari testlanadi.
4. **Qo'lda qabul ro'yxati:** har fazada avtomatlashtirib bo'lmaydigan tekshiruvlar
   (ko'rinish, oqim) qo'lda bajarilib belgilanadi.

### Test turlari

| Tur | Qayerda | Nimani tekshiradi |
|---|---|---|
| Unit | `tests/unit/` | Formulalar, konvertatsiyalar, validatsiya — DB'siz |
| Integratsiya | `tests/integration/` | Endpoint + DB, test bazasida |
| Kontrakt | `tests/contract/` | API javobi web tiplari bilan mos |
| Komponent | `apps/web/src/**/*.test.tsx` | React komponent holatlari |
| Widget | `apps/mobile/test/` | Flutter widget holatlari |

---

## 8. Muvaffaqiyat mezonlari

| Qachon | Metrika | Maqsad |
|---|---|---|
| F5 (alfa) | Tavsiya qilingan film 7 kun ichida ko'rildi | ≥ 15% |
| F5 (alfa) | Onboardingni tugatganlar ulushi | ≥ 70% |
| F5 (alfa) | Testerlar, davomiylik, suhbatlar | 12 tester (Android telefon + Gmail; maqsad 15, TZ 1.35), 2 hafta, 5 ta suhbat; 2026-12-06 gacha 12 bo'lmasa — o'sha son bilan, "zaif signal" (TZ 1.37) |
| Launch | D7 retention | ≥ 25% |
| Launch | Birinchi haftada baholar soni (o'rtacha) | ≥ 10 |
| Launch | Assistant so'rovi (foydalanuvchiga) | ≥ 2 |

**F5 darvozasi (TZ 1.30; sanalar TZ 1.35):** 12 tester, 2 hafta (2026-11-29 — 2026-12-13), 5 ta suhbat.
15% va 70% mezonlari o'zgarmagan. **TZ 1.37:** alfa 2026-11-29 da kim bo'lsa, o'shalar bilan boshlanadi, taklif davom etadi. 2026-12-06 gacha 12 tester bo'lmasa, 2026-12-13 dagi qaror o'sha son bilan qilinadi va hisobotda **"zaif signal"** deb belgilanadi; mezonlar o'zgarmaydi (masalan 4 kishida 70% = kamida 3, 2.8 yuqoriga).

**Qurish to'xtamaydi, launch to'xtaydi.** Mobil ilova (F6) va web launch tayyorligi (F9a)
alfa davomida quriladi va mahsulot darvozasini kutmaydi. Ochiq launch — web (F9a) ham,
do'kon (F9b) ham — alfa natijasidan keyin. **15% metrikasi yiqilsa, tavsiya dvigateli
qayta ishlanadi va launch to'xtaydi**; dvigateldan keyin alfa qayta o'tkaziladi.

**Launch uchun ikkala mezon shart (TZ 1.31).** 70% yiqilsa — onboarding tuzatiladi va
qayta o'lchanadi, dvigatel qayta ishlanmaydi; launch onboarding mezoni o'tguncha
to'xtaydi. **15% metrikasi faqat 7 kunlik oynasi yopilgan tavsiyalar bo'yicha
hisoblanadi** (2026-12-13 dagi qarorda: 2026-12-06 gacha ko'rsatilganlar); hisobotda
nechta tavsiya kirgani aytiladi. (Oldingi
qoida — "F5 metrikasi yetmasa mobil ilovaga o'tilmaydi" — TZ 1.30 bilan almashtirildi.)

**Kim sanaladi (TZ 1.36):** `alpha_tester` belgisi kelgan **hamma** testerga qo'yiladi (15 kelsa — 15);
70% va 15% hammasi bo'yicha: 15 kishida 70% = kamida 11 (10.5 yuqoriga), 12 kishida — 9.

**12 kishi bilan bu statistik isbot emas.** 70% mezoni 12 testerdan kamida 9 tasi (8.4
yuqoriga yaxlitlanadi); 9/12 = 75% bo'lsa ham 95% ishonch oralig'i (Wilson) taxminan
47–91%, ya'ni haqiqiy ulush 70% dan past bo'lishi ham mumkin. 15% metrikasi tavsiyalar
bo'yicha sanaladi, lekin tavsiyalar 12 kishiga to'plangan: bir faol tester natijani
siljitadi, samarali hajm 12 ga yaqin. Natija yo'nalishni ko'rsatadi va suhbatlar bilan
birga o'qiladi; launch'dan keyingi raqamlar (§8, "Launch" qatorlari) uni tasdiqlashi
kerak.

---

## 9. Hujjat o'zgarishi

Bu TZ o'zgarsa, versiya raqami oshadi va o'zgarish shu bo'limda qayd etiladi.

| Versiya | Sana | O'zgarish |
|---|---|---|
| 1.0 | 2026-09-24 | Birinchi versiya |
| 1.1 | 2026-09-25 | Ma'lumot manbai qarori: TMDB bepul tarifi, litsenziya monetizatsiyadan oldin (ADR 0002) |
| 1.2 | 2026-09-25 | Katalog 20 000 dan 5 000 ga; son sozlamaga chiqarildi; o'n yillik va til taqsimoti qo'shildi |
| 1.3 | 2026-09-29 | 2-bo'limga "Backlog" kichik bo'limi; birinchi band: migrate skriptiga testlar |
| 1.4 | 2026-09-29 | §6 API jadvali F2–F3 endpointlari bilan to'ldirildi; backlog'ga F3 dan qolgan to'rt band (DNA AI xulosasi, ulashish rasmi, provayder filtri, filmga xos chiplar) |
| 1.5 | 2026-09-30 | FR-2: katalog 5 000 dan 500 ga (xarajat); `catalogue_target = 500` |
| 1.6 | 2026-10-01 | Backlog: 500 filmni kvota bilan tanlash bajarildi (`scripts/select_catalogue.py`, `docs/catalogue-500.md`); yangi band — shu skriptga testlar |
| 1.7 | 2026-10-02 | Backlog: embedding tokenlarini guruhlab sanash (5 000 film bosqichi uchun), nega namuna emas |
| 1.8 | 2026-10-02 | §5 Tillar: ingliz standart va kalitlar manbasi, o'zbek ikkilamchi, rus qo'shimcha (foydalanuvchi qarori); backlog — film ma'lumotini tarjima qilish |
| 1.9 | 2026-10-02 | Backlog: izohlar limiti tugaganini interfeys aytishi kerak (F2 qo'lda tekshiruvidan) |
| 1.34 | 2026-11-18 | F3 band 5 o'lchandi (foydalanuvchi, 2026-11-17, jonli sayt, film sahifasi The Dark Knight Rises, incognito): mobil LCP 14.5 / 4.2 / 4.6 s, median **4.6 s** (talab < 2.5 s); desktop LCP 1.4 s; INP o'lchanmagan (Timespan rejimida Rate / Watchlist tugmalari topilmadi). **F4 yopildi** ikki ochiq yozuv bilan: FR-8 birinchi belgi (TZ 1.33) va "film sahifasi mobil LCP 4.6 s, INP o'lchanmagan". Mobil LCP < 2.5 s va INP < 200 ms **F9a (web launch) shartiga ko'chdi**: jonli saytda, mobil 3 o'lchov mediani; o'tmasa web launch bo'lmaydi (foydalanuvchi qarori) |
| 1.35 | 2026-11-22 | Testerlar hali yo'q: ular **2026-11-29 gacha** yig'iladi — 12 ta Android telefon + Gmail, maqsad 15; alfa shu kundan 14 kun (2026-11-29 — 2026-12-13). Qolgan sanalar oraliqlarni o'zgartirmasdan **+6 kun**: Play yopiq testi 2026-12-08 (o'sha testerlar bilan), alfa qarori 2026-12-13 (15% oynasi: 2026-12-06 gacha ko'rsatilganlar), web launch 2026-12-15, Google Play'ga ariza 2026-12-22, do'konda 2026-12-29 dan oldin emas. Doira va mezonlar o'zgarmagan (foydalanuvchi qarori) |
| 1.36 | 2026-11-23 | `alpha_tester` belgisi kelgan hamma testerga qo'yiladi (15 kelsa — 15); 70% va 15% mezonlari belgilangan hammasi bo'yicha hisoblanadi (15 kishida 70% = kamida 11). Mezonlarning o'zi o'zgarmagan (foydalanuvchi qarori) |
| 1.37 | 2026-11-23 | Pul va testerlar (foydalanuvchi, 2026-11-23: karta bor, hozir $25 yo'q; testerlar 4 ta). **(1) Alfa 2026-11-29 da kim bo'lsa, o'shalar bilan boshlanadi**, taklif davom etadi; 2026-12-06 gacha 12 tester bo'lmasa, 2026-12-13 dagi qaror o'sha son bilan qilinadi va **"zaif signal"** deb belgilanadi; 15% va 70% o'zgarmaydi. **(2) Google Play (F9b) $25 topilguncha to'xtaydi**; Play yopiq testi — "pul va 12 tester bo'lganda", ariza undan 14 kun keyin. Play akkaunti, Play uchun imzo va yopiq test treki F6 dan F9b ga ko'chdi. **(3) F6 davom etadi**; testerlar Android ilovani APK fayl sifatida oladi (Play'siz, CI build'i), yo'riqnoma `docs/testers-android.md`; F6 qo'lda ro'yxatida "Play yopiq testidan o'rnatildi" o'rniga "tester APK'ni yo'riqnoma bo'yicha o'zi o'rnatdi". **(4) Web launch (F9a) uchun Gemini pullik tarifi ($50 hold) ham pul talab qiladi**: pulsiz variantlar `docs/STATUS.md` da, tanlov foydalanuvchida, hech biri qurilmaydi. F6 qarorlari (2026-11-23): offline va push 2026-12-08 dan keyin, `isar_community`, "film chiqdi" push'i backlog'da |
| 1.38 | 2026-11-23 | Foydalanuvchi qarorlari. **(1) Web launch (F9a) AI'siz** — TZ 1.37 dagi A varianti: assistant yashirin, film sahifasidagi izoh faqat keshdan yoki shablondan (`named_traits`), so'rovda Gemini chaqirilmaydi. Kodi F9a vaqtida yoziladi, hozir emas. Gemini pullik tarifi va FR-8 mezoni (TZ 1.32/1.33) F9a shartidan chiqdi: pul topilganda assistant qaytadi va FR-8 o'shanda, pullik tarifda o'lchanadi; mezon yumshatilmaydi. **(2) F8 va F7 F9a dan keyin boshlanadi** (do'kondan keyin emas, TZ 1.31 o'rniga). **(3)** F6 qo'lda ro'yxati: tester APK'ni yo'riqnoma bo'yicha o'zi o'rnatadi (TZ 1.37 dagi o'zgarish tasdiqlandi). Release APK bitta doimiy kalit bilan imzolanadi (kalit repo'dan tashqarida, CI'da GitHub secret) |
| 1.33 | 2026-11-17 | FR-8 birinchi belgi mezoni (TZ 1.32) **boshqa yumshatilmaydi** (foydalanuvchi qarori). F4 shu mezon bajarilmagan holda, ochiq yozuv bilan yopiladi: "FR-8 birinchi belgi mezoni bajarilmagan (33 xabar, median 3.62 s, 1 xato)". Mezon **F9a (web launch) shartiga ko'chdi**: Gemini pullik tarifiga o'tgandan keyin kamida 30 xabar, kamida ikki xil kun, o'sha mezon (median ≤ 3 s, 90-persentil ≤ 15 s, `error` 0); o'tmasa web launch bo'lmaydi. Render log'i (2026-11-17): yagona xato — Gemini'ning ikki marta ketma-ket 503 "high demand" javobi, kod mo'ljallanganidek bitta qayta urinishdan keyin to'xtadi; sekin xabarlarda vaqt birinchi model chaqiruvida ketgan (6.6–11.6 s), bizning bosqichlarda emas |
| 1.32 | 2026-11-17 | FR-8: "birinchi belgi 2 soniya ichida" mezoni o'zgardi (foydalanuvchi qarori, phase-4-status'dagi (a) varianti): mijoz tomonida, ulangan sahifada, **kamida 30 xabar, kamida ikki xil kun; median ≤ 3 s, 90-persentil ≤ 15 s, `error` 0**; 2 s — maqsad. Sabab: Gemini Flash-Lite'ning tezligi soatdan soatga o'zgaradi (bir kod bilan bir kunda 1.78 s va 2.95 s), 10 xabarlik median qaror bera olmaydi; 2026-11-13 dagi yakuniy o'lchovda median 2.95 s edi. **Sanalar 4 kunga surildi** (13–17-noyabr ish bo'lmadi): F4 yopish 2026-11-19, F5 alfa kodi 11-22, testerlar 11-23, Play yopiq testi 12-02, alfa qarori 12-07 (15% oynasi: 11-30 gacha ko'rsatilganlar), web launch 12-09, Play'ga ariza 12-16, do'konda 12-23 dan oldin emas; oraliqlar o'zgarmagan; iOS — yanvar, o'zgarmagan (§2, §8) |
| 1.31 | 2026-11-13 | TZ 1.30 dagi ziddiyatlar bo'yicha qarorlar (foydalanuvchi): **do'konga ariza (F9b) F7 va F8 ni kutmaydi** — sharti F6 gate'i, F9a va Play yopiq testi; F8 va F7 do'kondan keyin yangilanish. Do'konda ko'rinish **2026-12-19 dan oldin emas**. **iOS hozir rejalanmaydi** — avval Android, iOS alohida qaror, yanvar. **Launch uchun 15% ham, 70% ham shart**; 70% yiqilsa onboarding tuzatiladi va qayta o'lchanadi, dvigatel qayta ishlanmaydi. **15% faqat 7 kunlik oynasi yopilgan tavsiyalar bo'yicha**, hisobotda tavsiyalar soni. Backlog: testerlardan oldin faqat NSFW va izohlar limiti xabari; recency sifat chegarasi va onboarding chiplari alfadan keyin; qolganlari F5 dan keyin (§2) |
| 1.30 | 2026-11-13 | **Roadmap tezlashtirildi** (foydalanuvchi qarori). Doira o'zgarmadi. Tartib: F4 yopish → F5 alfa kodi → mobil (Android birinchi, alfa paytida) → web launch tayyorligi (F9a) → Smart Watchlist + Group Match (F8) → Character Match (F7, yurist ko'rigigacha flag ortida) → do'konlar (F9b); F9 ikkiga bo'lindi. Maqsad sanalar: F4 15-noyabr, alfa kodi 18-noyabr, testerlar 19-noyabr, Android yopiq testi 28-noyabr, alfa qarori 3-dekabr, web launch 5-dekabr, do'konlarga ariza 12-dekabr (§2). "F5 darvozasi o'tmaguncha F6 boshlanmaydi" qoidasi o'zgardi: qurish alfa paytida ketadi, ochiq launch alfa natijasidan keyin; 15% yiqilsa dvigatel qayta ishlanadi va launch to'xtaydi. F5 darvozasi: 12 tester (Android), 2 hafta, 5 suhbat (30–50 tester va 10 suhbat o'rniga); 15% va 70% o'zgarmadi; 12 kishi statistik isbot emasligi yozildi (§8) |
| 1.29 | 2026-11-13 | FR-8: **janr filtri** — `search_movies` ga `genres` argumenti (TMDB'ning 19 janr nomi, ko'pi bilan ikkitasi, film hammasiga ega bo'lishi kerak); phase-04 promptidagi tool imzosi shunga o'zgardi. **Kirish gapi** — model nima izlayotganini bitta gapda (foydalanuvchi tilida, film nomisiz) `search_movies` ning majburiy `intro` argumentida yozadi; server uni qidiruvdan oldin ko'rsatadi, shuning uchun birinchi belgi qidiruv va ikkinchi chaqiruvni kutmaydi. `intro` qidiruv argumenti emas; bo'sh yoki 160 belgidan uzun bo'lsa ko'rsatilmaydi, oxirida tinish belgisi bo'lmasa nuqta qo'shiladi. Aniqlashtirildi 2026-11-13 (foydalanuvchi tasdig'i): dastlabki variant — matn chaqiruvdan oldin — ishlamadi, Gemini Flash-Lite (MINIMAL thinking) 6 tashxis chaqiruvining hammasida chaqiruvdan oldin matn yozmadi (ADR 0009 qo'shimchasi). **Joylashtirilmagan kartochkalar ko'rsatilmaydi** — faqat javob o'zi qo'ygan filmlar. Sabab: qo'lda tekshiruvlarda "musical" ga Ratatouille, thriller so'roviga Bambi chiqdi, model esa mavjud bo'lmagan `comedy` traitini yubordi; javobdan keyin qo'shilgan kartochkalar so'rovga mos emasdi (The Lion King "blow my mind" ga) (foydalanuvchi qarori, 2026-11-12) |
| 1.28 | 2026-11-13 | FR-8: **xabar uchun vaqt chegarasi** — birinchi belgi 25 s, butun javob 45 s; o'tsa "assistant band" matni va "Qayta urinish" tugmasi (uch tilda). Sabab: 2026-11-12 da Gemini sekin edi (birinchi chaqiruv 6–19 s, birinchi belgi 15–39 s), har chaqiruvga 30 s va to'rttagacha chaqiruv bilan foydalanuvchi ~2 daqiqa kutishi mumkin edi; bitta xabar 52 s da xato bilan tugadi. Oqim boshlanib, 10 s jim qolsa — 503 kabi bir marta qayta uriniladi. "2 soniya" mezoni o'zgarmadi va hali bajarilmagan (foydalanuvchi qarori; ADR 0009 qo'shimchasi 2026-11-13) |
| 1.27 | 2026-10-22 | FR-5: **"sabab" yaqinlikni bildiradi, yo'nalishni emas** — 1.23 ning kesimlari o'rniga: sabab = kattalik ≤ 0.35 σ **va** yo'nalish ≥ 0.40 σ (yo'nalish endi ma'no emas, qo'riqchi), farq = kattalik ≥ 1.0 σ, orasi — jim; sabablar eng kichik kattalik bo'yicha saralanadi. Sabablar ustunligi, `named_traits` + `trait_side` shartnomasi va match formulasi o'zgarmadi. FR-6: **sabab prompti qayta yozildi** — har jumla moslikni aytadi, taqqoslash shakllari ("more than you", "gentler than") taqiqlandi; farq prompti o'zgarmadi; eski sabab izohlari keshdan o'chirildi. Sabab: jonli saytda "WHY IT SUITS YOU" ostida "much gentler than you usually prefer" turdi — ikkisi ham eski qoidaga ko'ra rost edi, ya'ni ziddiyat qoidaning o'zida (foydalanuvchi o'rtachadan 2.3 ball narida, film undan 16.7 ball narida = "mos"). O'lchov: 500 filmdan 495 tasi sabab tomonida edi → endi 44.8 / 50.6 / 66.2% (uch akkaunt), jim 0%. Takrorlanish hal bo'lmadi (eng ko'p nomlangan trait sabab filmlarining 64.3 / 51.8 / 43.5% ida) — backlog'ga. Qaror, raqamlar va rad etilgan uch variant: `docs/decisions/0008-closeness-reasons.md` |
| 1.26 | 2026-10-16 | FR-6: farq promptida **taqqoslash majburiy** — har jumlada foydalanuvchi odatda nimani tanlashi va film shunga qarshi qayerda turishi; faqat filmni ta'riflash yetmaydi, farqni baholovchi so'zlar taqiqlanadi. Sabab: jonli jumlalardan biri (Casablanca) foydalanuvchini umuman eslamagan, ya'ni farq bayoni film retsenziyasiga aylangan. "Sizga yoqadi" taqiqi o'z kuchida (foydalanuvchi qarori) |
| 1.25 | 2026-10-16 | FR-5: **panel sarlavhasi ostidagi jumlani nomlaydi**, band'ni emas — tomon `reason` da "Why it suits you", `difference` da "How it differs", band `strong` bo'lmasa va hech narsa nomlanmasa neytral "You and this film". Qizil "STRONG MATCH" `strong` da qoladi, **faqat tomon `difference` bo'lsa bosiladi**: farq jumlasi band bilan ziddiyat hosil qiladi (1.23/1.24 dagi ziddiyat qaytib kelardi), jimlik esa ziddiyat emas — jumla yo'q, band rost, va hech narsa nomlanmagan film 14 traitda ta'mga eng yaqin turgani uchun eng mos filmlardan biri. Uch tilda matn foydalanuvchi tomonidan tanlangan. Sabab: band va tomon boshqa o'lchovlar, shuning uchun band'li sarlavha jumla maqtovmi yoki farq bayonimi — aytmasdi (foydalanuvchi qarori, qizil qoidasi 2026-10-16 da aniqlashtirildi; matnlar va holatlar jadvali `docs/ui.md`, "Kicker qoidasi") |
| 1.24 | 2026-10-15 | Interfeys: `outside_usual` bo'limining nomi "Outside your usual taste" → "Something different" / "Boshqacha kinolar" / "Другое кино" (foydalanuvchi qarori). Eski nom ta'm haqida da'vo qilardi, bo'lim esa embedding masofasi bo'yicha tuziladi, shuning uchun bitta filmda "ta'mingizdan tashqari" va "good" darajasi birga chiqardi |
| 1.23 | 2026-10-15 | FR-5: sabab qoidasi o'rniga **bitta simmetrik trait qoidasi** — bitta og'ish o'lchovi, bitta yo'nalish tekshiruvi, ikki kesim (sabab 0.5 σ, farq 1.0 σ); sabablar ustun, ikkalasi bo'lmasa panel jim. FR-6: farq tomonida alohida prompt, "sizga yoqadi" ma'nosi taqiqlanadi. API: `reasons` → `named_traits` + `trait_side`. Sabab: foydalanuvchi "Outside your usual taste" yorlig'i ostidagi filmda "sizga mos" izohini ko'rdi; eski qoida og'ish kattaligini o'lchamasdi (82 va 85 ham "sabab" edi). Interfeysdan "ta'mingizga umuman mos" jumlasi olib tashlandi (foydalanuvchi qarori; o'lchov `docs/phase-2-status.md`) |
| 1.22 | 2026-10-13 | FR-6: `ExplanationOut` ga **`reason`** qo'shildi (jumla yo'qligining sababi, yetti qiymat) — oldin `text: null` yetti holatda bir xil edi. Interfeys "Izoh tayyorlanmoqda…" ni faqat jumla kelishi mumkin bo'lganda ko'rsatadi (tester fikri: indikator har film sahifasida chiqib, shablon jumla bilan tugardi) |
| 1.21 | 2026-10-13 | FR-5: bo'lim ichida **recency jarimasi** (`recency_weight` = 0.02) — faqat MMR relevantligida, match foiziga tegmaydi. Asos: MMR pre-1980 ulushini 32% dan 40% ga ko'tarardi (katalog 26%); 0.02 da 30% (foydalanuvchi qarori, o'lchov `docs/phase-2-status.md`) |
| 1.20 | 2026-10-13 | Tester fikri (P0–P2). Backlog'ga uch band: tavsiyalarning eski tomonga og'ishi (o'lchandi, qaror kutilmoqda), baho chiplari, NSFW/ekstremal kontent. FR-5 sabab qoidasi (1.12) **o'zgarmadi**; o'zgargan narsa — zaxira jumlasining matni: "Siz bilan umumiy jihatlari" yaqinlikni da'vo qilardi, qoida esa yaqinlikni talab qilmaydi (film katalog o'rtachasidan yuqori + ta'm shu tomonda). Misol: The Wave `plot_twist` — katalog o'rtachasi 30.9, σ 20.4, film 60 (z +1.43), foydalanuvchi 34 (z +0.15): ikkala shart ham bajariladi, lekin 26 ball farq "umumiy" emas. FR-3 (8.0 chegarasi) o'zgarmadi; backlog'ga ikki band — baho chiplari va NSFW/ekstremal kontent | 
| 1.19 | 2026-10-12 | Backlog: "qayerdan ko'rish mumkin" hozir qurilmaydi — TMDB/JustWatch UZ ni qo'llamaydi (100 filmlik o'lchov), uchta variant (foydalanuvchi qarori) |
| 1.18 | 2026-10-10 | FR-3: jonli saytda bajarildi, alohida vaqt o'lchovisiz (foydalanuvchi qarori); backlog'dan CORS `Access-Control-Max-Age` bandi olindi — 7200 qilindi |
| 1.17 | 2026-10-09 | §5 Tillar: janr nomlari interfeys lug'atida tarjima qilinadi; backlog — film nomi va tavsifining ruscha tarjimasiga foydalanuvchi so'rovi (TMDB `ru-RU`) yozildi |
| 1.16 | 2026-10-06 | FR-5: interfeysda daraja ikki holatda — "Strong match" (qizil) va neytral "You and this film"; "good" hisoblanadi va API'da qoladi, lekin ko'rsatilmaydi. Asos: Home'dagi film sahifalarining 68% ida chiqardi (0.15), ajratmaydi (foydalanuvchi qarori) |
| 1.15 | 2026-10-06 | Backlog: dizayn 4-bosqichi (Movie DNA) faqat radial diagrammaga qisqardi; Wrapped tuzilmasi va brauzerdagi ulashish rasmi backlog'ga (foydalanuvchi qarori) |
| 1.14 | 2026-10-05 | FR-5: "yaxshi" darajasi eng yaqin 35% dan 15% ga (`match_good_share` 0.15): 35% da 500 dan 175 film, har uchinchi film sahifasi — yorliq ma'nosini yo'qotardi (foydalanuvchi qarori). O'lchov: `docs/STATUS.md`. Film sahifasida daraja — panel sarlavhasi |
| 1.13 | 2026-10-05 | FR-5: interfeys match foizini emas, match darajasini ko'rsatadi (kuchli — eng yaqin N=5 film, qizil; yaxshi — eng yaqin 35%, neytral); foiz API'da ichki qoladi; "60% dan past" o'rniga eng uzoq 25% tavsiya qilinmaydi. Asos: foiz 8+ va ≤ 5 baholarni ajratmadi (AUC 0.52). Backlog — ta'm yoqmagan filmlardan ham o'rgansin |
| 1.12 | 2026-10-02 | FR-5: sabab traitlari katalogga nisbatan tanlanadi (formula yuqorida), ro'yxat bo'sh bo'lishi mumkin; backlog — izoh keshi kalitiga sabablar, traitlarni qayta baholash (arzon, jarayon qimmat) |
| 1.11 | 2026-10-02 | Backlog FR-7: ulashish rasmi brauzerda, server varianti link preview uchun qoladi |
| 1.10 | 2026-10-02 | O'sha bandda izoh narxi taxmindan o'lchovga: $0.00013 bittasi, oyiga ≤ $0.08 (avvalgi "$0.24, maqsaddan yuqori" ogohlantirishi noto'g'ri taxminga asoslangan edi) |
