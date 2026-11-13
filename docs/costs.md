# Xarajatlar — Movie Match

Oxirgi tekshiruv: **2026-11-13** (assistant: `intro` bilan suhbat boshidagi xabar $0.00185 o'lchandi; Render'dagi Gemini kaliti bepul tarifda — 15 RPM, tarif qarori kutilmoqda). Narx o'zgarsa yoki yangi provayder ko'rib chiqilsa, shu
fayl yangilanadi (CLAUDE.md qoidasi). Har narx yonida manba bor; manbasiz raqam — hisob
yoki taxmin, va u shunday deb belgilangan.

> **Provayder tanlanmagan.** LLM ishlari (trait, embedding, izoh) provayder interfeysi
> orqasida (ADR 0006); hozirgi implementatsiya — Gemini, lekin Gemini Google Cloud'ning
> $50 karta hold talabi tufayli yopiq (foydalanuvchi ma'lumoti, 2026-09-30). Shuning uchun
> quyidagi jadvallar bir nechta variantni beradi. Tanlov — alohida qaror.

## Hisob asoslari

| Kattalik | Qiymat | Qayerdan |
|---|---|---|
| Trait: **kirish tokeni, film boshiga — o'lchangan** | **380** (18 976 / 50) | 50 filmlik run, 2026-10-01, Gemini 3.5 Flash-Lite, `TRAIT_MODE=sync`; `app.cost` qatori, `docs/phase-1-status.md` |
| Trait: **chiqish tokeni, film boshiga — o'lchangan** | **195** (9 746 / 50, thinking bilan) | o'sha run |
| Trait: eski taxmin (almashtirildi) | 410 kirish / 250 chiqish | `--dry-run` taxmini, 2026-09-26. Haqiqiy kirish 14% kam, chiqish 22% kam chiqdi. Boshqa provayderlar jadvallari hali shu taxminda |
| Embedding: token, film boshiga | ~208 (taxmin) | 5 000 filmning embedding matni, o'rtacha 729 belgi ÷ 3.5; `docs/phase-1-status.md` |
| Embedding: **500 film o'lchangan** (2026-10-02) | **182** token film boshiga (91 076 / 500, `count_tokens`) | Ikki run: 258 film ($0.0095, `status=interrupted`) + 242 film ($0.0087, `status=complete`) = **$0.0182** standart tarifda, bepul tarifda $0; `docs/phase-1-status.md` |
| Embedding: **258 film o'lchangan** (2026-10-01) | 184 token film boshiga (47 554 / 258, `count_tokens`) | Birinchi embedding run'i: $0.0095 standart tarifda, bepul tarifda $0; `status=interrupted` (Google serveri ulanishni uzdi), `docs/phase-1-status.md` |
| Embedding: **bitta film o'lchangan** (2026-10-01) | 187 token (`count_tokens`) | *Fight Club*, 856 belgi (4.6 belgi/token), Gemini Embedding 2, 1 536-o'lcham; $0.000037 standart tarifda, bepul tarifda $0. Belgi ÷ 3.5 taxmini bu filmda 250 berdi (34% ortiq) |
| Izoh: **token, bitta izoh — o'lchangan** | **187 kirish, 30 chiqish** (29.6) | 19 ta `run=explanation` cost qatorining o'rtachasi, 2026-10-02 (F2 qo'lda tekshiruvi, Gemini 3.5 Flash-Lite, foydalanuvchi log'i). Avvalgi taxmin 200 / 60 edi |
| Katalog | 500 film (`catalogue_target`) | TZ FR-2, v1.5 |

Formulasi: `narx = kirish_token × kirish_narxi + chiqish_token × chiqish_narxi`, narxlar
1 million token uchun. Har run'dan keyin haqiqiy raqam `app.cost` log qatorida chiqadi
(ADR 0006) — taxminni o'sha bilan almashtiring.

## 1. Bir martalik: trait + embedding

### Trait ekstraksiyasi (batch rejimi)

| Provayder, model | Batch narxi, $/MTok (kirish / chiqish) | 500 film | 5 000 film | Manba |
|---|---|---|---|---|
| Gemini 3.5 Flash-Lite (hozirgi kod) | 0.15 / 1.25 | **$0.15** (o'lchangan 380/195; taxmin bilan $0.19) | $1.50 (taxmin bilan $1.87) | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) |
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

| Provayder, model | Standart narx, $/MTok | 50 film — **haqiqiy run** (2026-10-01) | 500 film (o'lchangan 380/195) | 5 000 film | Manba |
|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite, pullik tarif | 0.30 / 2.50 | **$0.0301** (18 976 kirish, 9 746 chiqish) | $0.30 | $3.01 | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| Gemini 3.5 Flash-Lite, bepul tarif | $0 | **$0** | $0 | $0 (kunlik limit bir necha kunga bo'lishi mumkin) | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) |

**2-bosqich, haqiqiy** (2026-10-01, Gemini 3.5 Flash-Lite, sync):

| Run | So'rovlar | Kirish | Chiqish | Standart tarif | Bepul tarif |
|---|--:|--:|--:|--:|--:|
| Davomi (o'lchangan, `status=complete`) | 260 | 94 800 | 47 199 | **$0.1464** | $0 |
| Birinchi urinish (narx qatori yo'qolgan; 1-bosqich o'lchovi bilan **taxmin**) | ~199 | ~75 600 | ~38 800 | ≈ $0.12 | $0 |
| **2-bosqich jami** | | | | **≈ $0.27** | **$0** |

So'rov boshiga 365 kirish / 182 chiqish (1-bosqichda film boshiga 380 / 195):
bloklangan promptlar kirish tokeni oladi, chiqish bermaydi. 12 film Google xavfsizlik
filtri bilan bloklandi (`PROHIBITED_CONTENT`) — `docs/phase-1-status.md`.

50 filmlik run qaysi tarifda o'tgani kalitdan aniqlanmaydi: batch `FAILED_PRECONDITION`
bilan rad etilib, oddiy so'rov o'tgani bepul tarifga ishora qiladi. Bepul tarifda
50 film uchun 429 yoki kvota xatosi chiqmadi (minutiga 10 so'rov bilan).

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

Hisob o'lchangan tokenlar bilan (187 kirish / 29.6 chiqish, Gemini hisobi, 2026-10-02).
Izoh foydalanuvchi so'rovida sinxron yaratiladi, shuning uchun **standart** narx (Batch
emas). Boshqa provayderlarning tokenizatori boshqacha — ularning qatori taxmin.

| Model (standart narx, $/MTok) | Bitta izoh | Eng og'ir foydalanuvchi, oyiga (600 ta) | Manba |
|---|---|---|---|
| Gemini 3.5 Flash-Lite (0.30 / 2.50) | **$0.00013** (o'lchangan tokenlar) | **$0.08** | [narx](https://ai.google.dev/gemini-api/docs/pricing) |
| gpt-5-nano (0.05 / 0.40) | $0.00002 | $0.01 | [narx](https://developers.openai.com/api/docs/pricing) |
| gpt-4o-mini (0.15 / 0.60) | $0.00005 | $0.03 | [narx](https://developers.openai.com/api/docs/pricing) |
| Claude Haiku 4.5 (1 / 5) | $0.00034 | **$0.20** — TZ chegarasida | [narx](https://platform.claude.com/docs/en/about-claude/pricing) |

TZ §5: LLM xarajati foydalanuvchiga oyiga < $0.20. Oddiy foydalanuvchi limitga yetmaydi.

### Assistant (4-faza)

**Model: Gemini 3.5 Flash-Lite**, provayder interfeysi orqali (ADR 0009, foydalanuvchi
qarori 2026-11-11). Oldingi reja, Claude Sonnet 5 ($2 / $10), shu qaror bilan bekor
qilindi. Limit: kuniga 30 xabar (`assistant_daily_calls_per_user`, UTC kun). Bitta xabar —
ko'pi bilan ikki chaqiruv: tool so'rovi va natijadan keyingi javob. 503 (yoki qisqa kutishli
429) bo'lsa har biri bir marta qayta uriniladi, eng yomoni 4 chaqiruv (2026-11-12, `f4-fixes`).
Foydalanuvchi kutgani uchun narx **standart** (Batch emas).

| Narx, $/MTok | Kirish | Kesh urilgan kirish | Chiqish | Manba |
|---|---|---|---|---|
| Gemini 3.5 Flash-Lite, pullik tarif, standart | 0.30 | **0.03** (context caching) | 2.50 | [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) (endi aistudio.google.com/docs/pricing ga yo'naltiradi), tekshirildi 2026-11-11 |
| O'sha, bepul tarif | $0 | mavjud emas | $0 | o'sha sahifa |

Kesh: implicit caching avtomatik, lekin sahifadagi minimal hajm jadvalida Flash-Lite yo'q.
Ro'yxatdagi 3.x Flash modellari uchun minimum 4 096 token
([aistudio.google.com/docs/caching](https://aistudio.google.com/docs/caching), 2026-11-11).
Bizning prefiks ~1 600 token, shuning uchun hisob **keshsiz** qilingan. Explicit cache
saqlash uchun soatiga $1.00 / MTok oladi, hozir qo'llanmaydi (ADR 0009). **O'lchov
(2026-11-11, 72 xabar): kesh bir marta ham urilmadi** — birorta cost qatorida `cached_tokens`
yo'q (birinchi chaqiruv ~1 800 kirish token).

| O'lchangan (2026-11-11, F4 qo'lda tekshiruvi, Render log'idagi 72 ta `run=assistant` qatori, standart tarif) | Bitta xabar | Oyiga 20 xabar | Oyiga 20 suhbat (55 xabar) | Oyiga 900 xabar (limit) |
|---|---|---|---|---|
| Oddiy xabar, 2 chaqiruv (63 ta): o'rtacha 4 393 kirish + 128 chiqish | **$0.00164** (median $0.00162, eng ko'pi $0.00204) | **$0.033** | **$0.086** | $1.48 |
| Off-topic, 1 chaqiruv (4 ta): ~1 820 kirish + 5 chiqish | $0.00055 | — | — | — |
| **O'lchangan, 2026-11-12 19:33–19:34 UTC** (`556e676`: `genres` va kirish gapi, TZ 1.29; Render log'idagi 10 ta `run=assistant` qatori, hammasi 2 chaqiruv, `tokens=reported`, `status=complete`; **hammasi yangi suhbat, kontekstsiz**): o'rtacha 4 713 kirish + 169 chiqish | **$0.00184** (median $0.00186, 0.00167–0.00195; jami $0.0184) | — | — | — |
| **O'lchangan, 2026-11-13 06:17–06:18 UTC** (`f930295`: kirish gapi tool'ning `intro` argumentida; Render log'idagi 8 ta `status=complete` qatori, hammasi 2 chaqiruv, `tokens=reported`; hammasi yangi suhbat, kontekstsiz; yana 2 tasi 429 bilan birinchi chaqiruvda to'xtadi, `requests=1`, 0 token): o'rtacha 4 847 kirish + 159 chiqish | **$0.00185** (median $0.00187, 0.00162–0.00203; jami $0.0148) — 19:33 dagidan farqi +$0.00001, ya'ni `intro` narxni sezilarli o'zgartirmadi | — | — | — |
| **Suhbat ichidagi xabar, o'rtacha** (taxmin: 2026-11-11 ning kontekstli o'rtachasi 4 393 / 128 + yangi prefiks farqi +507 / +55) | ~$0.00193 | ~$0.039 | ~$0.106 | ~$1.73 |

O'lchangan qator — suhbatning birinchi xabari: o'lchov skripti har xabarni
`new_conversation: true` bilan yubordi, server esa bunda foydalanuvchining saqlangan
navbatlarini o'chiradi (`forget`). Suhbatdagi keyingi xabarlar oldingi navbatlarni (4 tagacha)
ham olib boradi, shuning uchun oylik ustunlar ikkinchi qatordan (taxmin). Prefiks farqi
o'lchandi: 2026-11-12 16:27 dagi 6 ta to'liq xabar (`84ac291`, ular ham yangi suhbat,
4 206 / 114) bilan solishtirganda +507 kirish (chaqiruvga ~250, taxmin ~280 edi), +55 chiqish
(taxmin ~15). $0.20 chegarasiga oyiga ~103 xabarda yetiladi. Namuna 10 xabar: kichik. Vaqt chegarasi (TZ 1.28) chaqiruvlar sonini o'zgartirmaydi; u kesgan chaqiruv ham
pul, uning tokenlari belgilardan hisoblanib `tokens=estimated` bilan yoziladi.

**Render'dagi kalit bepul tarifda (2026-11-13 da aniqlandi).** 06:18:08 va 06:18:09 UTC dagi ikkita 429 javobi: "Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-3.5-flash-lite, description: Generate content requests per minute limit exceeded on Free Tier", "Please retry in 51.8s". Demak yuqoridagi dollar raqamlari pullik tarif narxida hisoblangan narx, haqiqatda hisob-kitob qilinmagan. Bepul tarifda: daqiqasiga 15 so'rov (assistant xabari 2 so'rov, ya'ni **butun servis bo'yicha daqiqasiga ~7 xabar**), limit loyiha bo'yicha, kalit bo'yicha emas; kirish va chiqish "Free of charge", lekin "Used to improve our products: Yes". ADR 0004: foydalanuvchi ma'lumoti bor har qanday so'rov pullik kalitda bo'lishi kerak. Pullik tarif (Tier 1): billing hisobini ulash, odatda darhol; billing tier cap $250, 10 daqiqalik oynada $10 xarajat chegarasi. Tier 1 ning Flash-Lite uchun RPM/TPM/RPD raqamlari rasmiy sahifada yo'q, AI Studio'dagi loyiha sahifasida ko'rinadi. Manba: [aistudio.google.com/docs/rate-limits](https://aistudio.google.com/docs/rate-limits), [aistudio.google.com/docs/pricing](https://aistudio.google.com/docs/pricing), tekshirildi 2026-11-13. Tarif tanlash foydalanuvchining qarori.

72 xabar jami **$0.1086** (taxmin $0.14 edi). Bitta suhbat (o'rtacha 2.75 xabar) $0.0043.
$0.20 chegarasiga oyiga ~122 xabarda yetiladi (~4 kuniga). 5 ta xabar 503 bilan uzilgan,
ularning cost qatorida faqat birinchi chaqiruv bor edi (`requests=1`): ikkinchi chaqiruvning
uzilgan qismi hisobda yo'q, farq kichik. `f4-fixes` dan boshlab uzilgan chaqiruv ham
hisoblanadi.

Quyidagi jadval — o'lchovdan oldingi taxmin, tarix uchun qoladi.

| Faraz (taxmin, 2026-11-11, o'lchov bilan almashtirildi) | Bitta xabar | Oyiga 20 xabar | Oyiga 900 xabar (limit) |
|---|---|---|---|
| 2 chaqiruv: ~4 400 kirish (system prompt + tool sxemasi ~1 600, 4 oldingi navbat, tool natijasi 6 film) + ~200 chiqish | **~$0.0018** | **~$0.04** | ~$1.6 |
| Off-topic: 1 chaqiruv, ~1 900 kirish + ~10 chiqish | ~$0.0006 | — | — |

Token sonlari belgilardan taxmin qilingan (system prompt 3 685 belgi, tool sxemasi 2 735
belgi, ~4 belgi/token). Qo'lda tekshiruvdagi 20 suhbatning `run=assistant` cost qatorlari bu
qatorni o'lchov bilan almashtiradi. TZ §5: oyiga < $0.20. Oddiy foydalanishda (20 xabar)
taxmin chegaradan 5 baravar past. Limitgacha ishlatgan foydalanuvchi chegaradan oshadi:
limit pulni cheklaydi, byudjetni kafolatlamaydi.

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
| API (FastAPI) | Render Free web service, **Singapur** (`render.yaml`, `docs/deploy.md`) | $0 | 0.1 CPU, 512 MB; oyiga 750 soat; 15 daqiqa trafik bo'lmasa to'xtaydi, qayta turishi ~1 daqiqa; workspace trafigi oyiga 5 GB (Hobby; sana: 2026-10-08 dagi tekshiruvda 2026-08-01 dan, foydalanuvchi ma'lumotida 2026 aprel — aniqlashtirilmagan; rasmiy `free` sahifasida GB yo'q, Billing → Monthly Included Usage da ko'rinadi), karta bo'lmasa oshganda servislar oy oxirigacha to'xtaydi | [render.com/docs/free](https://render.com/docs/free), [blueprint-spec](https://render.com/docs/blueprint-spec), [outbound-bandwidth](https://render.com/docs/outbound-bandwidth) |
| **API uxlamasligi — tanlangan (foydalanuvchi qarori, 2026-10-10)** | Render Free + cron-job.org ping har 10 daqiqada `/health` ga | $0 | Uxlash 15 daqiqa trafiksiz — 10 daqiqalik ping yetadi. Oyiga ~744 soat (31 kun × 24) 750 lik bepul limitdan: **zaxira 6 soat**, shart — workspace'da boshqa bepul servis yo'q (soatlar bo'linadi; limit tugasa oy oxirigacha **hamma** bepul servis to'xtaydi). CPU 0.1 qoladi: feed ~3.1 s o'zgarmaydi, faqat ~34 s uyg'onish yo'qoladi. Ping trafigi juda kichik (`/health` javobi ~40 bayt) | [render.com/docs/free](https://render.com/docs/free) — 750 soat, hammasi to'xtashi va 15 daqiqa tekshirildi 2026-10-10; [cron-job.org](https://cron-job.org) |
| API, to'xtamaydigan (qachon: haqiqiy foydalanuvchilar paydo bo'lganda yoki soat limiti tig'izlashganda) | Render Starter | $7/oy | 0.5 CPU, 512 MB; karta kerak | [render.com/pricing](https://render.com/pricing) (sahifa to'liq o'qilmadi; narx ikkinchi manbadan) |
| API, zaxira (ko'rib chiqilgan) | Google Cloud Run, Singapur (`asia-southeast1`, bazaga yaqin) | Bizning hajmda amalda $0 | Bepul chegara oyiga 180 000 vCPU-s, 360 000 GiB-s, 2 mln so'rov; uyg'onish 1–3 s; karta kerak; ko'chirish 1–2 soat. Raqamlar foydalanuvchidan (2026-10-10), rasmiy sahifadan tekshirilmadi (sahifa to'liq ochilmadi); Singapur qaysi narx tier'ida — tekshirilmagan | [cloud.google.com/run/pricing](https://cloud.google.com/run/pricing) |
| API, to'xtamaydigan (ko'rib chiqilmoqda) | Fly.io, Singapur, shared-cpu-1x 512 MB | ~$4.7/oy (taxmin: $3.69 AQSh narxi + Singapur ustamasi) | Bepul tarif yo'q; sinov muddatidan keyin karta kerak | [docs.fly.io/about/pricing](https://docs.fly.io/about/pricing) |

Render Free'ning sovuq starti (~34 s, DevTools) TZ'dagi "tavsiya < 500 ms" talabiga zid edi;
2026-10-10 dan ping uni yo'qotadi (yuqorida). Feed tezligi (0.1 CPU) qoladi. Variantlar va tavsiya:
`docs/deploy.md`, 5-bo'lim. Render ro'yxatdan o'tishda firibgarlikka qarshi tekshiruv
uchun karta so'rashi mumkin (forum xabarlari; rasmiy sahifada aytilmagan).
Render'ning bepul Postgres'i 30 kundan keyin o'chadi — biz Supabase ishlatamiz.

### Do'konlar va iOS build (TZ 1.30, tekshirildi 2026-11-13)

| Nima | Narx | Shart | Manba |
|---|---|---|---|
| Google Play developer akkaunti | **$25 bir marta** | Shaxsiy akkaunt: hukumat ID va o'z nomidagi karta so'ralishi mumkin; Play Console mobil ilovasi orqali Android qurilmaga kirishni tasdiqlash — ilova chiqarishdan oldin. Tasdiqlash muddati sahifada yo'q | [support.google.com/googleplay/android-developer/answer/6112435](https://support.google.com/googleplay/android-developer/answer/6112435) |
| Google Play: yangi shaxsiy akkaunt uchun yopiq test | $0 | 2023-11-13 dan keyin ochilgan shaxsiy akkaunt: kamida **12 tester, kamida 14 kun ketma-ket** qo'shilgan bo'lishi; chiqib qayta qo'shilgan tester hisoblanmaydi. Keyin "Apply for production" (yopiq test, ilova va tayyorlik haqida savollar); ko'rik "usually takes seven days or less, but can occasionally take longer" | [support.google.com/googleplay/android-developer/answer/14151465](https://support.google.com/googleplay/android-developer/answer/14151465) |
| Apple Developer Program | **99 USD yiliga** (mintaqada mahalliy valyutada) | Individual: 2FA yoqilgan Apple Account, voyaga yetgan, Apple Account'da haqiqiy ism-familiya (taxallus kechiktiradi). Tashkilot: yuridik shaxs, D-U-N-S raqami, domenli ish email, ishlaydigan veb-sayt. Muddat sahifada yo'q; xarid tasdig'i 24 soat ichida kelmasa — support | [developer.apple.com/programs/enroll](https://developer.apple.com/programs/enroll/), [developer.apple.com/support/enrollment](https://developer.apple.com/support/enrollment/) |
| iOS build: macOS majburiy | — | "Xcode is required to build and release your app. You must use a device running macOS" — Windows'dan faqat bulutli macOS orqali | [docs.flutter.dev/deployment/ios](https://docs.flutter.dev/deployment/ios) |
| iOS bulutli build: Codemagic | Bepul: **oyiga 500 daqiqa** Mac mini M2, 1 parallel build, build 120 daqiqagacha; keyin M2 **$0.095/daqiqa** (M4 $0.114) | App Store Connect API kaliti bilan sertifikat yaratadi va profillarni oladi (Mac'siz imzolash); bepul tarifda imzolash va yuklash mumkinligi narx sahifasida aytilmagan | [codemagic.io/pricing](https://codemagic.io/pricing/), [docs.codemagic.io/yaml-code-signing/signing-ios](https://docs.codemagic.io/yaml-code-signing/signing-ios/) |
| iOS bulutli build: GitHub Actions macOS | **$0.062/daqiqa** (standart macOS runner) | Bepul daqiqalar (GitHub Free) shu sahifada aytilmagan; imzolashni o'zimiz sozlaymiz | [docs.github.com/en/billing/reference/actions-runner-pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing) |

Bitta Flutter iOS build'i necha daqiqa olishi o'lchanmagan. Shuning uchun "500 daqiqa yetadi"
degan xulosa yo'q: birinchi build'dan keyin o'lchanadi.

## 3. TMDB tijorat litsenziyasi

- Bepul API faqat notijorat foydalanish uchun. Daromad olish (obuna, reklama, pullik
  tarif) — faqat TMDB bilan alohida yozma kelishuv bilan
  ([TMDB API Terms of Use](https://www.themoviedb.org/api-terms-of-use)).
- **Narx ochiq emas:** shartlarda faqat "may be subject to, among other things, payment
  of fees" deyilgan. Summa `sales@themoviedb.org` orqali kelishiladi (`docs/legal.md`).
- Kerak bo'ladigan payt: **monetizatsiyadan oldin**. Alfa va bepul launch uchun emas.
- Bepul tarifda ham atributsiya shart: TMDB logosi va "not endorsed or certified by
  TMDB" jumlasi (web'da `/about` va Profil sahifasida bor, logo hali qo'shilmagan).
- **Watch providers** ("qayerdan ko'rish mumkin", `GET /movie/{id}/watch/providers`) bepul
  API ichida, qo'shimcha narxsiz. Ikki shart
  ([developer.themoviedb.org/reference/movie-watch-providers](https://developer.themoviedb.org/reference/movie-watch-providers),
  o'qildi 2026-10-12):
  - manba sifatida **JustWatch ko'rsatilishi shart**: "In order to use this data you must
    attribute the source of the data as JustWatch.";
  - buzilsa TMDB **kalitni bekor qiladi**: "If we find any usage not complying with these
    terms we will revoke access to the API."
  Deep link berilmaydi: javobdagi `link` — TMDB'ning o'z "qayerda ko'rish" sahifasi
  (masalan `themoviedb.org/movie/11324-shutter-island/watch?locale=RU`). Attributsiya qanday
  ko'rinishda bo'lishi (logo, joy) sahifada aytilmagan. O'zbekiston uchun ma'lumot yo'q,
  funksiya hozir qurilmaydi (TZ, 2-bo'lim backlog, 2026-10-12).

## 4. Umumiy manzara

| | 500 film, alfa (hisob 30–50 tester uchun; TZ 1.30 da 12 tester) | Izoh |
|---|---|---|
| Bir martalik (trait + embedding) | $0.03 – $0.45 | Provayderga bog'liq, yuqoridagi jadvallar |
| Oylik: LLM izohlar | ≤ $4 (Gemini) | Eng yomon holat: 50 tester har kuni limitga yetadi, 50 × $0.08. Avval "< $1" yozilgan edi — limit hisobiga noto'g'ri edi (2026-10-02 tuzatildi). Oddiy foydalanishda ancha kam |
| Oylik: assistant | ~$0.039 × faol tester (20 xabar), ~$0.106 (20 suhbat); eng yomoni ~$1.73 × tester (har kuni 30) | Gemini 3.5 Flash-Lite, ADR 0009; suhbat boshidagi xabar **o'lchangan** 2026-11-12 (`556e676`, 10 xabar, $0.00184), suhbat ichidagi o'rtacha ~$0.00193 — taxmin (oldin 2026-11-11, 72 xabar, $0.00164 o'lchangan). Bepul tarifda $0 |
| Oylik: baza + hosting | $0 | Free tariflar; cheklovlari yuqorida |
| TMDB | $0 | Monetizatsiyagacha |

## O'zgarishlar

| Sana | Nima o'zgardi |
|---|---|
| 2026-09-30 | Birinchi versiya. Provayder tanlanmagan; katalog 500 |
| 2026-09-30 | Trait sync rejimi narxi (standart $0.30/$2.50 va bepul tarif); bitta filmning o'lchangan tokenlari |
| 2026-10-01 | Trait tokenlari o'lchov bilan almashtirildi: 50 film, 380/195 film boshiga; haqiqiy run $0.0301 standart tarifda, bepul tarifda $0. Gemini 500/5 000 film qayta hisoblandi |
| 2026-10-02 | Izoh tokenlari o'lchov bilan almashtirildi: 187 / 30 (19 ta run, F2 qo'lda tekshiruvi); Gemini standart tarifda $0.00013 bitta izoh, oyiga ≤ $0.08. Boshqa provayderlar qatori shu tokenlar bilan qayta hisoblandi |
| 2026-10-01 | 2-bosqich: davomi 260 so'rov, 94 800 / 47 199 token, $0.1464 standart tarifda (o'lchangan); birinchi urinish ≈ $0.12 (taxmin); jami ≈ $0.27, bepul tarifda $0 |
| 2026-10-12 | TMDB watch providers: bepul API ichida, JustWatch attributsiyasi shart, buzilsa kalit bekor qilinadi; deep link yo'q (3-bo'lim). UZ uchun ma'lumot yo'q — funksiya hozir qurilmaydi |
| 2026-10-10 | Hosting: uyqu muammosi uchun Render Starter o'rniga bepul yechim — Render Free + cron-job.org ping har 10 daqiqada (foydalanuvchi qarori): ~744 / 750 soat, zaxira 6 soat, boshqa bepul servis bo'lmasligi shart; Render `free` sahifasi bilan tekshirildi. Starter — haqiqiy foydalanuvchilar yoki soat limiti tig'izlashganda. Zaxira: Google Cloud Run Singapur (raqamlar tekshirilmagan) |
| 2026-10-08 | Hosting: Render Free aniqlashtirildi (0.1 CPU / 512 MB, Singapur, Hobby trafigi 5 GB 2026-08-01 dan); to'xtamaydigan variantlar qo'shildi: Render Starter $7/oy, Fly.io Singapur ~$4.7/oy (taxmin) |
| 2026-11-13 | Do'konlar va iOS build qo'shildi (TZ 1.30): Google Play $25 bir marta va yangi shaxsiy akkauntga 12 tester × 14 kun yopiq test; Apple Developer 99 USD/yil; iOS build macOS talab qiladi — Codemagic bepul 500 daqiqa M2/oy, keyin $0.095/daqiqa; GitHub Actions macOS $0.062/daqiqa. Rasmiy sahifalar 2026-11-13 da o'qildi |
| 2026-11-13 | Assistant: `intro` bilan narx o'lchandi — Render log'i 06:17–06:18 UTC, 8 xabar, o'rtacha 4 847 / 159 token, $0.00185 (taxmin +$0.00007 edi, o'lchovda +$0.00001). Render'dagi Gemini kaliti **bepul tarifda** ekani 429 javobidan aniqlandi (daqiqasiga 15 so'rov, Flash-Lite); dollar raqamlari pullik tarif narxida, hisob-kitob qilinmagan. Tier 1 shartlari rasmiy sahifadan tekshirildi |
| 2026-11-13 | Assistant: kirish gapi tool'ning `intro` argumentiga ko'chdi (ADR 0009 qo'shimchasi 2) — tool sxemasi 3 091 → 3 331 belgi, taxminan +$0.00007 xabarga (~+140 kirish, ~+12 chiqish token); tashxisga 6 ta to'g'ridan-to'g'ri chaqiruv (~1 980 kirish + ~25 chiqish token har biri, ~$0.004 jami). O'lchov deploy'dan keyin |
| 2026-11-13 | Assistant: kattalashgan prefiks taxmini o'lchov bilan almashtirildi — Render log'i, 2026-11-12 19:33–19:34 UTC, 10 xabar (hammasi yangi suhbat, kontekstsiz — shu kuni keyinroq aniqlandi va tuzatildi): o'rtacha 4 713 / 169 token, **$0.00184** suhbat boshidagi xabar; suhbat ichidagi o'rtacha ~$0.00193 (taxmin), oyiga 20 xabar ~$0.039, 20 suhbat ~$0.106, limitda ~$1.73; qayta urinish 0, kesilgan chaqiruv 0 |
| 2026-11-13 | Assistant: prefiks kattalashdi (`genres` argumenti, kirish gapi; TZ 1.29) — taxmin ~$0.0018 xabarga (o'lchangan $0.00164 + ~280 kirish token × 2 chaqiruv), limitda ~$1.66 oyiga; o'lchov Render log'ini kutmoqda. Kesilgan chaqiruv tokenlari endi taxminan yoziladi (TZ 1.28) |
| 2026-11-12 | Assistant narxi o'lchov bilan almashtirildi: 72 xabar $0.1086, oddiy xabar $0.00164 (4 393 / 128 token), off-topic $0.00055; oyiga 20 xabar $0.033, 20 suhbat $0.086, limitda $1.48. Kesh 0 marta urildi. 503 da bir marta qayta urinish: xabar boshiga eng yomoni 4 chaqiruv |
| 2026-11-11 | Assistant: Claude Sonnet 5 o'rniga Gemini 3.5 Flash-Lite, provayder interfeysi orqali (ADR 0009, foydalanuvchi qarori). Narx 0.30 / 2.50, kesh urilgan kirish 0.03 (sahifa tekshirildi). Taxmin ~$0.0018 bir xabarga, oyiga 20 xabar ≈ $0.04; implicit kesh minimumi Flash-Lite uchun ko'rsatilmagan (3.x Flash: 4 096), hisob keshsiz |
