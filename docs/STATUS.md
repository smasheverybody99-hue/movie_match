# Holat — Movie Match

Oxirgi yangilanish: 2026-09-30 · `main` = `4ccd878` (F3 `66bc7a0` da qo'shilgan) · **LLM provayderi tanlanmagan** (ADR 0006)

Bitta sahifada: qaysi faza tugagan, nima chala, keyingi qadam. Tafsilotlar faza
hisobotlarida: `docs/phase-1-status.md`, `docs/phase-2-status.md`, `docs/phase-3-status.md`. Fazalar ro'yxati:
`docs/prompts/README.md`. Xarajatlar: `docs/costs.md`.

## Fazalar

| Faza | Holat |
|---|---|
| F0 — Poydevor | **Tugagan** (`b2a4d35`, gate o'tgan) |
| F1 — Ma'lumot va Movie DNA | **Kod tugagan, ma'lumot chala.** 1-bosqich bajarildi (2026-10-01): 50 film trait oldi (sync, 0 yiqildi), qo'lda ko'rik **o'tdi** — 50 dan 3 tasi bahsli, chegara 5. 2-bosqich: traitlar 500 / 500 (13 film Google filtri bilan bloklanib almashtirildi); 2-bosqich ≈ $0.28 standart tarifda, bepul tarifda $0. Embedding 258 / 500 (birinchi run uzildi) |
| F2 — Tavsiya dvigateli | **Kod tugagan va `main` da, qo'lda tekshiruv chala.** Gate yashil. Qo'lda tekshiruv F1 ma'lumotini talab qiladi |
| F3 — Web ilova | **Kod tugagan, `main` da (`66bc7a0`), CI yashil. Qo'lda tekshiruv chala.** Foydalanuvchi so'rovi bilan F2 qo'lda tekshiruvidan oldin boshlangan (prompt sharti bajarilmagan). Onboarding vaqti o'lchanmagan: Supabase kalitlari va trait'li filmlar kerak |
| F4 va keyingilari | Boshlanmagan |

## Oxirgi gate natijasi

| | |
|---|---|
| CI (`main`, `4ccd878`) | **Yashil**, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36609806293 (provayder interfeysi, katalog 500, costs.md, Alembic log tuzatishi) |
| CI (`main`, `852c767`, provayder interfeysi) | **Qizil**, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36603649367 — `test_migrations` dan keyin `app.cost` logi o'chib qolgan; `4ccd878` da tuzatilgan |
| CI (`main`, `66bc7a0`, F3 merge) | Yashil, 2026-09-30: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36599220279 |
| Web testlari | Mahalliy, 2026-09-29: 11 fayl, 90 test, hammasi o'tgan; lint 0, typecheck 0 |
| `app/services/` coverage | CI (`9b046e1`): ≥ 85% (`--fail-under=85` qadami o'tgan; aniq raqam run log'ida). Mahalliy to'liq run, 2026-09-28: **98.9%** (535 statement, 6 miss) |
| API testlari | Mahalliy to'liq run, 2026-09-30 (`852c767` holatida): 424 o'tgan, 1 yiqilgan — CI'dagi o'sha log testi; tuzatishdan keyin u juftlik (migratsiya + provayder testlari) bilan qayta o'tgan |

CI Supabase'ga ulanmaydi: runner'dagi Postgres 17 + pgvector konteyneri ishlatiladi,
secret yo'q (`.github/workflows/gate.yml`).

## Chala

1. **Provayder tanlanmagan (ADR 0006).** Gemini Google Cloud'ning $50 karta hold talabi
   bilan yopiq. Kod provayder interfeysi orqasida; yangi provayder = bitta modul + bitta
   qator. Variantlar narxi bilan: `docs/costs.md`. Agar tanlangan provayderning
   embeddingi 1 536 o'lchamli bo'lmasa — migratsiya va qayta embed kerak (API bu holatda
   ishga tushmaydi, xato matni yo'lni aytadi).
2. **F1: traitlar va embeddinglar.** 500 lik ro'yxatda traitlar 500 / 500, embedding
   258 / 500.
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

1. **F1: embeddinglarni tugatish — qolgan 242 film.** Traitlar 500 / 500 (2026-10-01;
   13 film Google xavfsizlik filtri bilan bloklanib almashtirildi, ro'yxat
   `docs/catalogue-500.md` da). Embedding 258 / 500: birinchi run Google serveri ulanishni
   uzgani bilan to'xtadi (`status=interrupted`, $0.0095 standart tarifda, bepul tarifda
   $0). Oldin tuzatish: provayderning tarmoq xatolarini (`httpx.TransportError`)
   `TransientError` ga o'girish (embedding, trait sync, `count_tokens`), keyin o'sha buyruq.
2. **F1: qolgan tekshiruvlar.** Embeddinglardan keyin: 5 filmning eng yaqin qo'shnilari
   ko'z bilan, "missing count = 0".
3. Batch uchun billing ochilsa — `TRAIT_MODE=batch` ga qaytish (yarim narx).

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
