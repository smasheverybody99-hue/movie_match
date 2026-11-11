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
5. **Bitta xabar — ko'pi bilan ikki chaqiruv**: birinchisida model tool so'rashi mumkin,
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
