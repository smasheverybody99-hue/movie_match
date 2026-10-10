# Deploy — API Render'da (Singapur)

F4 dan oldin alohida qadam, foydalanuvchi qarori bilan (2026-10-08). Maqsad — F3 ning
ochiq o'lchovlarini (onboarding vaqti FR-3, feed tezligi, Lighthouse) jonli URL'da olish:
API bazaning yonida turadi. F5 ning qolgani (telemetriya, metrikalar, "wrong" tugmasi,
testerlar) F5 da qoladi.

| Qism | Qayerda | Holat |
|---|---|---|
| API | Render Free, **Singapur** (`render.yaml`) | **Ishlayapti** (2026-10-08): <https://movie-match-api-mgdn.onrender.com>, natijalar 1a-bo'limda |
| Baza | Supabase, asosiy loyiha, `ap-southeast-1` (Singapur) | O'zgarmaydi |
| Web | Cloudflare Pages Free (`docs/costs.md`) | Tayyorgarlik: 6-bo'lim |

Faktlar 2026-10-08 da rasmiy sahifalardan tekshirildi (manbalar pastda).

## 1. Render: yaratish tartibi

Mintaqa servis yaratilgandan keyin **o'zgarmaydi** (Render: "You can't modify this value
after creation"). Shuning uchun u qo'lda tanlanmaydi: `render.yaml` da
`region: singapore` yozilgan, Render uni fayldan oladi. Qo'lda forma ("New > Web
Service") **ishlatilmaydi**: u yerda mintaqa ro'yxatdan tanlanadi va standart qiymat
Oregon.

1. render.com → **Sign up** → **GitHub** bilan kirish.
   **Karta so'ralsa — to'xtang**, hech narsa kiritmang, menga yozing. (Render
   forumlarida "firibgarlikka qarshi tekshiruv uchun karta so'raladi" degan xabarlar bor:
   hammadan emas, lekin bo'lishi mumkin.)
2. GitHub ruxsati: faqat `movie_match` repozitoriysiga ("Only select repositories").
3. Dashboard → **New** → **Blueprint**.
4. Repo ro'yxatidan `movie_match` → **Connect**.
5. Formada: **Blueprint Name** — `movie-match`; **Branch** — `main`; **Blueprint Path** —
   bo'sh qoldiring (standart `render.yaml`).
6. **O'zgarishlar ro'yxati** (Render nima yaratishini ko'rsatadi). Bu yerda tekshiring:
   - bitta servis: `movie-match-api`, web service, plan **Free**;
   - mintaqa — **Singapore**. Boshqa mintaqa ko'rinsa, **Deploy bosmang**, menga yozing.
7. Shu sahifada `sync: false` o'zgaruvchilar uchun maydonlar chiqadi — 2-bo'limdagi
   to'rttasini kiriting.
8. **Deploy Blueprint**. Birinchi build bir necha daqiqa oladi.
9. Servis sahifasida URL ko'rinadi (`https://movie-match-api-XXXX.onrender.com`).
   Brauzerda `<URL>/health`, keyin `<URL>/health/db` ni oching — ikkalasi
   `"status":"ok"` bo'lishi kerak. Natijani menga yuboring (URL'da kalit yo'q).

Avtomatik deploy: faqat GitHub gate (CI) o'tgan commit'lar (`autoDeployTrigger:
checksPass`) va faqat `services/api/`, `packages/shared/` yoki `render.yaml` o'zgarganda.

Migratsiyalar Render'da ishga tushmaydi. Asosiy baza hozir eng oxirgi migratsiyada. Yangi
migratsiya bo'lsa, `alembic upgrade head` avvalgidek mahalliy mashinadan ishga
tushiriladi.

## 1a. Natija (2026-10-08)

API Blueprint orqali yaratildi: <https://movie-match-api-mgdn.onrender.com>.

| Tekshiruv | Natija |
|---|---|
| `/health` | 200, `"status":"ok"` |
| `/health/db` | 200, `"status":"ok"`, `"database":"reachable"` |
| Server vaqti, bitta ulanishda 10 juftlik (Claude) | `/health` 290–430 ms, `/health/db` 325–710 ms (ko'pi 330–420); farq ~40 ms |
| Foydalanuvchi o'lchovi | `/health` 0.22–0.26 s, `/health/db` 0.22–0.30 s; farq ~0 |

**Mintaqa tekshiruvi.** DNS nomi `gcp-us-west1-1.origin.onrender.com` (Oregon nomi) avval
servis Oregon'da degan xavotir berdi. O'lchov buni rad etdi:
- lokal API'da `/health/db` bazaga ~5 marta boradi: ~1.4 s, bir borib-kelish ~270 ms;
- Render'da ortiqcha vaqt ~40 ms, ya'ni bir borib-kelish ≤ ~8 ms (eng yomoni ≤ 40 ms).
  Oregon→Singapur ~5 × 160 ms ≈ 800 ms qo'shardi.

Demak, API bazaning (`aws-0-ap-southeast-1`) yonida. DNS nomi servis mintaqasini
ko'rsatmaydi: u Render'ning kirish nuqtasi nomi. Panelda "Settings → Region" alohida
ko'rilmadi, foydalanuvchi qarori bilan: o'lchov yetarli dalil.

## 1b. Auto-deploy (2026-10-10)

**Qoida:** `main` ga har push, GitHub gate'i (CI) yashil bo'lgach, API'ni qayta deploy qiladi
(`autoDeployTrigger: checksPass`, `buildFilter` yo'q). Veb — Cloudflare Pages, har push'da
alohida.

**Nega filtr olib tashlandi.** Avval `buildFilter` faqat `services/api/**`,
`packages/shared/**` va `render.yaml` o'zgarganda deploy qilardi. 2026-10-10 dagi push
(`5c8264a..49207fa`, to'rt commit) ichida `81c29a7` `services/api/app/main.py` ni o'zgartirgan,
lekin push'ning oxirgi commiti `49207fa` veb edi — Render deploy qilmadi, foydalanuvchi qo'lda
ishga tushirdi. Dalillar shunga mos: Render filtrni push'ning **tip commiti** bo'yicha
baholaydi (butun push yoki oxirgi deploy'dan beri bo'yicha emas: ikkala oraliqda ham
`main.py` bor edi). Render hujjati buni ochiq aytmaydi (`render.com/docs/monorepo-support`).

**Tekshiruv har push'dan keyin:** `/health` javobidagi `commit` — deploy qilingan commit
(Render'ning `RENDER_GIT_COMMIT`). U push'ning tip commitiga teng bo'lishi kerak; lokalda
`null`.

**Kuzatish kerak: build daqiqalari.** Endi veb va docs push'lari ham API'ni build qiladi.
Render Billing → Pipeline Minutes (bepul: 500/oy). Daqiqalar tez o'sib ketsa — filtrni
qaytarish, `/health` dagi `commit` esa xavfsizlik to'ri bo'ladi (API commiti veb commiti
ostida qolib ketsa, darhol ko'rinadi).

## 2. O'zgaruvchilar (qiymatlarini faqat Render panelida kiritasiz)

Repoda qiymat yo'q. `render.yaml` da faqat sir bo'lmaganlari bor: `PYTHON_VERSION`
(3.12.10), `ENV=production` (SQL logini o'chiradi), `LLM_PROVIDER=gemini`,
`EMBEDDING_DIM=1536`.

| O'zgaruvchi | Nima | Qayerdan |
|---|---|---|
| `DATABASE_URL` | Asosiy baza, session pooler, `postgresql+asyncpg://...` | `services/api/.env` dagi bilan bir xil |
| `SUPABASE_PROJECT_URL` | `https://<ref>.supabase.co` | `.env` dagi bilan bir xil |
| `GEMINI_API_KEY` | Keshda yo'q izohlar uchun ("Why you'll like this") | `.env` dagi bilan bir xil |
| `CORS_ORIGINS` | Web manzili. Hozircha `http://localhost:5173`; web deploy bo'lgach, Pages URL'i qo'shiladi (vergul bilan) | — |

Kerak **emas**, kiritilmaydi: `TEST_DATABASE_URL` (testlar uchun), `TMDB_API_KEY`
(ingestion — fon ishi, serverda emas), `ANTHROPIC_API_KEY` (F4), `SUPABASE_JWT_SECRET`
(bo'sh qolishi shart, ADR 0007), `REDIS_URL` (ishlatilmaydi).

## 3. O'lchovdan oldin isitish

Render Free 15 daqiqa so'rovsiz qolsa to'xtaydi, qayta turishi ~1 daqiqa. Aks holda
birinchi so'rov uyg'onish vaqtini o'lchaydi.

1. `<URL>/health` ni oching. Javob kelguncha kuting (1 daqiqagacha) — bu uyg'onish.
2. `<URL>/health/db` — bazaga birinchi ulanish (pool shu yerda ochiladi).
3. Ilovada Home'ni bir marta oching — katalog keshlari yuklanadi (daraja chegaralari,
   sabablar qoidasi; ~10 daqiqaga saqlanadi).
4. Shundan keyin o'lchang. O'lchovlar orasida 15 daqiqadan ko'p tanaffus bo'lsa —
   1-qadamdan qayta.

Raqamlarni yozganda "isitilgan" deb belgilaymiz. Sovuq start alohida bir marta o'lchanadi.

## 4. Cheklovlar va taxminlar

**Xotira (Free: 512 MB, 0.1 CPU).** Mahalliy o'lchov (Windows, 2026-10-08): butun API
import qilinganda ~91 MB, Gemini SDK bilan ~93 MB; haqiqiy so'rovlarga xizmat qilgan
server cho'qqisi **102 MB**. Linux'da shu tartibda, ehtiyot bilan **120–180 MB** — limitning
~25–35%. Chegaraga yaqin emas. Xavf faqat ikki holatda: worker sonini oshirish (har biri
to'liq nusxa) yoki katalog embedding'larini Python'ga yuklash (500 × 1 536 son ≈ 30–40 MB).

**CPU 0.1.** Mahalliy hisob ~0.03 s, 0.1 CPU da ~0.3 s bo'lishi mumkin; JSON va token
tekshiruvi ham sekinlashadi. Deploy'dan keyingi o'lchov buni ko'rsatadi.

**Trafik: oyiga 5 GB** (Hobby workspace, 2026-08-01 dan). Karta bo'lmasa, oshib ketganda
Render servislarni **oy oxirigacha to'xtatadi**. Taxmin: `/recommendations` javobi
~40–60 KB (50 film, tavsifi bilan; API javoblarni siqmaydi). 50 tester × kuniga 10 marta ≈
0.75 GB/oy, boshqa so'rovlar bilan ~1–2 GB. Posterlar TMDB'dan, web Cloudflare'dan keladi —
ular hisobga kirmaydi. Alfa uchun yetadi. Zaxira: API javoblarini gzip bilan siqish
(bir qatorlik o'zgarish, hozir qilinmaydi).

**Supabase Free pauzasi.** Loyiha **bir hafta** davomida bazaga yetarli so'rov
kelmasa to'xtatiladi; pauzadan taxminan bir hafta oldin ogohlantirish xati keladi.
Dashboard → loyiha → **Resume project** bilan qaytariladi (ma'lumot saqlanadi, 1 yil
ichida). Alfa davomida testerlar kunda so'rov yuboradi — xavf faqat tanaffuslarda. Test
loyihasi (Frankfurt) har push'da CI tomonidan ishlatiladi. Pauzasiz: Supabase Pro, $25/oy.

## 5. Haqiqiy foydalanuvchi uchun uyg'onish muammosi

Tanlangan: B (2026-10-10, pastda).

| Variant | Narx | Afzalligi | Kamchiligi |
|---|---|---|---|
| A. Render Starter | $7/oy | Hech qachon to'xtamaydi; CPU 0.5 (Free'dan 5×); faqat tarif almashadi | Karta kerak |
| B. Free + tashqi "ping" har ≤ 14 daqiqada (masalan bepul uptime monitor) | $0 | Kod va hisob o'zgarmaydi | Oyiga ~744 soat — 750 soatlik bepul limitning deyarli hammasi, ya'ni faqat bitta bepul servis; CPU 0.1 qoladi; Render shartlari bunga qanday qarashini tekshirmadim |
| C. Fly.io, Singapur, shared-cpu-1x 512 MB | ~$4.7/oy (taxmin: AQSh narxi $3.69 + Singapur ustamasi) | To'xtamaydi | Karta kerak; yangi platforma, `render.yaml` o'rniga boshqa sozlama; bepul tarif yo'q |

~~**Qaror (2026-10-09):** alfa testerlar chaqirilishidan oldin **A** (Render Starter).~~

**Qaror (2026-10-10, foydalanuvchi):** **B** — cron-job.org har 10 daqiqada `/health` ga so'rov
yuboradi. Render uxlatadi 15 daqiqa trafiksiz (render.com/docs/free, 2026-10-10). Oyiga
~744 / 750 soat: workspace'da boshqa bepul servis bo'lmasligi shart. CPU 0.1 qoladi. **A**
(Starter) haqiqiy foydalanuvchilar paydo bo'lganda yoki soat limiti tig'izlashganda; zaxira —
Google Cloud Run, Singapur (`docs/costs.md`).

## 6. Web: Cloudflare Pages

Build `apps/web` dan tashqariga chiqmaydi (traitlar ro'yxati ichida, `src/lib/traits.ts`).
Shuning uchun root directory `apps/web`. Yo'llar (`/movie/123` va boshqalar): `404.html`
yo'q bo'lsa, Pages ilovani SPA deb hisoblaydi va har yo'lni ilovaga beradi. Qo'shimcha
fayl kerak emas.

Pages har `main` push'ida build qiladi: CI'ni kutmaydi, Render'dan farqli. `npm run
build` ichida `tsc` bor, shuning uchun tip xatosi bo'lsa build yiqiladi.

Bosiladigan tugmalar:

1. dash.cloudflare.com → **Sign up** (email). Karta so'ralsa — to'xtang.
2. **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
3. **GitHub** → ruxsat: **Only select repositories** → `movie_match`.
4. `movie_match` → **Begin setup**.
5. Formada:
   - Project name: `movie-match`. URL `https://movie-match.pages.dev` bo'ladi; nom band
     bo'lsa boshqasi, URL shunga qarab o'zgaradi.
   - Production branch: `main`.
   - Framework preset: **Vite** (yoki None).
   - Build command: `npm run build`.
   - Build output directory: `dist`.
   - Root directory (advanced): `apps/web`.
   - Environment variables (qiymatsiz ro'yxat):
     - `NODE_VERSION` = `24` (`.nvmrc` bilan bir xil);
     - `VITE_API_URL` = `https://movie-match-api-mgdn.onrender.com`;
     - `VITE_SUPABASE_URL` — `apps/web/.env` dagi bilan bir xil;
     - `VITE_SUPABASE_ANON_KEY` — `apps/web/.env` dagi bilan bir xil.
       Brauzerga ochiq kalit, lekin baribir faqat panelga kiritiladi.
     - `VITE_MOCK_API` kiritilmaydi.
6. **Save and Deploy**. Tayyor bo'lgach, sayt URL'ini menga yuboring.

`VITE_*` qiymatlar build paytida kodga yoziladi. Ularni o'zgartirsangiz, **qayta deploy
qilish shart** (Deployments → oxirgi deploy → **Retry deployment**).

## 7. Web manzili ma'lum bo'lgach

`<WEB>` = Pages URL, masalan `https://movie-match.pages.dev` (oxirida `/` siz).

**Render (CORS):**
1. Servis `movie-match-api` → **Environment**.
2. `CORS_ORIGINS` → **Edit** → `<WEB>,http://localhost:5173`.
3. **Save and deploy** (build qayta kerak emas).

**Supabase (kirish qaytadigan manzil):**
1. Asosiy loyiha → **Authentication** → **URL Configuration**.
2. **Site URL** → `<WEB>` → **Save**.
3. **Redirect URLs** → **Add URL** → `<WEB>/` → **Save**.
   `http://localhost:5173/**` ro'yxatda qoladi (lokal ish uchun).

Google kirishi uchun Google Cloud sozlamasi o'zgarmaydi: u Supabase'ning callback
manziliga qaytadi, u esa o'zgarmagan.

**Tekshiruv:** `<WEB>` → Google bilan kirish → Home'ning yuklanishi. Brauzer konsolida CORS
xatosi bo'lmasligi kerak.

## Manbalar

- Render Free: <https://render.com/docs/free> (15 daqiqa, ~1 daqiqa, 750 soat)
- Render mintaqalari: <https://render.com/docs/regions> (Singapur bor, o'zgarmaydi)
- Blueprint: <https://render.com/docs/blueprint-spec> (`region` standarti oregon, `plan: free` = 0.1 CPU / 512 MB, `autoDeployTrigger`, `sync: false`)
- Blueprint yaratish: <https://render.com/docs/infrastructure-as-code>
- Monorepo, root directory: <https://render.com/docs/monorepo-support>
- Python versiyasi: <https://render.com/docs/python-version>
- Trafik: <https://render.com/docs/outbound-bandwidth> (Hobby 5 GB)
- Supabase pauzasi: <https://supabase.com/docs/guides/platform/free-project-pausing>
- Cloudflare Pages, Git: <https://developers.cloudflare.com/pages/get-started/git-integration/>
- Pages build image (Node versiyasi): <https://developers.cloudflare.com/pages/configuration/build-image/>
- Pages SPA yo'llari: <https://developers.cloudflare.com/pages/configuration/serving-pages/>
- Render o'zgaruvchilarini tahrirlash: <https://render.com/docs/configure-environment-variables>
- Supabase redirect URL'lari: <https://supabase.com/docs/guides/auth/redirect-urls>
- Fly.io narxlari: <https://docs.fly.io/about/pricing>
- Render Starter $7/oy: <https://render.com/pricing> (sahifa to'liq o'qilmadi; narx ikkinchi manbadan va 2026-08-01 dagi o'zgarish sharhidan)
