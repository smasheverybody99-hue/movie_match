# Holat — Movie Match

Oxirgi yangilanish: 2026-09-29 · `main` = `3a8181c` · F3 ishi `phase-3-web` branch'ida (hali `main` ga qo'shilmagan)

Bitta sahifada: qaysi faza tugagan, nima chala, keyingi qadam. Tafsilotlar faza
hisobotlarida: `docs/phase-1-status.md`, `docs/phase-2-status.md`, `docs/phase-3-status.md`. Fazalar ro'yxati:
`docs/prompts/README.md`.

## Fazalar

| Faza | Holat |
|---|---|
| F0 — Poydevor | **Tugagan** (`b2a4d35`, gate o'tgan) |
| F1 — Ma'lumot va Movie DNA | **Kod tugagan, ma'lumot chala.** 5 000 film TMDB'dan yuklangan. Traitlar va embeddinglar hali yo'q: birinchi pullik qadam (50 film) tasdiq kutmoqda |
| F2 — Tavsiya dvigateli | **Kod tugagan va `main` da, qo'lda tekshiruv chala.** Gate yashil. Qo'lda tekshiruv F1 ma'lumotini talab qiladi |
| F3 — Web ilova | **Kod tugagan, `phase-3-web` branch'ida, CI yashil. Qo'lda tekshiruv chala.** Foydalanuvchi so'rovi bilan F2 qo'lda tekshiruvidan oldin boshlangan (prompt sharti bajarilmagan). Onboarding vaqti o'lchanmagan: Supabase kalitlari va trait'li filmlar kerak |
| F4 va keyingilari | Boshlanmagan |

## Oxirgi gate natijasi

| | |
|---|---|
| CI (GitHub Actions, `phase-3-web`, `9b046e1`) | **Yashil**, 2026-09-29: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36538488478 — endi web uchun `typecheck`, `npm test` va `": any"` tekshiruvi ham bor |
| CI (`main`, `4084b5e`) | Yashil, 2026-09-29: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36522528019 |
| Web testlari | Mahalliy, 2026-09-29: 11 fayl, 90 test, hammasi o'tgan; lint 0, typecheck 0 |
| `app/services/` coverage | CI (`9b046e1`): ≥ 85% (`--fail-under=85` qadami o'tgan; aniq raqam run log'ida). Mahalliy to'liq run, 2026-09-28: **98.9%** (535 statement, 6 miss) |
| Testlar | Mahalliy, 2026-09-28: 371 o'tgan, 1 yiqilgan. Yiqilgani tarmoq uzilishi (`WinError 1236`), assert emas. CI'da hammasi o'tgan |

CI Supabase'ga ulanmaydi: runner'dagi Postgres 17 + pgvector konteyneri ishlatiladi,
secret yo'q (`.github/workflows/gate.yml`).

## Chala

1. **F1: traitlar va embeddinglar.** 5 000 filmning hammasida yo'q. Bosqichlar:
   50 → 500 → 5 000, har biridan oldin tasdiq (CLAUDE.md). 1-bosqich ≈ $0.02
   (`docs/phase-1-status.md`, "Cost estimates"). Gemini kaliti bilan oxirgi urinish
   `400 FAILED_PRECONDITION` bilan rad etilgan; birinchi gumon: kalit loyihasida billing
   yoqilmagan.
2. **F1: 50 filmni qo'lda ko'rib chiqish.** `docs/review-films.md` hali qoralama.
3. **F2: qo'lda tekshiruv.** 30 ta baho qo'yib tavsiyalarni o'qish; bitta match'ni qo'lda
   hisoblash; 5 ta izohni o'qish (≈ $0.002 Gemini, tasdiq bilan).
4. **F3: kirish sozlanmagan.** `apps/web/.env` da `VITE_SUPABASE_URL` va
   `VITE_SUPABASE_ANON_KEY` yo'q; Supabase'da Google provayderi va redirect URL'lar
   yoqilishi kerak. Apple kirishi Apple Developer Program'ni talab qiladi ($99/yil) —
   foydalanuvchi qarori.
5. **F3: qo'lda tekshiruv chala.** Onboarding vaqti o'lchanmagan; Lighthouse dev serverda
   o'lchangan (LCP 2.1 s mobil, INP 80 ms) — production build va haqiqiy posterlar bilan
   qayta o'lchash kerak. axe: 0 buzilish, 320px: gorizontal scroll yo'q
   (`docs/phase-3-status.md`).
6. **Tezlik (TZ: tavsiya < 500 ms) o'lchanmagan.** Dev mashinadan bazagacha so'rov
   150–1000 ms; bazaga yaqin serverdan o'lchash kerak.

## Keyingi qadam

F1 1-bosqichi hamon asosiy to'siq: F2 va F3 qo'lda tekshiruvlari trait'li filmlarni
talab qiladi. Kalit billing'ini tekshirish (bepul `models.list` so'rovi), keyin
`docs/review-films.md` ni tuzatib, 50 filmga trait ekstraksiyasi (≈ $0.02), **faqat
tasdiqdan keyin**.

Parallel (pulsiz): `apps/web/.env` ga Supabase URL va anon kalitni qo'yish, Supabase'da
Google provayderini yoqish — shunda web'da haqiqiy kirish sinab ko'riladi.
`phase-3-web` ni `main` ga qo'shish — foydalanuvchi qarori.

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
