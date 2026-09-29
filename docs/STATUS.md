# Holat — Movie Match

Oxirgi yangilanish: 2026-09-29 · `main` = `4084b5e`

Bitta sahifada: qaysi faza tugagan, nima chala, keyingi qadam. Tafsilotlar faza
hisobotlarida: `docs/phase-1-status.md`, `docs/phase-2-status.md`. Fazalar ro'yxati:
`docs/prompts/README.md`.

## Fazalar

| Faza | Holat |
|---|---|
| F0 — Poydevor | **Tugagan** (`b2a4d35`, gate o'tgan) |
| F1 — Ma'lumot va Movie DNA | **Kod tugagan, ma'lumot chala.** 5 000 film TMDB'dan yuklangan. Traitlar va embeddinglar hali yo'q: birinchi pullik qadam (50 film) tasdiq kutmoqda |
| F2 — Tavsiya dvigateli | **Kod tugagan va `main` da, qo'lda tekshiruv chala.** Gate yashil. Qo'lda tekshiruv F1 ma'lumotini talab qiladi |
| F3 va keyingilari | Boshlanmagan. F3 ni F2 qo'lda tekshiruvidan oldin boshlamang |

## Oxirgi gate natijasi

| | |
|---|---|
| CI (GitHub Actions, `main`, `4084b5e`) | **Yashil**, 2026-09-29: https://github.com/smasheverybody99-hue/movie_match/actions/runs/36522528019 |
| `app/services/` coverage | CI: ≥ 85% (`--fail-under=85` qadami o'tgan; aniq raqam run log'ida). Mahalliy to'liq run, 2026-09-28: **98.9%** (535 statement, 6 miss) |
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
4. **Asosiy baza (Singapur) `0002` da.** `0003` (ratings.updated_at) va `0004`
   (dismissals, explanations.lang) faqat test bazasiga qo'yilgan. F2 API asosiy bazada
   ishlashidan oldin qo'llash kerak (tasdiq bilan).
5. **TZ §6 API jadvali** yangi endpointlarni (`/me`, `/dismissals`,
   `/recommendations/{id}/explanation`, `/onboarding/films`) hali sanamaydi.
6. **Tezlik (TZ: tavsiya < 500 ms) o'lchanmagan.** Dev mashinadan bazagacha so'rov
   150–1000 ms; bazaga yaqin serverdan o'lchash kerak.

## Keyingi qadam

F1 1-bosqichi: kalit billing'ini tekshirish (bepul `models.list` so'rovi), keyin
`docs/review-films.md` ni tuzatib, 50 filmga trait ekstraksiyasi (≈ $0.02), **faqat
tasdiqdan keyin**.

## Muhit

- Test bazasi: Supabase, Frankfurt (`eu-central-1`). Asosiy baza: Singapur
  (`ap-southeast-1`), 5 000 film — testlar unga hech qachon ulanmaydi.
- Node: `apps/web/.nvmrc` (24); CI ham shuni o'qiydi. Python: 3.12 (`pyproject.toml`).
- Dev mashinada Windows Application Control ba'zi native fayllarni bloklaydi
  (`alembic.exe`; 2026-09-29 dan rollup'ning `rollup.win32-x64-msvc.node` —
  mahalliy `npm run build` shu sabab yiqiladi). CI'da (Linux) build o'tadi.
