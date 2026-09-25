# Movie Match

AI asosidagi film tavsiya qiluvchi platforma. Web (React) + mobil (Flutter) + Python API.

## Nima qayerda

| Papka | Nima |
|---|---|
| `apps/web` | React 19 + Vite + TypeScript |
| `apps/mobile` | Flutter 3.47 |
| `services/api` | Python 3.12 + FastAPI |
| `packages/shared` | Ikkala til uchun umumiy shartnomalar (trait ro'yxati) |
| `docs` | Arxitektura, qarorlar, huquqiy eslatmalar |

## Birinchi ishga tushirish

Quyidagilarni terminalda o'zingiz bajarasiz.

### Tezkor yo'l

Git Bash (yoki macOS/Linux terminal):

```bash
./tasks.sh doctor     # kerakli dasturlar bormi
./tasks.sh install
./tasks.sh test       # faza darvozasi
```

Windows CMD yoki PowerShell:

```cmd
tasks install
tasks test
```

`tasks.cmd` — `tasks.ps1` uchun o'rovchi. PowerShell standart sozlamada `.ps1`
fayllarni ishga tushirishdan bosh tortadi; `.cmd` fayl bu cheklovga tushmaydi va
skriptni faqat shu jarayon uchun bypass bilan chaqiradi. Mashina sozlamasi o'zgarmaydi.

Agar `tasks.ps1` ni to'g'ridan-to'g'ri ishlatmoqchi bo'lsangiz, bir marta:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
Unblock-File .\tasks.ps1
```

Quyidagilar esa qo'lda, qadamba-qadam qilish uchun.

### 0. Git

```bash
cd C:\Users\User\MovieMatch
git init
git add .
git commit -m "chore: initial skeleton"
```

### 1. API (Python 3.12+)

```bash
cd services/api
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy .env.example .env          # keyin .env ichini to'ldiring
uvicorn app.main:app --reload
```

Tekshirish: http://127.0.0.1:8000/health va http://127.0.0.1:8000/docs

### 2. Web (Node 20+)

```bash
cd apps/web
npm install
copy .env.example .env
npm run dev
```

Tekshirish: http://127.0.0.1:5173

### 3. Mobil (Flutter 3.47+)

```bash
cd apps/mobile
flutter create --org com.moviematch --project-name movie_match .
flutter pub add flutter_riverpod dio go_router
flutter run
```

`lib/theme/tokens.dart` allaqachon joyida — `flutter create` uni o'chirmaydi.

## Muhit o'zgaruvchilari

`.env` fayllari hech qachon git'ga tushmaydi. Har papkadagi `.env.example` namuna.

| Kalit | Qayerdan olinadi |
|---|---|
| `DATABASE_URL` | Supabase → Project Settings → Database → Connection string (URI) |
| `SUPABASE_JWT_SECRET` | Supabase → Project Settings → API → JWT Secret |
| `TMDB_API_KEY` | themoviedb.org → Settings → API |
| `ANTHROPIC_API_KEY` | console.anthropic.com |

## Hujjatlar

| Fayl | Nima uchun |
|---|---|
| `docs/TZ.md` | **Texnik topshiriq** — nima quriladi, qabul mezonlari, test qoidasi |
| `docs/prompts/` | Fazali promptlar — har fazani Claude'ga berish uchun tayyor matn |
| `docs/ui.md` | Dizayn tizimi va ekran maketlariga havola |
| `docs/architecture.md` | Tizim qanday ishlaydi |
| `docs/legal.md` | TMDB litsenziyasi va personaj IP masalalari |
| `docs/roadmap.html` | 17 haftalik jadval (brauzerda oching) |
| `CLAUDE.md` | Claude uchun loyiha qoidalari |

## Ish tartibi

1. `docs/TZ.md` ni o'qing — nima qurilishini bilib oling.
2. `docs/prompts/phase-00-foundation.md` ni to'liq nusxalab Claude'ga bering.
3. Claude ishlab bo'lgach, **darvoza buyruqlarini o'zingiz ishga tushiring**.
4. Hammasi 100% o'tsa — keyingi fazaga o'ting. O'tmasa — tuzattiring, qayta tekshiring.

Hozirgi faza: **F0 — poydevor**.
