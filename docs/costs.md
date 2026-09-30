# Xarajatlar — Movie Match

Oxirgi tekshiruv: **2026-09-30**. Narx o'zgarsa yoki yangi provayder ko'rib chiqilsa, shu
fayl yangilanadi (CLAUDE.md qoidasi). Har narx yonida manba bor; manbasiz raqam — hisob
yoki taxmin, va u shunday deb belgilangan.

> **Provayder tanlanmagan.** LLM ishlari (trait, embedding, izoh) provayder interfeysi
> orqasida (ADR 0006); hozirgi implementatsiya — Gemini, lekin Gemini Google Cloud'ning
> $50 karta hold talabi tufayli yopiq (foydalanuvchi ma'lumoti, 2026-09-30). Shuning uchun
> quyidagi jadvallar bir nechta variantni beradi. Tanlov — alohida qaror.

## Hisob asoslari

| Kattalik | Qiymat | Qayerdan |
|---|---|---|
| Trait: kirish tokeni, film boshiga | ~410 | `traits submit --dry-run` (2026-09-26), prompt uzunligidan, 3.5 belgi/token; `docs/phase-1-status.md` |
| Trait: chiqish tokeni, film boshiga | ~250 (thinking bilan 2× gacha) | Taxmin: 14 ta son + 2 jumla JSON. 50 filmlik o'lchov hali yo'q |
| Trait: **bitta film o'lchangan** (2026-09-30) | 370 kirish, 195 chiqish (thinking bilan) | *Fight Club*, Gemini 3.5 Flash-Lite, oddiy `generate_content`; bitta film — o'rtacha emas, taxmin hali almashtirilmadi |
| Embedding: token, film boshiga | ~208 | 5 000 filmning embedding matni, o'rtacha 729 belgi; `docs/phase-1-status.md` |
| Izoh: token, bitta izoh | ~200 kirish, ~60 chiqish | Taxmin: tizim prompti + 3 sabab qatori; javob 1–2 jumla. **O'lchanmagan** |
| Katalog | 500 film (`catalogue_target`) | TZ FR-2, v1.5 |

Formulasi: `narx = kirish_token × kirish_narxi + chiqish_token × chiqish_narxi`, narxlar
1 million token uchun. Har run'dan keyin haqiqiy raqam `app.cost` log qatorida chiqadi
(ADR 0006) — taxminni o'sha bilan almashtiring.

## 1. Bir martalik: trait + embedding

### Trait ekstraksiyasi (batch rejimi)

| Provayder, model | Batch narxi, $/MTok (kirish / chiqish) | 500 film | 5 000 film | Manba |
|---|---|---|---|---|
| Gemini 3.5 Flash-Lite (hozirgi kod) | 0.15 / 1.25 | **$0.19** | $1.87 | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| OpenAI gpt-5-nano | 0.025 / 0.20 | **$0.03** | $0.30 | [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing) |
| OpenAI gpt-4.1-nano | 0.05 / 0.20 | **$0.04** | $0.35 | [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing) |
| OpenAI gpt-4o-mini | 0.075 / 0.30 | **$0.05** | $0.53 | [developers.openai.com/api/docs/pricing](https://developers.openai.com/api/docs/pricing) |
| Mistral Small 4 | 0.075 / 0.30 (0.15 / 0.60 dan −50%) | **$0.05** | $0.53 | [mistral.ai/pricing/api](https://mistral.ai/pricing/api), batch −50%: [mistral.ai/pricing](https://mistral.ai/pricing) |
| Anthropic Claude Haiku 4.5 | 0.50 / 2.50 | **$0.42** | $4.15 | [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing) |

Ogohlantirishlar:
- gpt-5-nano — reasoning modeli: fikrlash tokenlari chiqish sifatida hisoblanadi, shuning
  uchun haqiqiy chiqish 250 dan bir necha barobar ko'p bo'lishi mumkin. 1-bosqichdagi
  o'lchovsiz bu raqamga ishonmang.
- Arzonlik — sifat emas. Qaysi model traitlarni to'g'ri baholashini faqat 50 film qo'lda
  ko'rib chiqilgandan keyin bilamiz (`docs/review-films.md`).
- Chiqish 2× uzun bo'lsa (thinking), Gemini 500 film ≈ $0.34.

### Trait ekstraksiyasi (sync rejimi, `TRAIT_MODE=sync`)

Bitta film — bitta oddiy so'rov (ADR 0006, 2026-09-30 qo'shimchasi). Batch hisob
ochilmaganda ishlatiladi. Pullik tarifda standart narx — batch'ning ikki barobari.
Bepul tarifda to'lov yo'q, lekin kunlik va minutlik limit bor, va Google so'rovlardan
foydalanishi mumkin.

| Provayder, model | Standart narx, $/MTok | 500 film (taxmin 410/250) | 500 film (o'lchangan 370/195 bilan) | 5 000 film | Manba |
|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite, pullik tarif | 0.30 / 2.50 | $0.37 | $0.30 | $3.74 | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| Gemini 3.5 Flash-Lite, bepul tarif | $0 | $0 | $0 | $0 (kunlik limit bir necha kunga bo'lishi mumkin) | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) |

Tezlik: standart `TRAIT_SYNC_REQUESTS_PER_MINUTE = 10` → 50 film ~5 daqiqa, 500 film
~50 daqiqa (kunlik limit to'xtatsa, keyingi run davom ettiradi).

### Embeddinglar

Ustun hozir `vector(1536)`. Boshqa o'lcham — migratsiya va hamma filmni qayta embed
qilish (ADR 0006); API bu holatda ishga tushmaydi.

| Provayder, model | $/MTok | O'lcham | Migratsiya? | 500 film | 5 000 film | Manba |
|---|---|---|---|---|---|---|
| Gemini Embedding 2 (hozirgi kod) | 0.20 standart (0.10 batch) | 128–3 072, so'ralgan: 1 536 | Yo'q | $0.02 | $0.21 | [narx](https://ai.google.dev/gemini-api/docs/pricing) |
| OpenAI text-embedding-3-small | 0.02 | 1 536 (standart) | Yo'q | $0.002 | $0.02 | [narx](https://developers.openai.com/api/docs/pricing), [o'lcham](https://developers.openai.com/api/docs/guides/embeddings) |
| OpenAI text-embedding-3-large | 0.13 | 3 072, qisqartirish mumkin → 1 536 | Yo'q (`dimensions=1536`) | $0.01 | $0.14 | [narx](https://developers.openai.com/api/docs/pricing), [o'lcham](https://developers.openai.com/api/docs/guides/embeddings) |
| Voyage voyage-4-lite | 0.02; birinchi 200M token bepul | 1 024 (256/512/2 048) | **Ha** | $0 (bepul ulush) | $0 | [narx](https://docs.voyageai.com/docs/pricing), [o'lcham](https://docs.voyageai.com/docs/embeddings) |
| Mistral Embed | 0.10 | 1 024 | **Ha** | $0.01 | $0.10 | [narx](https://mistral.ai/pricing/api), [o'lcham](https://docs.mistral.ai/resources/cookbooks/mistral-embeddings-embeddings) |

Xulosa: bir martalik xarajat 500 film uchun har qanday variantda **$0.50 dan kam**.
Haqiqiy bir martalik to'siq — narx emas, hisob ochish sharti (masalan, Google Cloud hold).

## 2. Takrorlanuvchi (oylik)

### Izohlar ("nega sizga yoqadi")

Keshlanadi: bir (foydalanuvchi, film, til) uchun bir marta. Limit:
`explanation_daily_calls_per_user = 20` → foydalanuvchiga oyiga ko'pi bilan ~600 ta.

| Model (standart narx, $/MTok) | Bitta izoh (taxmin) | Eng og'ir foydalanuvchi, oyiga (600 ta) | Manba |
|---|---|---|---|
| Gemini 3.5 Flash-Lite (0.30 / 2.50) | $0.00021 | $0.13 | [narx](https://ai.google.dev/gemini-api/docs/pricing) |
| gpt-5-nano (0.05 / 0.40) | $0.00003 | $0.02 | [narx](https://developers.openai.com/api/docs/pricing) |
| gpt-4o-mini (0.15 / 0.60) | $0.00007 | $0.04 | [narx](https://developers.openai.com/api/docs/pricing) |
| Claude Haiku 4.5 (1 / 5) | $0.00050 | **$0.30** — TZ'dagi $0.20 dan oshadi | [narx](https://platform.claude.com/docs/en/about-claude/pricing) |

TZ §5: LLM xarajati foydalanuvchiga oyiga < $0.20. Oddiy foydalanuvchi limitga yetmaydi.

### Assistant (4-faza)

Model qaror qilingan: Claude Sonnet 5, $2 / $10 per MTok
([manba](https://platform.claude.com/docs/en/about-claude/pricing)). Limit: kuniga 30 so'rov.

| Faraz (taxmin, o'lchanmagan) | Bitta so'rov | Oyiga 20 so'rov | Oyiga 900 so'rov (limit) |
|---|---|---|---|
| ~3 000 kirish (tool ta'riflari, tarix) + ~400 chiqish token | ~$0.010 | ~$0.20 | ~$9 |

**Ochiq masala:** assistant TZ'dagi "< $0.20/oy" byudjetini yolg'iz o'zi tugatadi. 4-faza
boshlanishidan oldin: yoki limitni pasaytirish, yoki prompt keshlash (kesh o'qish 0.1×
narx, [manba](https://platform.claude.com/docs/en/about-claude/pricing)), yoki byudjetni
qayta ko'rish. Bu — foydalanuvchi qarori.

### Baza

| Variant | Narx | Nima kiradi | Manba |
|---|---|---|---|
| Supabase Free | $0 | 500 MB baza, 5 GB egress, 50 000 MAU, 2 ta faol loyiha; **1 hafta faolsizlikdan keyin pauza** | [supabase.com/pricing](https://supabase.com/pricing) |
| Supabase Pro | $25/oy | 8 GB disk, 250 GB egress, pauza yo'q, kunlik backup | [supabase.com/pricing](https://supabase.com/pricing) |

Hajm hisobi: bitta 1 536-o'lchamli embedding ≈ 6 KB (4 bayt × 1 536); 5 000 film ≈ 30 MB,
HNSW indeksi bilan taxminan ikki barobar. 500 film — bir necha MB. **500 MB Free limitiga
sig'adi.** Hozir ikkita loyiha ishlatilmoqda (asosiy + test) — Free'dagi 2 ta faol
loyiha limitining hammasi.

### Hosting

| Nima | Variant | Narx | Cheklov | Manba |
|---|---|---|---|---|
| Web (statik Vite build) | Cloudflare Pages Free | $0 | Oyiga 500 build, bir vaqtda 1 build, sayt boshiga 20 000 fayl, fayl ≤ 25 MiB | [developers.cloudflare.com/pages/platform/limits](https://developers.cloudflare.com/pages/platform/limits/) |
| API (FastAPI) | Render Free web service | $0 | Oyiga 750 soat; 15 daqiqa trafik bo'lmasa to'xtaydi, qayta turishi ~1 daqiqa | [render.com/docs/free](https://render.com/docs/free) |

Render Free'ning ~1 daqiqalik sovuq starti TZ'dagi "tavsiya < 500 ms" talabiga zid —
alfa testerlar uchun chidab bo'ladi, ochiq launch uchun emas. Pullik Render tarifi narxi
bu yerda keltirilmagan: sahifadan olinmadi ([render.com/pricing](https://render.com/pricing)).
Render'ning bepul Postgres'i 30 kundan keyin o'chadi — biz Supabase ishlatamiz.

## 3. TMDB tijorat litsenziyasi

- Bepul API faqat notijorat foydalanish uchun. Daromad olish (obuna, reklama, pullik
  tarif) — faqat TMDB bilan alohida yozma kelishuv bilan
  ([TMDB API Terms of Use](https://www.themoviedb.org/api-terms-of-use)).
- **Narx ochiq emas:** shartlarda faqat "may be subject to, among other things, payment
  of fees" deyilgan. Summa `sales@themoviedb.org` orqali kelishiladi (`docs/legal.md`).
- Kerak bo'ladigan payt: **monetizatsiyadan oldin**. Alfa va bepul launch uchun emas.
- Bepul tarifda ham atributsiya shart: TMDB logosi va "not endorsed or certified by
  TMDB" jumlasi (web'da `/about` va Profil sahifasida bor, logo hali qo'shilmagan).

## 4. Umumiy manzara

| | 500 film, alfa (30–50 tester) | Izoh |
|---|---|---|
| Bir martalik (trait + embedding) | $0.03 – $0.45 | Provayderga bog'liq, yuqoridagi jadvallar |
| Oylik: LLM izohlar | < $1 | Hamma tester har kuni limitga yetsa ham, Haiku'dan tashqari |
| Oylik: assistant | ~$0.20 × faol tester | 4-fazadan; faraz o'lchanmagan |
| Oylik: baza + hosting | $0 | Free tariflar; cheklovlari yuqorida |
| TMDB | $0 | Monetizatsiyagacha |

## O'zgarishlar

| Sana | Nima o'zgardi |
|---|---|
| 2026-09-30 | Birinchi versiya. Provayder tanlanmagan; katalog 500 |
| 2026-09-30 | Trait sync rejimi narxi (standart $0.30/$2.50 va bepul tarif); bitta filmning o'lchangan tokenlari |
