# ADR 0009 — Assistant ham provayder interfeysi orqali, hozir Gemini Flash-Lite

- **Holat:** qabul qilindi (2026-11-11)
- **Qaror:** foydalanuvchi (2026-11-11, 4-faza boshida)
- **O'rnini bosadi:** CLAUDE.md "Stack decisions" dagi "Claude Sonnet 5 only for the
  conversational assistant" qatori; ADR 0004 dagi assistant bandi; `docs/costs.md` dagi
  "Model qaror qilingan: Claude Sonnet 5".
- **Kod:** `app/providers/base.py` (`Assistant` protokoli), `app/providers/gemini.py`
  (`GeminiAssistant`), `app/services/assistant.py`, `app/routers/assistant.py`.

## Muammo

Assistant (FR-8) uchun Claude Sonnet 5 rejalashtirilgan edi ($2 / $10 per MTok). Uning
hisobi (`docs/costs.md`, 2026-10-02, taxmin) bitta so'rovga ~$0.010, oyiga 20 so'rovga
~$0.20 berardi. Bu TZ §5 dagi foydalanuvchiga oyiga < $0.20 byudjetini assistant yolg'iz
o'zi tugatadi degani. Ustiga, bu loyihada vendor SDK faqat `app/providers/` ichida bo'ladi
(ADR 0006), Anthropic SDK esa umuman o'rnatilmagan: alohida yo'l qo'shilsa, ikkinchi
provayder, ikkinchi kalit va ikkinchi narx jadvali paydo bo'ladi.

## Qaror

1. **Assistant ham `LLM_PROVIDER` orqali ishlaydi**, xuddi trait, embedding va izohlar
   kabi. Interfeysga to'rtinchi protokol qo'shildi: `Assistant.stream(system, messages,
   tools, allow_tools)` matn bo'laklarini (`TextDelta`), tool chaqiruvini (`ToolRequested`)
   va oxirida `StreamEnd` (usage, qanday tugagani) qaytaradi. Xatolar boshqa ishchilarnikidek
   neytral: `RateLimited`, `TransientError`, `ProviderUnavailable`.
2. **Hozirgi implementatsiya — Gemini 3.5 Flash-Lite** (`gemini-3.5-flash-lite`,
   `generate_content_stream`, function calling). Izohlar bilan bir xil model va bir xil kalit.
3. **Vendor SDK `app/providers/` dan tashqarida import qilinmaydi.** Servis mahsulot
   tilida ishlaydi: `ChatMessage`, `ToolSpec`, `ToolCall`.
4. **Gemini 3 ning thought signature'i.** Tool chaqiruvi bo'lagida model imzo qaytaradi va
   keyingi so'rovda uni o'zgartirmasdan qaytarish kerak. `ToolCall.raw` — provayderning o'z
   yozuvi, servis uchun shaffof emas, Gemini uni so'zma-so'z qaytarib yuboradi. Boshqa
   provayder `raw` ni `None` qoldirishi mumkin.
5. **Bitta xabar — ko'pi bilan ikki chaqiruv** (qo'shimcha 2026-11-12: 503 yoki qisqa
   kutishli 429 da har biri bir marta qayta uriniladi, eng yomoni to'rt; 2026-11-13: to'xtab
   qolgan oqim ham, va butun xabarga 25 s / 45 s chegara; pastda): birinchisida model tool so'rashi mumkin,
   ikkinchisi tool natijasidan keyingi javob, unda tool taqiqlangan (`mode: NONE`).
6. **Kunlik limit o'zgarmaydi:** `assistant_daily_calls_per_user = 30`, UTC kun (foydalanuvchi
   qarori, TZ o'zgarmaydi). Off-topic xabar ham hisoblanadi, chunki u ham chaqiruv.

## Prompt keshlash — ochiq aytilishi kerak bo'lgan cheklov

Faza prompti "prompt caching on the system prompt" deydi. Qilingani:

- System prompt **qat'iy blok** (`INSTRUCTIONS`) bilan boshlanadi: u har foydalanuvchi va
  har chaqiruvda bayt-ma-bayt bir xil. Foydalanuvchi ta'mi va til undan keyin keladi. Shu
  tartibni test tekshiradi (`test_the_system_prompt_starts_with_the_fixed_block...`).
- Gemini'da implicit caching 2.5 va undan yangi modellarda avtomatik yoqiq. Kesh urilgan
  tokenlar `cached_content_token_count` da keladi, `Usage.cached_input_tokens` ga yoziladi
  va $0.03 / MTok da hisoblanadi (oddiy kirish $0.30). Cost qatorida `cached_tokens=N`
  ko'rinadi.

**Cheklov:** caching sahifasidagi minimal token jadvalida Flash-Lite modellari yo'q. Ro'yxatdagi
3.x Flash modellari uchun minimum **4 096** token
([aistudio.google.com/docs/caching](https://aistudio.google.com/docs/caching), o'qildi
2026-11-11). Bizning prefiks (system prompt ~3 700 belgi + tool sxemasi ~2 700 belgi) taxminan
1 600 token. Demak **kesh amalda urilmasligi mumkin.** Explicit cache (`caches.create`)
saqlash uchun soatiga $1.00 / MTok oladi va uning ham minimumi bor, shuning uchun hozir
qo'llanmaydi. Haqiqiy urilish ulushi qo'lda tekshiruvdagi 20 suhbatda `cached_tokens`
bo'yicha o'lchanadi. Narx hisobi keshsiz qilingan (pastda), shuning uchun kesh urilsa,
narx faqat kamayadi.

## Narx (taxmin, o'lchanmagan)

Bitta xabar: birinchi chaqiruv ~1 900 kirish token (prefiks, 4 oldingi navbat, xabar) va
~50 chiqish token. Ikkinchi chaqiruv ~2 500 kirish (tool natijasi bilan, 6 film) va ~150
chiqish. Jami ~4 400 kirish va ~200 chiqish: 4 400 × $0.30 + 200 × $2.50 per MTok ≈
**$0.0018** bir xabarga. Oyiga 20 xabar ≈ $0.04, limitda (900) ≈ $1.6. Manba va tafsilot:
`docs/costs.md`. Qo'lda tekshiruvdagi 20 suhbat bu taxminni o'lchov bilan almashtiradi.

## Oqibatlar

- `ANTHROPIC_API_KEY` sozlamasi qoladi (eski `.env` yuklanishi uchun), lekin ishlatilmaydi.
- Provayder almashsa (ADR 0006), assistant ham u bilan birga almashadi: yangi modulga
  `assistant()` qo'shiladi.
- Bepul tarifda Google yuborilgan matndan o'qitish uchun foydalanishi mumkin (ADR 0006).
  Assistant'da bu foydalanuvchi yozgan matn bo'ladi. Haqiqiy foydalanuvchilardan oldin
  pullik tarif masalasi alohida hal qilinadi.

## Qo'shimcha, 2026-11-12: o'lchov va qayta urinish

- **Narx o'lchandi** (qo'lda tekshiruv, 2026-11-11, 72 xabar, Render log'i): oddiy xabar
  $0.00164 (taxmin $0.0018 edi), oyiga 20 xabar $0.033. Tafsilot `docs/costs.md` da.
- **Kesh urilmadi:** 72 qatorning birortasida `cached_tokens` yo'q. Yuqoridagi cheklov
  tasdiqlandi. Narx keshsiz hisoblangan edi, shuning uchun u o'zgarmaydi.
- **503 UNAVAILABLE** ("high demand") 72 xabardan 5 tasini oqim o'rtasida uzdi, hammasi
  ikkinchi chaqiruvda. Endi chaqiruv bir marta qayta uriniladi (1 s kutib; 429 faqat
  provayder ≤ 2 s kutishni so'rasa). Matn chiqib ulgurgan bo'lsa, mijozga `reset` hodisasi
  boradi va qayta urinish uning o'rnida chiqadi. Follow-up'lar kelib bo'lgandan keyingi
  uzilish qayta urinilmaydi: javob to'liq. Shu bilan 5-banddagi "ikki chaqiruv" xatoda
  to'rttagacha boradi. Kunlik limit xabarni sanaydi, chaqiruvni emas; o'zgarmadi.

## Qo'shimcha, 2026-11-13: xabar uchun vaqt chegarasi

- **Nima bo'ldi** (jonli o'lchov 2026-11-12, 10 xabar, Render log'idagi `assistant timing`
  qatorlari, 9 tasi log'da): birinchi chaqiruv median 9.0 s (5.9–19.1), ikkinchisi 16.3 s
  (6.1–40.2), birinchi belgi 17.7 s (14.7–39.1), jami 33.3 s. Bizning kod (`prepare` +
  `search`) 0.1 s. 503 lar: uchta, ikki xabarda, hammasi ikkinchi chaqiruvda; biri qayta
  urinishda tiklandi, ikkinchisi ikki marta 503 olib 51.7 s da yiqildi. Yana bir javob
  birinchi so'zlaridan keyin to'xtab qoldi va eski 30 s chaqiruv chegarasida
  `TimeoutError` bilan tugadi. Ya'ni eng yomoni ~2 daqiqa kutish, oxirida umumiy xato.
- **Qaror** (foydalanuvchi, 2026-11-12, "B varianti"): xabarning o'ziga chegara.
  `FIRST_TEXT_SECONDS = 25` — birinchi belgi shu vaqtgacha; `TOTAL_SECONDS = 45` — butun
  javob. O'tsa, `error {reason: "timeout"}` va mijoz "assistant band" matnini "Qayta
  urinish" tugmasi bilan ko'rsatadi. Har chaqiruvdagi 30 s chegara olib tashlandi.
- **Timeout ham qayta urinishga kiradi:** oqim boshlangandan keyin `STALL_SECONDS = 10`
  davomida hech narsa kelmasa, u 503 kabi bir marta qayta uriniladi (`reset` bilan).
  Birinchi hodisagacha bu qoida yo'q: faqat tool so'raydigan chaqiruv oxirigacha hech narsa
  yubormaydi va 2026-11-12 da 19 s gacha olib, muvaffaqiyatli tugagan. Qayta urinish
  chegaraga kamida `MIN_TRY_SECONDS = 5` qolganda qilinadi, aks holda xabar "timeout".
  Follow-up'lar kelib bo'lgan bo'lsa, chegara javobni buzmaydi (avvalgi qoida).
- **Kesilgan chaqiruv ham pul:** provayder unga token sonini aytmaydi, shuning uchun u
  belgilardan hisoblanadi (3.5 belgi = 1 token, ko'proq sanaydi) va xarajat qatorida
  `tokens=estimated` bo'ladi. 2026-11-12 dagi kesilgan javobning tokenlari umuman
  yozilmagan edi (`requests=1`, aslida ikki chaqiruv).
- **Rad etildi:** har urinishga "birinchi bo'lak 8 s ichida" qoidasi (rejada taklif
  qilingan edi): 2026-11-12 da birinchi chaqiruvlarning 6/9 tasi 8 s dan uzoq davom etib
  muvaffaqiyatli tugagan, qoida ularni behuda qayta yuborardi.
- **Narxi:** chaqiruvlar soni o'zgarmadi (eng yomoni to'rt), narx ham. Chegara faqat
  kutishni qisqartiradi. O'lchovdagi 10 xabarda B varianti 4 tasini kesgan bo'lardi,
  shulardan 3 tasi 35–47 s da muvaffaqiyatli tugagan edi: bu foydalanuvchi tanlagan narx.
  11-11 dagi 72 xabarning birortasi kesilmasdi (eng uzuni 16.3 s).
- **Zaxira model (1e) qilinmadi** (foydalanuvchi qarori): 503 xabarlarning 2/9 qismida,
  sekinlik esa hammasida. Zaxira model sekinlikka yordam bermaydi, 503 esa ikkinchi
  chaqiruvda keladi, va thought signature boshqa modelga o'tmagani uchun almashtirish
  butun xabarni qaytadan yuborishni talab qiladi.

## Qo'shimcha, 2026-11-13: janr argumenti va kirish gapi

- **Tool imzosi o'zgardi:** `search_movies(traits, year_min, year_max, runtime_max, mood,
  genres, exclude_ids)` (TZ 1.29, phase-04 prompti). `genres` — TMDB'ning 19 janr nomi,
  kodda qat'iy ro'yxat (`GENRES`), bazadan o'qilmaydi: tool sxemasi prefiksning bir
  qismi va har chaqiruvda bir xil baytlar bo'lishi kerak. Film berilgan janrlarning
  hammasiga ega bo'ladi, shuning uchun ko'pi bilan ikkitasi.
- **Kirish gapi:** model tool'ni chaqirishdan oldin nima izlayotganini bitta gapda aytadi
  va shu javobning o'zida tool'ni chaqiradi. Birinchi belgi endi birinchi chaqiruvning
  boshida chiqadi, qidiruv va ikkinchi chaqiruvdan keyin emas. Ikkinchi chaqiruv bu
  gapni o'z qismlari bilan qaytarib oladi va uni takrorlamaydi.
- **Prefiks kattalashdi:** ko'rsatmalar 3 025 → 3 643 belgi, tool sxemasi 2 735 → 3 091
  belgi, ya'ni har chaqiruvga taxminan +280 kirish token (3.5 belgi/token). Narx
  o'lchovdan keyin `docs/costs.md` da yangilanadi.
