# UI/UX spetsifikatsiyasi

Dizayn tizimining **v1** versiyasi va barcha ekran maketlari alohida sahifada:

**https://claude.ai/artifact/AMbQ9PQVCAryRVZU6j96G9**

U yerda bor: rang tokenlari, tipografika (Playfair Display + Inter + JetBrains Mono),
masofa va radius, komponentlar, navigatsiya, ekran maketlari, to'rtta majburiy holat,
platforma pariteti, qabul mezoni.

**Diqqat:** quyidagi **v2 brifi** v1 bilan zid kelgan joyda v2 ustun. Eng katta farq —
rang qoidasi: v1 da qizil "foydalanuvchi bosadigan narsa", oltin "match"; v2 da qizil
**faqat match**. v2 tasdiqlangach, artifact yangilanadi yoki "v1, eskirgan" deb
belgilanadi.

---

## Dizayn brifi v2 — "jasur va zamonaviy"

Holat: **tasdiqlangan** (foydalanuvchi, 2026-10-02; qarorlar 11-bo'limda). Ekran-ekran,
bosqichma-bosqich qilinadi (9-bo'lim), hammasi birdan emas.

### 0. Manbalar va ularning o'rni

| Namuna | Nima olinadi | Nima olinmaydi |
|---|---|---|
| **NOXX — asos** | Chuqur qora fon, neytral chrome, rangni posterlar beradi. Katta poster to'ri. Hover'da poster ustida match foizi va tez tugmalar. Haqiqiy ikonkalar. Yuqori o'ngda dumaloq, yorqin qidiruv maydoni | — |
| **AZM movies — faqat bitta narsa** | Home tepasidagi butun kenglikdagi hero: eng yaxshi tavsiya, backdrop, 3–5 ta film aylanadi, chapda matn, pastda nuqtalar | Zaytun-yashil panel (aksent bilan urishadi); 10 yulduzli reyting (bizda match foizi bor — kuchliroq va o'ziga xos); o'rtada logo + hamburger (eskirgan); "Watch Now" (biz striming emasmiz) |
| **Netflix / IVI — tuzilma** | Home'da bo'limlar gorizontal poster qatorlari | — |
| **Spotify — xarakter** | Movie DNA: Wrapped uslubidagi imzo ekrani | — |

Foydalanuvchining oldingi xabarlaridan **bekor qilinganlar** (NOXX rang qoidasi ustun):
asosiy tugmaning qizil rangi va glow'i, hero'dagi faol nuqtaning qizili, bo'lim
sarlavhasidagi belgining qizili. Shakl qoladi (pill tugma, nuqtalar, belgi), rang neytral.

### 1. Rang qoidasi — eng muhim band

**Qizil (`--red`) faqat kuchli moslik uchun** (TZ 1.13, 2026-10-05). Interfeys match
foizini ko'rsatmaydi — uning o'rnida daraja: **"Kuchli moslik"** (foydalanuvchining
katalogdagi eng yaqin 5 filmi) — qizil; qolganida pill yo'q (film sahifasi va hero'da
neytral kicker). "Yaxshi moslik" API'da hisoblanadi, lekin 2026-10-06 dan ko'rsatilmaydi
(TZ 1.16: Home'dagi sahifalarning 68% ida chiqardi). Boshqa hech qayerda qizil yo'q. Sabab: qizil kam
uchrasa, kuchini saqlaydi; 1.13 gacha har kartadagi foiz badge'i bir ekranda 11 ta qizil
bergan edi. Ekranda qizil ko'rinsa — bu "katalogda sizga eng yaqinlaridan biri" degani.

Yangi rang qo'shilmaydi: hamma narsa `apps/web/src/styles/tokens.css` dagi tokenlar bilan.

| Token | Hozirgi vazifasi (v1) | v2 dagi vazifasi |
|---|---|---|
| `--bg` `#0a0a0f` | Ekran foni | O'zgarmaydi: chuqur qora fon |
| `--surface`, `--surface-2`, `--line` | Kartalar, inputlar, chegaralar | Neytral chrome, **toza kulrang** (qaror 5): tus yo'q, R = G = B |
| `--text`, `--muted`, `--faint` | Matn | O'zgarmaydi. Oddiy tugmalarning konturi ham shulardan |
| `--red` | Asosiy tugma, faol nav, tanlangan chip, input fokus, kuchli trait bar, progress nuqtalari, tanlangan poster, ring | **Faqat "Kuchli moslik" pill'i** (poster, film sahifasi, watchlist, hero) |
| `--red-dark` | Skip-link, tanlangan chip, onboarding belgisi | Ishlatilmaydi (token qoladi; F7 da kerak bo'lishi mumkin) |
| `--gold` | Match raqami, fokus konturi, input xatosi, eyebrow, katta baho raqami, slider | **Faqat ogohlantirish va xato** (input xatosi, "diqqat"). Match'dan olinadi |
| `--green` | Muvaffaqiyat | O'zgarmaydi: faqat "bajarildi" |

Kodda qizil ishlatilgan 11 joydan 10 tasi neytralga o'tadi (`app.css`: skip-link, faol nav,
`.btn-primary`, tanlangan chip, input fokus, kuchli trait bar, progress nuqtalari,
tanlangan poster va uning belgisi); ring qoladi. Oltin 11 joyda, match'ga tegishlilari
(`.match`, poster badge'i) qizilga, fokus konturi oqqa o'tadi.

**Tugmalar:** pill shaklida (to'liq radius). Oddiy tugmalar (watchlist, baho, ulashish) —
**neytral kontur**: shaffof fon, `--muted` chegara, oq matn; hover'da chegara `--text`
ga. Ekrandagi bitta asosiy amal (onboarding "Davom etish", kirish) — oq bilan to'ldirilgan
pill, qora matn, ekranda bittadan ko'p emas, glow yo'q (qaror 2).

**Chiplar:** yil, davomiylik, janr — neytral pill chip (`--surface-2` fon, `--muted`
matn). Tanlangan filtr chipi: oq fon, qora matn (qizil emas).

**Fokus:** 2px oq kontur (hozir oltin). Qora fonda eng yuqori kontrast.

Fayllar: `tokens.css` va `tokens.dart` (neytral qiymatlar), `app.css`. Ish: **0.5 kun.**

### 2. Ikonkalar — emoji butunlay olib tashlanadi

**Kutubxona: `lucide-react`** — versiya 1.49.0, litsenziya **ISC** (bepul, tijorat
uchun ham), `sideEffects: false` — bundle'ga faqat import qilingan ikonkalar kiradi.
`node_modules` dagi hajmi 35 MB (diskda, bundle'da emas). Bundle'ga ta'siri o'rnatilgandan
keyin o'lchanadi: hozir asosiy JS 604 KB. O'rnatishga ruxsat berildi (qaror 6).

Hozirgi emoji va belgilar (12 joy) va ularning o'rni:

| Joy | Hozir | lucide |
|---|---|---|
| Nav: Home / Search / DNA / Watchlist / Profil | 🏠 🔍 🧬 🔖 (avatar) | `House`, `Search`, `Dna`, `Bookmark`; Profil — harfli avatar qoldi (emoji emas, shaxsiy) |
| Film sahifasi: Baholash | ★ | `Gauge` — yulduz ishlatilmaydi (reytingimiz yulduz emas) |
| Film sahifasi: Saqlash | 🔖 | `Bookmark` / `BookmarkCheck` |
| Watchlist guruhlari | 🔥 ⏱ ✓ | `ListVideo`, `Timer`, `CircleCheck` |
| Onboarding: tanlangan poster | ✓ | `Check` |
| DNA: Ulashish | ↗ | `Share2` |
| Input xatosi | ⚠ (CSS) | `TriangleAlert` |
| Home bo'lim sarlavhalari (yangi) | — | For you `Sparkles`, Because you loved `Heart`, Under 90 `Timer`, Outside usual `Compass` |
| Hero (yangi) | — | `ChevronLeft/Right`, `Pause/Play`, `CircleHelp` ("Nega menga mos?") |

Ikonkalar neytral (`currentColor`), 20px, chiziq qalinligi 1.75. Bitta `Icon` o'rami
(`aria-hidden`, o'lcham) — har joyda bir xil. Qo'riqchi test: `src/` da emoji qolmasligi
(regex, CI'da).

Fayllar: `Layout.tsx`, `MoviePage.tsx`, `Watchlist.tsx`, `Onboarding.tsx`, `Dna.tsx`,
`app.css`, yangi `components/Icon.tsx`. Ish: **0.5 kun.**

### 3. Qobiq: navigatsiya va qidiruv

- **Navigatsiya:** hozirgi chap yon menyu qoladi (qaror 3), emoji o'rniga ikonkalar.
  Mobil'da pastki panel, ikonka + yorliq.
- **Qidiruv maydoni yuqori o'ngda:** dumaloq (pill), yorqin — `--text` fon, qora matn,
  `Search` ikonkasi. Qora fonda eng kuchli kontrast. Yozish `/search?q=` ga olib o'tadi.
  Mobil'da — yuqori panelda ikonka, bosilganda maydon ochiladi.
- **Sahifa o'tishlari:** 7-bo'lim.

Fayllar: `Layout.tsx`, `app.css`, `Search.tsx` (`q` ni URL'dan o'qish). Ish: **0.5–1 kun.**

### 4. Home

**4a. Hero** (2026-10-06 holati; 3-bosqich, `components/Hero.tsx`)

- **Nima:** "For you" ning birinchi 5 filmi, bittadan, karusel. **"For you" qatori
  6-filmdan boshlanadi** — hero'dagi filmlar takrorlanmaydi (Netflix, IVI kabi); 5 tadan
  kam bo'lsa qator ko'rsatilmaydi. 1440 birinchi ekranida qizil — 1 ta (hero kicker'i). Backdrop `.main` ning
  to'liq enida (w780 / w1280 `srcset`); backdrop yo'q — poster xira; ikkalasi ham yo'q —
  `--surface`. Scrim va gradientlar film sahifasidagi bilan bir xil.
- **Balandlik — qat'iy, minimal emas:** desktop (≥ 640) `clamp(360px, 56vh, 520px)`,
  mobil `max(280px, 48svh)`. 1440 × 900 da birinchi poster qatori ko'rinadi. Qat'iy
  bo'lgani uchun slayd almashganda pastdagi qatorlar surilmaydi; nom va jumla shuning
  uchun 2 qatorda to'xtaydi (to'liq matn film sahifasida).
- **Har slayd film sahifasining "Why you" bloki kabi o'qiladi:** tepada kicker (film
  sahifasidagi uslub: 19px uppercase) — "STRONG MATCH" qizil yoki neytral "YOU AND THIS
  FILM" ("good" ko'rsatilmaydi, TZ 1.16); keyin nom (Playfair, film sahifasiga havola),
  yil va davomiylik chiplari, ostida qisqa jumla.
- **Jumla:** tavsiyalar javobidagi keshlangan izoh; yo'q bo'lsa — film sahifasidagi
  bepul zaxira ("What you share with it: …", sabab yo'q bo'lsa "It suits your taste
  overall…"). **Hero LLM chaqirmaydi:** aylanish izoh so'rasa, har slayd pul va kunlik
  limit sarflardi.
- **Tugmalar,** ikkalasi neytral kontur: **"See why"** (uz "Nega mos", ru "Почему
  подходит") — film sahifasini ochadi; **Save**. Rate hero'da yo'q — u karta hover'ida va
  film sahifasida bor.
- **Aylanish:** har 7 s; sichqoncha yoki fokus ichida bo'lsa va Pause bosilsa to'xtaydi
  (WCAG 2.2.2). `prefers-reduced-motion` — o'zi aylanmaydi, faqat nuqtalar, ← → tugmalari
  va klaviatura; Pause tugmasi bu holatda yo'q. Boshqaruv hero ichida, pastki chap
  burchakda. Mobil'da (< 640) rasm hero chetigacha boradi (pastki gradient chetda
  `--bg` ning 85% i, to'liq emas) — boshqaruv rasm ustida turadi; doiralar 40px, bosish
  nishoni 44px. Nuqtalar: joriy — oq va kengroq, qolgani
  kulrang, har biri 24px nishon. Aylanayotganda `aria-live="off"`, to'xtaganda `polite`.
- **Unumdorlik:** birinchi backdrop `fetchpriority="high"` (LCP); qolganlari faqat
  navbati kelganda (ko'rsatilganlar va keyingisi).
- **API:** `backdrop_path` har `MovieOut` da (`schemas.py`, `types.ts` — `963404b`).

**4b. Poster qatorlari (Netflix/IVI tuzilmasi, NOXX ko'rinishi)**

- Bo'limlar hozir ham gorizontal qator — tuzilma qoladi. Sarlavha oldida neytral ikonka
  (2-bo'lim jadvali).
- Posterlar kattaroq: desktop ~180px eni, mobil'da ekranda 2.4 ta (keyingisining chekkasi
  scroll borligini bildiradi). Nisbat 2:3. Nom poster ostida, kichik, 2 qatorgacha.
- **Faqat "Kuchli moslik" badge'i** (qizil) posterda doim ko'rinadi; "Yaxshi moslik"
  kartada ko'rsatilmaydi (aks holda ~25 kulrang pill — o'sha shovqin), u film sahifasida
  va watchlist'da. Raqam yo'q (TZ 1.13).
- **Hover** (sichqoncha, `pointer: fine`): poster 1.08 ga kattalashadi va yumshoq soya oladi, ustida qorong'u
  qatlam va tez tugmalar — **Baholash** (mavjud baho dialogini ochadi) va **Watchlist**.
  Klaviatura: `:focus-within` da xuddi shu. Sensorli ekran: hover yo'q, bosish film
  sahifasini ochadi.

Fayllar: `Feed.tsx`, `MovieCard.tsx`, `Poster.tsx`, yangi `components/Hero.tsx`, `app.css`;
API: `schemas.py`, `types.ts`. Ish: hero **1.5–2 kun**, qatorlar va hover **1 kun.**

### 5. Film sahifasi

Hozir backdrop 200px balandlikda va 55% shaffoflikda — deyarli ko'rinmaydi.

- Backdrop **butun kenglikda hero**: desktop ~60vh (kamida 360px), mobil ~45vh, to'liq
  shaffofliksiz; gradient pastga va chapga `--bg` ga o'tadi.
- Poster hero'ning pastki chetiga ustma-ust tushadi; yonida nom (Playfair, katta),
  chiplar.
- "Why you" bloki tavsifdan yuqorida (v1 qoidasi qoladi). **Ring yo'q (TZ 1.13):**
  daraja — panelning sarlavhasi (kicker): "STRONG MATCH" qizil, qolgan hammasida va ta'm
  profili yo'q holatda neytral "YOU AND THIS FILM" ("good" ko'rsatilmaydi, TZ 1.16). Jumla uni
  davom ettiradi. "Why you?" yorlig'i yo'q (2026-10-05, pastda).
- Amallar: Baholash va Watchlist — neytral kontur pill; mobil'da pastda sticky.
- Pastki taqqoslash ("Other traits" / "Its strongest traits") neytral: film — oq, siz — kulrang (hozir
  qiymatga qarab qizil/oltin).
- Backdrop yo'q bo'lsa: posterning o'zi kattalashtirilib, xira (blur) fon sifatida.
- API o'zgarishi kerak emas: film sahifasida `backdrop_path` bor.

Fayllar: `MoviePage.tsx`, `Traits.tsx`, `app.css`. Ish: **1 kun.**

### 6. Movie DNA — imzo ekrani (Spotify Wrapped yo'nalishi)

**14 o'lchovni ko'rsatish usullari:**

| Usul | Baho |
|---|---|
| Progress barlar (hozir) | Aniq, lekin jadval kabi — imzo emas |
| Radar (ko'pburchak) | Rad: qo'shni o'qlar orasidagi chiziq bog'liq bo'lmagan o'lchovlarni bog'langandek ko'rsatadi; shakl o'qlar tartibiga bog'liq |
| Konstellyatsiya (yulduzlar) | Rad: chiroyli, lekin qiymatni o'qib bo'lmaydi |
| DNA spirali | Rad: tashqi effekt, ma'lumot o'qilmaydi |
| **Radial "DNA guli" — tavsiya** | Pastda |

**Tavsiya — radial "DNA guli":** markazdan 14 ta nur (gulbarg), har biri bitta o'lchov.

- **Uzunlik = qiymat** (0–100, chiziqli). Nurlar bir xil enli — to'ldirilgan sektor emas:
  sektor yuzasi radius kvadratiga qarab o'sadi va kuchli o'lchovni bo'rttirib yuboradi.
- **Har o'lchovning burchagi doimiy** (`traits.json` tartibida): har foydalanuvchida
  "Syujet burilishi" bir joyda. Shuning uchun gul shakli — barmoq izidek: ikki odamning
  DNA'sini bir qarashda solishtirsa bo'ladi, ulashishga arziydi.
- Eng kuchli 3 ta nur — to'liq oq va yorlig'i yirik; qolganlari qiymatiga qarab xiraroq.
- **Nega shunday:** (1) har foydalanuvchida o'ziga xos siluet — Wrapped'dagi "bu men"
  hissi; (2) 14 tasi birdaniga, ro'yxatsiz ko'rinadi; (3) tabiiy animatsiya — nurlar
  markazdan ketma-ket o'sib chiqadi; (4) halol — uzunlik chiziqli, raqamni qo'lda
  tekshirsa bo'ladi.
- Kutubxona kerak emas: qo'lda yozilgan SVG (14 ta `path`).

**Rang:** DNA match emas, shuning uchun 1-bo'lim qoidasiga ko'ra **qizil yo'q** —
monoxrom (qaror 1): qora fonda oq nurlar, lekin **yassi oq emas** — har nurning
yorqinligi qiymatiga qarab o'zgaradi. Ekranning kuchi harakat va yirik tipografikadan.

> **2026-10-06:** 4-bosqichda faqat radial gul quriladi. Quyidagi Wrapped tuzilmasi va
> ulashish rasmi TZ backlog'iga ko'chdi — tavsif keyinga saqlanadi.

**Wrapped tuzilmasi:** sahifa vertikal "hikoya" bloklari, har biri scroll'da paydo bo'ladi:
1. "Siz N ta film baholadingiz" — raqam sanalib chiqadi.
2. "Eng kuchli tomoningiz: {trait}" — juda yirik matn.
3. DNA guli ochiladi (nurlar ketma-ket o'sadi).
4. Bir jumlalik xulosa (Playfair, kursiv).
5. Statistika: o'rtacha baho, eng ko'p janr.
6. Ulashish.

**Ulashish rasmi:** brauzerda yasaladi — xuddi shu SVG + sarlavha + top-3 + ilova nomi
`canvas` ga chiziladi (1080×1920, story formati), PNG; qo'llansa `navigator.share` (fayl
bilan), aks holda yuklab olish. Server ham, ommaviy havola ham kerak emas, maxfiylik
savoli yo'q — rasm foydalanuvchi o'zi ulashmaguncha qurilmadan chiqmaydi. TMDB rasmlari
ishlatilmaydi. Shriftlar yuklangach chiziladi (`document.fonts.ready`). Server varianti
FR-7 backlog'ida link preview uchun qoladi (qaror 4).

**Qulaylik:** SVG `role="img"` va xulosa `aria-label`; 14 ta qiymatning matnli ro'yxati
("Raqamlar" tugmasi) — ekran o'quvchi va aniq qiymat kerak bo'lganlar uchun.

API o'zgarishi kerak emas (`/me/dna` ballarni, sonni, o'rtacha bahoni, janrni beradi).

Fayllar: `Dna.tsx`, yangi `components/DnaFlower.tsx`, `lib/shareImage.ts`, `app.css`.
Ish: **2–3 kun** (testlari bilan).

### 7. Harakat

| Joy | Harakat | Davomiyligi |
|---|---|---|
| Sahifa o'tishlari | Yangi sahifa paydo bo'ladi: faqat opacity, ease-out. Yon menyu, yuqori panel va qidiruv qatori qimirlamaydi (2026-10-09, quyida) | 120 ms |
| Poster hover va fokus | `transform: scale(1.03)` + qatlam paydo bo'lishi; kirish ease-out, chiqish ease-in; soya animatsiyasiz; fokus halqasi kechikmaydi | 120 ms |
| Skeleton → kontent | Kontent skeleton o'rnida paydo bo'ladi (opacity); keshdan kelsa — animatsiyasiz | 160 ms |
| Baholash dialogi | Ochilish: fon fade + varaq 0.96 → 1 (ease-out). Yopilish: teskari (ease-in), dialog shundan keyin yopiladi | 160 / 120 ms |
| Onboarding qadamlari | Yon siljish 24px + opacity: oldinga o'ngdan, orqaga chapdan; pastki panel qimirlamaydi | 200 ms |
| Xato va xabar bannerlari | Fade + 8px: offline banner va maydon xatosi yuqoridan, toast pastdan | 160 ms |
| DNA guli | Nurlar markazdan ketma-ket o'sadi | 40 ms oraliq, jami ~900 ms |
| Hero | Slaydlar crossfade | 400 ms |

Qoidalar: faqat `transform` va `opacity` (layout emas); har animatsiya element birinchi
paydo bo'lganda bir marta, har qayta chizishda emas. Kirish ease-out, chiqish ease-in, hech
biri 200 ms dan uzun emas (DNA guli va hero bundan mustasno — ular o'z bo'limlarida).

**Tuzatish (2026-10-09): avvalgi "Sahifa o'tishlari — View Transitions, 200–250 ms" yozuvi
noto'g'ri edi.** Ilova `BrowserRouter` ishlatadi; React Router 7.18 da `viewTransition`
faqat data router'da (`createBrowserRouter` + `RouterProvider`) ishlaydi —
`BrowserRouter` da prop jimgina e'tiborsiz qoladi (manba kodida tekshirildi: 
`startViewTransition` faqat `RouterProvider` ichida). Haqiqiy Chrome'da navigatsiyada
bironta o'tish animatsiyasi yo'q edi. Ishlamaydigan `viewTransition` proplari va
`::view-transition-*` CSS olib tashlandi, o'rniga yuqoridagi 120 ms paydo bo'lish.
To'liq o'tish (eski sahifa so'nib, yangisi 8px ko'tarilib) — backlog (TZ, 2-bo'lim).

**`prefers-reduced-motion`:** CSS'da global qoida bor (`app.css`, barcha animatsiya va
transition o'chadi). Lekin JS animatsiyalari (sanash, hero aylanishi, DNA ketma-ketligi) uni
ko'rmaydi — ular uchun `usePrefersReducedMotion` hook: harakat o'rniga darhol oxirgi holat,
hero avtomatik aylanmaydi. Testi: reduced-motion holatida darhol oxirgi raqam chiqadi.

Kutubxona kerak emas (framer-motion/motion o'rnatilmaydi): CSS va ~40 qatorli hook yetadi.

Ish: tegishli ekran bilan birga; umumiy qism (hook'lar, o'tishlar) **0.5 kun.**

### 8. Yangi kutubxonalar

| Nomi | Nima uchun | Litsenziya | Hajmi |
|---|---|---|---|
| `lucide-react` 1.49.0 | Ikonkalar | ISC, bepul | Diskda 35 MB; bundle'ga faqat ishlatilgan ikonkalar (o'rnatilgach o'lchanadi) |

Boshqa hech narsa: animatsiya, grafik va rasm — qo'lda (CSS, SVG, canvas).

### 9. Tartib — ekran-ekran

Har qadam: alohida commit(lar), to'rt holat testlari saqlanadi, axe 0 buzilish, 320px da
gorizontal scroll yo'q, reduced-motion tekshiruvi, keyin **skrinshot sizga** — tasdiqdan
keyingina keyingi qadam.

| # | Qadam | Ish |
|---|---|---|
| 0 | Poydevor: rang qoidasi, `lucide-react` (ruxsat bilan), emoji olib tashlash, qobiq (yon menyu ikonkalari, qidiruv maydoni), umumiy harakat hook'lari | 1.5–2 kun. **Bajarildi** (2026-10-02), tasdiqlandi |
| 1 | Film sahifasi (backdrop hero) | 1 kun. **Bajarildi va tasdiqlandi** (2026-10-04) |
| 2 | Home: poster qatorlari va hover | 1 kun. **Bajarildi** (2026-10-04), tasdiqlandi |
| 3 | Home: hero (`backdrop_path` API'ga) | 1.5–2 kun. **Bajarildi** (2026-10-06), tasdiqlandi |
| 4 | Movie DNA: faqat radial gul (2026-10-06 dan; Wrapped tuzilmasi va ulashish rasmi — TZ backlog) | 1 kun. **Bajarildi** (2026-10-06), tasdiqlandi |
| 5 | Qolgan ekranlar yangi qoidalarga: Search (poster to'ri), Watchlist, Onboarding, Profile, Welcome | 1 kun. **Bajarildi** (2026-10-06; Welcome ko'rib chiqilmadi — brifda yo'q edi), tasdiqlandi |

**Dizayn v2 yopildi** (2026-10-06): olti bosqichning hammasi bajarildi va foydalanuvchi
tomonidan tasdiqlandi.

Jami taxminan **8–10 kun.** Film sahifasi birinchi: eng kichik va eng ko'rinadigan
o'zgarish (backdrop hozir eng katta isrof) — yangi qoidalarni bitta ekranda sinab
ko'ramiz.

### 0-bosqich natijasi (2026-10-02)

- Neytral tokenlar (R = G = B, yorqinlik avvalgidek, kontrastlar o'zgarmadi), web va Dart.
- Qizil faqat match'da: poster badge'i (qizil fon, qora matn, 4.8:1), ring, `.match`.
  Qolgan 10 joy neytral. Oltin — faqat ogohlantirish va xato.
- Tugmalar pill; asosiy amal — oq to'ldirilgan; qolganlari kontur. Film sahifasidagi
  "Baholash" endi kontur (avval qizil to'ldirilgan edi).
- `lucide-react` 1.49.0, `Icon` o'rami; 12 ta emoji/belgi olib tashlandi; `noEmoji.test.ts`
  barcha manba va CSS fayllarni tekshiradi.
- Qidiruv pill'i yuqori o'ngda (≥ 640px), `/search?q=` ga olib boradi; qidiruv ekranida
  yashirinadi.
- Sahifa o'tishlari (`viewTransition`), ring raqami sanalib chiqadi (`useCountUp`),
  `usePrefersReducedMotion` (matchMedia bo'lmasa — harakatsiz).
- Bundle (o'lchangan): JS 604.24 → 616.66 kB (gzip 175.86 → 179.51), CSS 17.29 → 18.13 kB.
- Testlar: 15 fayl, 166 test (avval 117); lint 0; build 0. 390px va 320px da
  `scrollWidth` = ekran eni (gorizontal scroll yo'q).

### 1-bosqich natijasi (2026-10-04)

- **Hero:** backdrop `.main` ning to'liq enida (`container-type: inline-size`, `100cqw`),
  desktop `max(360px, 60vh)`, mobil `max(240px, 45svh)`, shaffofliksiz; gradient pastga
  va chapga `--bg` ga. Desktop'da qidiruv qatori ostiga ham kiradi. `srcset` w780/w1280,
  `fetchpriority="high"`. Backdrop yo'q — poster xira fon; ikkalasi ham yo'q — `--surface`.
- **Sarlavha:** poster hero chetidan chiqib turadi (desktop 200px, mobil 112px); nom
  Playfair 52px / 28px; yil, davomiylik, janrlar — neytral chiplar.
- **"Why you" — bitta panel:** ring, jumla va 3 tagacha sabab bitta grid'da; bo'shliq
  ritmi: qismlar orasida `--space-4`, qism ichida `--space-2`. Jumla Playfair 700, oq,
  30px (≥ 1100px), 26px (640–1099), 22px (mobil). Joylashuv: ≥ 1100 — ring | jumla |
  o'qlar; 640–1099 — ring, yonida jumla va ostida o'qlar; mobil — ring + sarlavha, ostida
  jumla, o'qlar.
- **Sabablar o'qda:** har trait bitta 0–100 o'qda, siz — kulrang nuqta, film — oq nuqta,
  orasi chiziq; ikkala raqam ham yozilgan, ekran o'quvchiga so'z bilan ("you 88, film 34").
  Ta'm hali yuklanmagan bo'lsa, sizning nuqtangiz 0 da chizilmaydi — keyin paydo bo'ladi.
  Qizil yo'q. "Sizning ta'mingiz va shu film" ham shu o'qlarga o'tdi va panelda
  ko'rsatilgan sabablarni takrorlamaydi (filmning qolgan eng kuchli 5 trait'i).
- **Sabab yo'q holat:** "suits you overall" jumlasi xuddi shu slot'da, shu o'lchamda; o'qlar
  qismi yo'q, ustunlar o'sha (jumla bir xil enda o'raladi). API sababsiz izoh yozmaydi
  (`explain.py`), shuning uchun bu holatda izoh so'ralmaydi — skeleton ham, siljish ham yo'q.
- **Skeleton:** jumla slot'ining balandligi oldindan band (`min-height`: mobil 4, 640–1099
  da 3 qator; ≥ 1100 da o'qlar ustuni balandroq); matn 200 ms da paydo bo'ladi.
- **Reduced motion:** CSS qoidasidan tashqari JS ham: fade klassi qo'yilmaydi, ring va
  raqam birinchi kadrdanoq oxirgi qiymatda, `requestAnimationFrame` chaqirilmaydi (test).
- **Tuzatilgan xato (0-bosqichdan):** `useCountUp` birinchi kadrda manfiy son ko'rsatardi
  (Chrome'da "-8%" ko'rindi): rAF vaqt belgisi `performance.now()` dan oldin bo'lishi
  mumkin. Progress endi 0 dan pastga tushmaydi; testi bor.
- **Layout shift (o'lchangan, headless Chrome, CDP, `layout-shift` PerformanceObserver,
  mock API: film 250 ms, izoh +900 ms):** desktop 1440×900 — CLS 0.000007–0.000037
  (o'rtacha, 2 jumlali, izohsiz, sababsiz, backdrop'siz); 1024 — 0.000042; 390×844 —
  0.000000–0.000028; 320 — 0.000016. Yagona sezilarli holat: 390px da 2 jumlali uzun
  izoh (6 qator, 4 qator band) — **0.0038**. "Yaxshi" chegarasi 0.1. Qolgan mayda
  siljishlar: ring raqami sanalganda eni o'zgaradi, ta'm yuklanganda "–" raqamga almashadi.
- axe 4.10.2: 0 buzilish (1440, sababsiz holat, 390, 320). 320px va 390px: `scrollWidth`
  = ekran eni. Qizil faqat ring'da (sahifadagi barcha elementlarning hisoblangan rangi
  tekshirildi).
- Testlar: 15 fayl, 176 test (avval 166); lint 0; build 0. Bundle: JS 618.93 kB (gzip
  180.09), CSS 21.37 kB. Mock'dagi TMDB path'lari (`src/dev/images.ts`) bundle'ga kirmaydi
  (tekshirildi).

### 1-bosqich, ko'rikdan keyingi tuzatishlar (2026-10-04)

Foydalanuvchi ko'rigi: yo'nalish to'g'ri, "Why you" hali bitta kompozitsiya emas — 7 band.
Yuqoridagi natijalardan farqi:

1. **Sabab yo'q — panel qisqaradi.** Joy faqat matn kelishi mumkin bo'lganda band
   qilinadi (`.why-reserve`); sababsiz holatda o'qlar ustuni ham, band joy ham yo'q.
   Desktop'da panel 186 → 160px (ring balandligi + padding).
2. **Vertikal markaz, o'qlar 40%.** ≥ 1100: ring | jumla | o'qlar, uchalasining markazi
   bitta chiziqda (o'lchangan: 129/129/129px). O'qlar ustuni — panel kontent enining 40%.
   Panel balandligi = eng baland ustun + padding. Joy endi sarlavha + jumla blokiga band
   qilinadi (25px + 4 qator) va ular birga markazlanadi.
3. **Raqam o'z nuqtasida:** siz — nuqta ustida, film — ostida, nuqta bilan bitta vertikalda;
   0/100 ga yaqin bo'lsa yarim eniga ichkariga suriladi (`clamp(12px, x, 100% - 12px)`).
4. **Yaqin qiymatlar:** nuqtalar markazlari orasi kamida 20px (`DOT_GAP`). Sof CSS:
   `min()/max()/clamp()` piksel bo'yicha hisoblaydi, o'q eni qanday bo'lmasin. Aniq qiymat
   raqamda, `aria-label` da va `title` da. O'lchangan: Mystery 84/80, Visual style va
   Pace — 20px; uzoqlari haqiqiy joyida.
5. **Shakl, rang emas:** siz — to'liq oq doira, film — ichi bo'sh oq doira. Legend sahifada
   bitta: "Why you" da o'qlar bo'lsa o'sha yerda, aks holda taqqoslash bo'limida.
6. **Raqam shrifti:** o'q raqamlari Inter, `tabular-nums`, chizilgan nol yo'q (JetBrains
   Mono'ning noli chizilgan edi). Ring: yashirin yakuniy qiymat qutining enini belgilaydi,
   sanoq uning ichida — quti sanoq paytida o'zgarmaydi.
7. **Hero va amallar:** desktop hero `clamp(360px, 60vh, 440px)` (1440×900 da 440px;
   mobil o'zgarmagan). Rate / Save ≥ 640 da sarlavha va chiplar ostida, sahifa oqimida,
   sticky emas; mobil'da pastki menyu ustida qotgan. 1440×900 da "Why you" butunlay
   birinchi ekranda.

Topilgan va tuzatilgan: skeleton chiziqlarining margin'lari qo'shilib ketgani uchun
skeleton 3 qator o'rniga 96px edi (matn 117px) — avval slot'ning `min-height` i buni
yashirgan. Endi chiziqlar flex ustunda.

**CLS (qayta o'lchangan, o'sha usul):**

| Holat | 1440×900 | 1024 | 390×844 | 320 |
|---|---|---|---|---|
| O'rtacha izoh (3 sabab) | 0.000011 | 0.000041 | 0.000000 | 0.000015 |
| Izohsiz (fallback, 2 qator) | **0.000721** | — | 0.000000 | — |
| 2 jumlali uzun izoh | **0.007463** | — | **0.0038** | — |
| Sabab yo'q | 0.000007 | 0.000043 | 0.000013 | — |
| 1 sabab | 0.000010 | — | 0.000010 | — |
| Backdrop'siz | 0.000014 | — | — | — |
| Reduced motion | 0.000001 | — | 0.000000 | — |

Sabab yo'q holatda panel qisqargani siljish keltirmadi: sabablar soni film bilan birga
keladi. Ikki narx: (a) desktop'da qisqa fallback — sarlavha + jumla birga markazlangani
uchun ~10px suriladi (0.0007); (b) uzun izoh endi tor ustunda 6 qator, band qilingan 4
qatordan oshadi va panel o'sadi (0.0075, avval 0.00004). Ikkalasi ham "yaxshi" chegarasi
0.1 dan ancha past. Qolgan mayda manbalar: ring sanog'i (quti emas, matn), ta'm
yuklanganda film nuqtasining 20px qoidasi bo'yicha surilishi.

axe 4.10.2: 0 buzilish (1440, sababsiz, 390, 390 sababsiz, 320). `scrollWidth` = ekran
eni (320, 390). Qizil faqat ring'da. Testlar: 15 fayl, 180 test; lint 0; build 0.

### 1-bosqich tasdiqlandi; yakuniy to'rt ish (2026-10-04)

1. **Ustunlar:** Overview va rejissyor/aktyorlar bitta to'liq enli qatorda (tavsif
   `max-width: 65ch`, ro'yxat o'ngda); taqqoslash to'liq enda, o'qlar 3 + 3 (≥ 900px),
   endi 6 trait. "Back" havolasi olib tashlandi.
2. **Mobil o'q:** trait nomi o'q ustida, o'q kartaning to'liq enida (< 640px). 390px da
   20px surilishi kerak bo'lgan juftliklar: Visual style 69/62 va Pace 55/48 endi haqiqiy
   joyida (22px); Mystery 84/80 hali suriladi (4 ball ≈ 13px).
3. **Mobil "Why you":** eyebrow tepada to'liq enda; ring chapda, jumla uning doirasi
   atrofida o'raladi (`float` + `shape-outside: circle()`), keyin to'liq enga chiqadi.
4. **Hero scrim:** butun backdrop ustida `--bg` ning 25% i (≈ rgba(0, 0, 0, .25)), pastki
   va chap gradientlar ostida. O'lchangan o'rtacha yorqinlik (0–255, oq qidiruv
   pikselisiz), oldin → keyin: The Prestige o'ng-yuqori 100.4 → 78.0, qidiruv atrofi
   105.0 → 83.4; Prisoners o'ng-yuqori 77.5 → 61.0, butun hero 37.5 → 31.6. Bir tekis scrim
   har pikselni bir xil ulushga qoraytiradi: yorqin joy ko'p, qorong'i joy kam o'zgaradi.

CLS (o'sha usul): desktop o'zgarmadi (0.000013 o'rtacha, 0.0007 qisqa fallback, 0.0075
uzun). Mobil: o'rtacha izoh 390px da 0.000000; o'ralish tufayli qatorlar ko'paydi — uzun
izoh 390px da **0.0154** (avval 0.0038), 320px da o'rtacha izoh **0.0071** (avval
0.000016). Band qilingan joy 4 qator qoldi: 5 qatorda 390px dagi o'rtacha izoh ostida bo'sh
qator qolardi. axe 0 (1440, 390, 320). Testlar: 15 fayl, 181; lint 0; build 0.

### 2-bosqich natijasi (2026-10-04)

- **Qatorlar** har ekranda gorizontal (avval ≥ 640px da to'r edi). Poster eni desktop'da
  180px (1440 da ekranda 5.9 ta), mobil'da ekranga 2.4 ta (o'lchangan: 390 da 2.45, 320 da
  2.47); keyingi posterning cheti qator davom etishini ko'rsatadi. Nisbat 2:3, nom 2
  qatorgacha.
- **Sarlavha ikonkalari** (neytral, `--muted`): For you `Sparkles`, Because you loved
  `Heart`, Under 90 `Timer`, Outside usual `Compass`.
- **Match badge** har kartada doim ko'rinadi (qizil; sahifadagi yagona qizil).
- **Hover** (`hover: hover` va `pointer: fine`) yoki klaviatura fokusi (`:focus-within`,
  har qurilmada): poster va qatlam birga `scale(1.05)`, pastdan ko'tariluvchi qorong'u
  qatlam (92% → 70% → shaffof; badge ochiq qoladi) va ikkita kontur ikonka-tugma:
  **Baholash** (film sahifasidagi o'sha dialog, `components/RateDialog.tsx` ga ko'chirildi;
  joriy baho bilan ochiladi) va **Watchlist** (`aria-pressed`, darhol, xatoda qaytadi va
  xabar chiqadi). Tugmalar havola ichida emas, yonida. Sensorli ekranda hover yo'q:
  bosish film sahifasini ochadi. Faqat `transform` va `opacity`, 200 ms.
- **Qo'shimcha (brifda yo'q):** desktop'da ←/→ tugmalari — qator sig'masa chiqadi, chetda
  yashirinadi, qatorni 80% eniga suradi (reduced motion'da sakrab). Sabab: gorizontal
  qatorda sichqonchali foydalanuvchi aks holda 7-filmdan keyingisiga yetolmaydi.
  Sensorli ekranda va < 640px da ko'rinmaydi.
- Mock: "For you" 12 ta film (qator to'lib, tugmalar ko'rinsin); faqat dev.
- **O'lchovlar:** CLS 0.000000 (1440, 1440 reduced motion, 1024, 390, 320). axe 4.10.2:
  0 buzilish (1440, 390, 320). `scrollWidth` = ekran eni. Testlar: 15 fayl, 189; lint 0;
  build 0. Bundle: JS 624.01 kB (gzip 181.54), CSS 24.31 kB.
- **Testlar haqida:** kompyuter band bo'lganda (fonda dev server va headless Chrome)
  Onboarding'ning bir nechta testi 1–5 s chegarasiga yetib yiqilgan (har safar boshqasi);
  server to'xtatilgach ikki marta alohida va bir marta to'liq run'da hammasi o'tdi.
  Onboarding bu bosqichda o'zgarmagan. Kuzatiladi.

### 2-bosqich, ko'rikdan keyingi tuzatishlar (2026-10-05)

Foydalanuvchi ko'rigi: beshta tuzatish, 3-bosqichdan oldin. Yuqoridagi natijalardan farqi:

1. **Mobil "Why you" — float yo'q.** Eyebrow tepada to'liq enda, ostida ring o'z qatorida
   chapda, keyin jumla toza, chapga tekislangan blok, keyin o'qlar (< 640px: bitta ustunli
   grid, qatorlar orasi `--space-3`, o'qlardan oldin `--space-4`). `float` va
   `shape-outside` olib tashlandi: qatorlar soni endi faqat panel eniga bog'liq.
2. **Hero scrim tepadan gradient:** `--bg` ning 45% i (≈ rgba(0, 0, 0, .45)) tepada,
   balandlikning 45% ida shaffof. Bir tekis 25% li qatlam olib tashlandi.
3. **Legend o'qlar ustunida:** legend endi bo'sh nom katagi bor `axis-row` — birinchi o'q
   ustida, o'q chizig'i bilan bir vertikalda boshlanadi (o'lchangan: farq 0px; 1440, 1024,
   390, 320, taqqoslash bo'limida ham). Mobil'da nom o'q ustida bo'lgani uchun bo'sh katak
   yashirin.
4. **Home hover kuchliroq:** poster va qatlam `scale(1.08)` (avval 1.05), poster ostida
   yumshoq soya, ko'tarilgan karta qo'shnilari ustida chiziladi (`z-index: 2`). Tez
   tugmalar 44 → 52px, ikonka 20 → 24px. Qator padding'i 8/6 → 12/8px (180 × 270 poster
   8% da yon tomonga 7.2px, tepaga 10.8px o'sadi; scroll qatori padding'dan chiqqanini
   kesadi). Nom va yil soyadan yuqorida (`z-index: 3`, har sticky panel ≥ 10 dan past) —
   aks holda soya o'z nomini ham, qo'shnining nomini ham xiralashtirardi (skrinshotda
   ko'rindi, tuzatildi).
5. **Onboarding testlarining beqarorligi** — sabab topildi, pastda.

Qo'shimcha topilgan (brifda yo'q): 1024px da film sahifasi gorizontal scroll berardi
(`scrollWidth` 1030): Overview qatoridagi rejissyor/aktyorlar ustuni 65ch matndan keyin
qolgan joyga siqilib, "Christopher Nolan" sig'mas edi (1-bosqich yakuniy ishidan,
`3c8f2a0`). Endi ustun kamida 14em, matn ustuni torayadi; 1024 da `scrollWidth` = 1024.

**CLS (o'sha usul: headless Chrome, CDP, mock API film 250 ms, izoh +900 ms):**

| Holat | Float bilan (oldin) | Float'siz (hozir) | Float'dan ham oldin |
|---|---|---|---|
| 390, uzun izoh (6 qator, 4 band) | 0.0154 | **0.0024** | 0.0038 |
| 390, o'rtacha izoh | 0.000009 | 0.000014 | 0.000000 |
| 320, o'rtacha izoh (5 qator) | 0.0049 (hujjatda 0.0071) | **0.000019** | 0.000016 |
| 320, uzun izoh (8 qator) | 0.0146 | 0.000000 | — |
| 390, uzun, reduced motion | — | 0.0024 | — |
| 1440 o'rtacha / 1024 | 0.000006 / — | 0.000010 / 0.000016 | — |

"Oldin" ustuni shu kod bilan shu sessiyada qayta o'lchangan (390 uzun 0.0154 hujjatdagi
bilan bir xil chiqdi). 320 × 640 da uzun izoh ostidagi o'qlar ekrandan tashqarida, shuning
uchun ularning siljishi CLS'ga kirmaydi.

**Hero yorqinligi** (o'rtacha yorqinlik 0–255, Rec. 709, oq qidiruv pikselisiz; 1440 × 900,
hero 440px, 45% = 198px):

| Mintaqa | Scrim yo'q | Tekis 25% | Tepadan gradient |
|---|---|---|---|
| Prestige — qidiruv atrofi (y 0–80) | 105.0 | 83.0 | **74.0** |
| Prestige — tepa 45% | 46.9 | 37.6 | 39.8 |
| Prestige — 45% dan past | 32.6 | 28.0 | **32.6** |
| Prisoners — qidiruv atrofi | 72.0 | 58.2 | **52.9** |
| Prisoners — tepa 45% | 41.6 | 33.7 | 35.9 |
| Prisoners — 45% dan past | 34.3 | 29.5 | **34.3** |

Qidiruv atrofi tekis scrim'dagidan ham qorong'iroq; o'rta va past qism scrim'siz holat
bilan aynan bir xil (gradient u yerga yetmaydi). Tepa 45% o'rtacha biroz yorug'roq, chunki
gradient pastga qarab kamayadi — qidiruv turgan eng yuqori qism esa eng qorong'i.

**Hover soyasi:** fon deyarli qora (#0a0a0a), shuning uchun soya fonda ko'rinmaydi (poster
ostidagi bo'sh joy 10 → 10). Ko'tarilish qo'shni poster ustida ko'rinadi: Memento'ning chap
30px i hover'da 116.5 → 101. Nomlar o'zgarmaydi (Memento 49.7 → 49.7, Prestige 53.3 → 53.6).

**Onboarding testlari — sabab (o'lchangan):**

- **Kutish shartlari aniq** (`findByRole`/`findByText`, aniq rol va nom bilan) — bo'sh
  mashinada birinchi tekshiruvdayoq bajariladi. Har qadam CPU ishi: tile grid'idagi
  `*ByRole` so'rovi 15–60 ms, `userEvent.click` ~50 ms. 10 dan ko'p tap qiladigan test
  (9 + 10 tanlash) bo'sh mashinada 1.9 s — 5 s chegarasigacha atigi 2.6 baravar zaxira.
- **Ishchi vaqti-vaqti bilan to'xtab qoladi:** 10 ms lag-monitor bo'sh mashinada 150–630 ms
  bloklarni ko'rsatdi; sun'iy CPU yuki ostida bitta click 2.2 s, bitta `findByRole` 1.7 s.
  Bir run'da `findByText` ning 1000 ms taymeri **1373 ms kech** otildi, mock javob esa
  allaqachon tayyor edi. Kutubxonada (`@testing-library/dom` `waitFor`) muddat tugaganda
  oxirgi tekshiruv qilinmaydi: kechikkan taymer navbatdagi render'dan oldin yutadi.
- **"Har safar boshqa joyda" sababi:** Vitest muddati o'tgan testni to'xtatmaydi. Uning
  qolgan `pick()` taplari global `screen` orqali **keyingi testning** DOM'ida ishlagan
  (log'da: "unpicks" testi ichida oldingi testning "The Machinist", "Enemy" taplari) —
  keyingi testlar o'zlariga tegishli bo'lmagan sabab bilan yiqilgan.
- **Yuk ostida topilgan to'rtinchi sabab — ilova kodida:** baholash qadami har film uchun
  bahoni `useEffect` da 7 ga qaytarardi. Effekt birinchi chizishdan keyin ishlaydi; test
  shu oraliqda 9.5 qo'ysa, effekt uni 7 ga qaytarardi. Brauzerda oraliq bitta kadr, lekin
  bu haqiqiy poyga.

Tuzatish: (1) chegara testlari tanlovlarning 8 tasini `saveProgress` bilan tayyor qo'yadi
va faqat chegarani kesib o'tadigan taplarni qiladi (19 tap → 2; "baholanganlar ham
sanaladi" testi 6 → 2); (2) `pick()` testning `signal` ini tekshiradi — muddati o'tgan
test endi boshqa testning ekraniga tegmaydi; (3) `asyncUtilTimeout` 1000 → 3000 ms
(`src/test/setup.ts`, sabab izohda) — sekinlik yuqorida isbotlangan, o'tadigan kutish
shart bajarilishi bilan qaytadi; (4) baholash qadami film bo'yicha `key` oladi, effekt
olib tashlandi; keyingi film standart baho bilan boshlanishi testga qo'shildi.

Natija: tuzatishdan oldin sun'iy yuk ostida (ikkita band CPU yadro, 2 yadroli mashina)
Onboarding fayli 5 run'dan 2 tasida yiqildi; keyin 8 / 8 yashil, bo'sh holatda 2 / 2.
To'liq web to'plami yuk ostida 3 / 3 yashil (189 test, ~90 s), dev server fonda ishlab
turganda 2 / 2.

axe 4.10.2: 0 buzilish (1440, 1024, 390, 320 film; 1440, 390 Home). `scrollWidth` = ekran
eni (1440, 1024, 390, 320; Home ham). Qizil: film sahifasida faqat ring, Home'da faqat
badge'lar. Testlar: 15 fayl, 189; lint 0; build 0. Bundle: JS 624.11 kB (gzip 181.53),
CSS 24.81 kB.

### Match darajasi (TZ 1.13, 2026-10-05)

Foiz interfeysdan olindi; o'rnida daraja pill'i (`components/MatchBand.tsx`). Qaror asosi:
`docs/STATUS.md`, "FR-5 o'lchovi".

- **Home:** posterda faqat "Strong match" (qizil, `.badge`). "Good match" kartada yo'q.
- **Film sahifasi:** ring olib tashlandi (`MatchRing`, `useCountUp` va ularning testlari
  bilan). "Why you" sarlavhasi qatorida pill: kuchli — qizil, yaxshi — neytral (`--surface-2`,
  `--line` chegara), aks holda hech narsa. Sarlavha qatori har holatda 26px — pill bor-yo'qligi
  jumlani surmaydi. ≥ 1100: jumla | o'qlar (40%); undan tor — ustma-ust.
- **Watchlist:** `NN%` o'rnida o'sha pill.
- **Matnlar:** "Strong match" / "Good match"; uz "Kuchli moslik" / "Yaxshi moslik"; ru
  (qoralama) "Очень близко" / "Близко" — "Сильное совпадение" 112px posterga sig'masdi.
  Feed bo'sh holati endi "60%" demaydi.

**O'lchovlar** (headless Chrome, mock API, o'sha usul):

| | Natija |
|---|---|
| Home qizil (1440 birinchi ekran / 390 / 320) | 2 / 2 / 2 (mock: "For you" ning 2 tasi kuchli) |
| Posterdagi badge eni, 112px poster (320) | en 88px, uz 88px, ru 92px — sig'adi |
| Sahifada `NN%` ko'rinishi | yo'q (film 1440/1024/390/320, Home, Watchlist) |
| CLS film, o'rtacha izoh | 1440 0.000001, 1024 0, 390 0, 320 0 |
| CLS film, 390 uzun izoh (6 qator, 4 band) | **0.0073** (ring bilan 0.0024): ring qatori ketgach o'qlar ekranga ko'tarildi va o'sha siljish endi ko'rinadigan joyda. "Yaxshi" chegarasi 0.1 |
| CLS Home / Watchlist | 0 / 0 |
| axe 4.10.2 | 0 (film 1440 kuchli va yaxshi, 1024, 390, 320; Home 1440, 390; Watchlist 390) |
| `scrollWidth` | ekran eni (hamma holatda) |

Testlar: 15 fayl, 189 (ring va sanoq testlari o'rniga daraja testlari: kuchli/yaxshi/yo'q,
Feed'da raqam yo'qligi, Watchlist). Bundle: JS 623.03 kB (gzip 181.23), CSS 23.51 kB.

### Film sahifasi: daraja — panel sarlavhasi (2026-10-05)

Foydalanuvchi ko'rigi: ring ketgach film sahifasi vizual markazini yo'qotdi. To'rt
tuzatish:

1. **"WHY YOU?" eyebrow'i va kichik pill o'rniga — darajaning o'zi sarlavha.** `h2.why-kicker`:
   Inter 800, uppercase, `letter-spacing .1em`, **19px**. Kuchli — `--red`, yaxshi —
   `--text`, darajasiz — `--muted`. Blok bitta gap bo'lib o'qiladi: "STRONG MATCH" →
   "It keeps you guessing…". Bo'limning nomi (`aria-labelledby`) — shu sarlavha.
   **Nega 19px, 14–16 emas:** qizil `--surface` (panel foni) ustida 4.37:1 — 4.5 dan
   past, kichik matn uchun AA dan o'tmaydi. 19px bold — WCAG bo'yicha "katta matn"
   (14pt bold = 18.67px), unga 3:1 yetadi. Uchala holat bir xil o'lchamda: jumla har
   doim bir joydan boshlanadi.
2. **Darajasiz holat ham ishlaydi:** neytral kicker "YOU AND THIS FILM" (uz "SIZ VA BU
   FILM", ru "ВЫ И ЭТОТ ФИЛЬМ"; foydalanuvchi tasdiqlagan). U moslik va'da qilmaydi —
   darajasiz filmlar o'rtacha yoki past moslikda. Ta'm profili yo'q holat (`match ===
   null`) ham shu kicker bilan.
3. **0 yoki 1 sabab — bir ustun (`.why-solo`), panel kontent balandligida.** O'q va
   legend jumla ostiga tushdi, o'q eni jumla eni bilan bir xil (720px). Sabab "o'ng
   ustun" emas edi: chap ustun 4 qatorlik joyni ushlab turardi (1440 da 198px), jumla
   esa 2–3 qator. ≥ 900 da bir ustunli holatda jumla uchun 2 qator ushlanadi (shu enda
   odatiy izoh uzunligi), skeleton ham 2 chiziq. Uzunroq izoh panelni o'stiradi.
   2–3 sabab — ≥ 1100 da avvalgidek jumla | o'qlar.
4. **Pastki bo'lim sarlavhasi:** "Your taste vs this film" yangi kicker bilan deyarli bir
   xil gap edi. Endi **"Other traits"** (uz "Boshqa jihatlari", ru "Другие черты") —
   "Why you" o'qlar ko'rsatganda; aks holda **"Its strongest traits"** ("Eng kuchli
   jihatlari", "Самые сильные черты"), chunki u holda bu filmning eng kuchli 6 traiti va
   "boshqa" deyishga asos yo'q.

Qo'shimcha topilgan (brifda yo'q): ta'm profili yo'q foydalanuvchida taqqoslash "siz"
nuqtalarini 0 da chizardi — API `scores: {}` beradi, sahifa uni `0` deb o'qirdi. Endi
bo'sh `scores` — "ta'm yo'q", "siz" nuqtasi chizilmaydi (test bilan).

**O'lchovlar** (headless Chrome, CDP, mock API film 250 ms, izoh +900 ms; axe 4.10.2):

| Holat | Panel balandligi | CLS | axe |
|---|---|---|---|
| Kuchli, 3 sabab, 1440 / 390 | 258 / 501 px | 0.000001 / 0 | 0 / 0 |
| Yaxshi, 3 sabab, 1440 / 390 | 258 / 501 px | 0.000002 / 0.000011 | 0 / 0 |
| Darajasiz, 1 sabab (Zodiac), 1440 / 390 | **272** / 330 px (avval 1440 da ~250, ichida bo'sh joy) | 0 / 0 | 0 / 0 |
| Ta'm profili yo'q, 1440 / 390 | 111 / 133 px | 0 / 0 | 0 / 0 |
| Darajasiz, 1 sabab, 1024 / 900 / 768 / 320 | 262 / 262 / 295 / 358 px | 0 / 0 / 0 / 0.0001 | 0 (1024, 320) |
| Uzun izoh: 1 sabab 1440 / 1024 / 390 | | 0.0059 / 0.0015 / 0.0075 | |
| Uzun izoh: 3 sabab 1440 / 390 | | 0.0013 / 0.0075 | |

Zodiac 1440 da panel 250 dan 272 ga o'sdi, lekin ichida bo'sh joy yo'q: jumla 78px
(2 qator) = ushlangan joy 78px, o'q jumla ostida. `scrollWidth` = ekran eni hamma
holatda. Sahifada `NN%` yo'q. Qizil: faqat "STRONG MATCH" kicker'i.

Testlar: 15 fayl, 192 (yangi: bitta sabab — bir ustun va legend o'q bilan; 2–3 sabab —
ikki ustun; darajasiz kicker; ta'm yo'q — kicker va "siz" nuqtasi yo'q). Bundle: JS
623.22 kB (gzip 181.32), CSS 23.82 kB.

### 3-bosqich: Home hero (2026-10-05)

`components/Hero.tsx`, Feed'ning boshida. "For you" ning birinchi 5 filmi, bittadan.

- **Rasm:** backdrop `.main` ning to'liq enida, w780/w1280 `srcset`; backdrop yo'q —
  poster xira; ikkalasi ham yo'q — `--surface`. Birinchisi `fetchpriority="high"` (LCP),
  qolganlari faqat navbati kelganda: ko'rsatilganlar va keyingisi. Slaydlar 600 ms
  cross-fade (reduced motion'da yo'q). Gradientlar film sahifasidagidek.
- **Balandlik qat'iy:** telefon `max(440px, 55svh)`, ≥ 640 `clamp(440px, 70vh, 720px)`.
  Minimal emas, qat'iy: uzun nom yoki ochilgan jumla har slaydda qatorlarni surmasin.
- **Matn:** nom (Playfair 32 / 56px, film sahifasiga havola), yil va davomiylik chiplari,
  daraja pill'i (kuchli qizil, yaxshi neytral, aks holda yo'q), ikki neytral tugma —
  "Why it suits me?" va Save.
- **"Why it suits me?":** tavsiya javobida keshlangan jumla bo'lsa — hero ichida ochiladi
  (`aria-expanded`); yo'q bo'lsa — film sahifasiga havola. Hero hech qachon izoh
  so'ramaydi (testda tekshirilgan).
- **Aylanish:** 7 s; sichqoncha yoki fokus ichida bo'lsa, jumla ochiq bo'lsa, Pause
  bosilsa to'xtaydi (WCAG 2.2.2). Reduced motion — o'zi aylanmaydi, Pause yo'q. ← →
  tugmalari, nuqtalar (joriy — oq va kengroq, qolgani `--faint`; har biri 24px nishon),
  klaviaturada ← →. Aylanayotganda `aria-live="off"`, to'xtaganda `polite`.
- **API:** `backdrop_path` endi har `MovieOut` da (tavsiyalar, qidiruv, watchlist),
  `MovieDetailOut` dan ko'chirildi; `types.ts` da `Movie` ga. Test: tavsiya elementlari
  saqlangan backdrop'ni qaytaradi.

**Brifdan farqlar:** janr chipi yo'q — `MovieOut` da janr yo'q, uni qo'shish tavsiya
so'roviga yana bir join (keyin, kerak bo'lsa). Hero'dagi film birinchi qatorda ham bor
(Netflix kabi); natijada 1440 birinchi ekranida qizil 3 ta (hero + 2 poster badge'i),
ikkitasi bitta film.

**O'lchovlar** (headless Chrome, CDP, mock API; axe 4.10.2):

| | 1440 | 1024 | 390 | 320 |
|---|---|---|---|---|
| Hero (en × balandlik) | 1232 × 630 | 816 × 538 | 390 × 464 | 320 × 440 |
| Birinchi qator tepasi | 654 | 562 | 540 | 516 |
| CLS (yuklanish) | 0 | 0 | 0 | 0 |
| CLS (16.5 s, ikki aylanish) | 0 | — | 0 | — |
| LCP elementi | hero backdrop | hero backdrop | hero backdrop | hero backdrop |
| axe | 0 | 0 | 0 | 0 |
| `scrollWidth` | ekran eni | ekran eni | ekran eni | ekran eni |

Aylanish brauzerda: 1.1 s Prestige → 8.1 s Memento → 14.8 Zodiac → 21.9 Prisoners → 29
Wind River (~7 s). Reduced motion'da 16 s da ham birinchi film, `aria-live="polite"`.
Yuklanmagan rasmlar: boshida 2 ta `img` (joriy + keyingi). Testlar: 16 fayl, 205
(Hero 10, Feed +2). Bundle: JS 628.33 kB (gzip 182.71), CSS 26.41 kB.

### 4-bosqich: Movie DNA — radial diagramma (2026-10-06)

`components/DnaFlower.tsx` (qo'lda SVG), `pages/Dna.tsx`.

- **Diagramma:** 14 nur, `traits.json` tartibida, soat 12 dan soat yo'nalishida;
  uzunlik qiymatga chiziqli (ichki doira 40 → 100 aylanasi 170 birlik). Masshtab
  hamma uchun bir xil: 100 aylanasi doim bir joyda, shakllar taqqoslanadi. 50 va 100 da
  xira aylana. Eng kuchli 3 nur to'liq oq; qolganlari qiymatga qarab 0.4–0.85 (0.4 —
  fonga nisbatan ~3.5:1, WCAG 1.4.11 grafika uchun 3:1). Qizil yo'q.
- **Shakl (foydalanuvchi qarori, 2026-10-06):** nur uchlarini tutashtiruvchi xira yopiq
  chiziq (`--line` va `--muted` aralashmasi), ichi oq 6%. Yuqoridagi jadvalda radar
  "qo'shni o'qlarni bog'langandek ko'rsatadi, shakl tartibga bog'liq" deb rad etilgan
  edi — bu e'tiroz o'z kuchida, lekin: nurlar o'z joyida qoladi (qiymat nur uzunligidan
  o'qiladi), tartib hamma uchun bir xil, shakl esa aynan sahifaning maqsadi — ikki
  odamni bir qarashda taqqoslash.
- **Yorliqlar:** ≥ 640 — 14 tasi (uzunlari ikki qatorda); torroqda faqat eng kuchli 3
  tasi (to'liq oq nurlar). Diagramma qutisi 4:3 (600 × 450 birlik) — kvadrat yuqori va
  pastda bo'sh polosa qoldirardi.
- **Joylashuv:** < 1100 — bitta ustun, markazda: xulosa, diagramma (≤ 480px),
  statistika bir qatorda, "Numbers". ≥ 1100 — ikki ustun: chapda diagramma (560px,
  vertikal markazda), o'ngda xulosa (Playfair, 24–32px, chapga), statistika ro'yxat
  bo'lib, "Numbers". Avval sinalgan "markazda bitta tor ustun" 1440 da quruq chiqdi
  (1232px enda 480px ustun). Ikki ustunli blok sarlavha qatori ostidagi balandlikda
  vertikal markazda (`min-height: calc(100vh - 200px)`; 1440 × 900 scroll bermaydi).
  Statistika plitkalari bir qatorli: yorliq chapda, qiymat o'ngda (40px, uchtasi 136px).
- **"Numbers":** oddiy `<details>` (modal emas) — 14 qiymatning matnli ro'yxati,
  diagrammaning ekran o'quvchi uchun muqobili; diagramma `role="img"`, eng kuchli
  uchtasi qiymati bilan `aria-label` da.
- **Harakat:** nurlar markazdan ketma-ket o'sadi (har biri 400 ms, 40 ms oraliq), shakl
  keyin paydo bo'ladi; reduced motion — animatsiya yo'q (o'lchangan: 0).

O'lchov: CLS eng yomoni 0 (chegara 0.1); axe 0 (1440, 1100, 390, 320 ru); 320 da scroll
yo'q, ruscha yorliqlar sig'adi (telefonda 22 birlik).

### 5-bosqich: qolgan ekranlar (2026-10-06)

Qoida: mavjud komponentlar, yangi narsa yo'q. To'rt ekran hozirgi qoidalar bilan
solishtirildi (qizil faqat "Strong match", neytral tugma va chiplar, kicker faqat daraja
bor joyda, oddiy yorliqlar — eyebrow / section-title):

- **Qidiruv:** natijalar Home bilan bir xil kartalar — endi Home'dagi hover tez
  tugmalari ham (Rate, Save). Mantiq umumiy hook'da: `components/QuickActions.tsx`
  (`useQuickActions`), Feed ham shuni ishlatadi.
- **Watchlist:** ro'yxat qoladi (foydalanuvchi qarori). Qatorda faqat "Strong match"
  pill'i ("good" ko'rsatilmaydi, TZ 1.16), tugmalar neytral — o'zgarish kerak emas edi.
- **Onboarding:** tanlash plitkalari (toggle, karta emas), oq belgi va progress, bitta
  oq asosiy tugma — qoidalarga mos, o'zgarishsiz.
- **Profil:** chiplar, neytral tugmalar, kichik sarlavhalar — mos, o'zgarishsiz.

O'lchov (bir marta): CLS eng yomoni 0 (chegara 0.1); axe 0 (to'rt ekran, 1440 va 320 ru);
320 da gorizontal scroll yo'q, rus tilidagi yozuvlar sig'adi (kesilgan element yo'q).

### Logo (2026-10-09, 1-bosqich)

Belgi Movie DNA diagrammasidan olingan: markazi bo'sh, har traitga bitta nur. Bitta oila,
ikki chizma, ikkalasi `viewBox="0 0 120 120"`, `stroke-linecap="round"`. Kod:
`components/Logo.tsx` (`size` px, `variant` "full" | "compact", `title`). Koordinatalar
shu faylda, bitta manba.

| | Full — 40px va undan katta | Compact — 40px dan kichik |
|---|---|---|
| Nurlar | 14 ta, `stroke-width` 6, ichki aylana r 14 dan uchigacha | 8 ta, `stroke-width` 9 |
| Konvert | Nurlar uchidan o'tuvchi `<polygon>`: fill 7%, stroke 40%, `stroke-width` 1.6, `stroke-linejoin` round | Yo'q |
| Qayerda | Welcome 48px; katta yuklanish belgisi (72px) | Yon menyu 32px, mobil yuqori panel 28px, favicon; ichki yuklanish belgilari (`variant="compact"` katta o'lchamda ham) |

**Chegara 40px** (foydalanuvchi, 2026-10-09; avval 24px edi). 40px dan kichikda doim compact. Sabab: yon menyudagi 32px skrinshotda 14 nur bir-biriga qo'shilib ketdi. Xato o'lchamda emas, 14 nurni kichik o'lchamda chizishda edi. Ikki variantli oila aynan shu uchun bor: o'lcham chizmani tanlaydi. Testi: 39px compact, 40px full.

Full nurlari `[x1, y1, x2, y2]`, soat 12 dan soat yo'nalishida: 60,46→60,16.8;
66.07,47.39→74.06,30.81; 70.95,51.27→90.1,36; 73.65,56.89→86.91,53.86;
73.65,63.11→104.16,70.08; 70.95,68.73→87.68,82.07; 66.07,72.61→73.15,87.3; 60,74→60,100.5;
53.93,72.61→48.76,83.33; 49.05,68.73→30.68,83.38; 46.35,63.11→27.15,67.5;
46.35,56.89→17.2,50.23; 49.05,51.27→37.33,41.92; 53.93,47.39→42.86,24.41.
Compact: 60,44→60,12.3; 71.31,48.69→84.54,35.46; 76,60→102.6,60; 71.31,71.31→81.5,81.5;
60,76→60,106.2; 48.69,71.31→33.41,86.59; 44,60→27.4,60; 48.69,48.69→30.87,30.87.

**Rang: faqat `currentColor`** — nurlar ham, konvert ham. Rangni joyi beradi: yon menyu va
Welcome'da `--text`. Qizil yoki boshqa aksent yo'q. Brief maketidagi `#F2F2F3` / `#0B0B0C`
ishlatilmadi: ular ozgina ko'k tusli, qaror 5 va CLAUDE.md ("inline hex yo'q") ustun
(foydalanuvchi, 2026-10-09).

Statik fayllar (`apps/web/public/`), tokenlarning qiymati bilan:
- `favicon.svg` — compact, fonsiz. Ichida `prefers-color-scheme`: yorug' brauzerda `#0a0a0a`
  (`--bg`), qorong'ida `#f5f5f5` (`--text`) nurlar. Oq favicon yorug' tabda yo'qolar edi.
- `apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png` — full, `#0a0a0a` fon,
  `#f5f5f5` nurlar, burchak radiusini tizim qo'yadi.
- `manifest.webmanifest` — minimal: nom, ikki ikonka, `background_color` va
  `theme_color` `#0a0a0a`. `display` yo'q: telefonga o'rnatish alohida qaror.

Ikonkalar `Logo.tsx` koordinatalaridan skript bilan chiziladi (headless Chrome, CDP —
yangi dastur o'rnatilmaydi). Logo o'zgarsa, ikonkalar qayta chiziladi. `Logo.test.tsx`
favicon nurlarini `COMPACT_RAYS` bilan solishtiradi.

O'lchov (2026-10-09, mock): CLS 0 (Home 1440 va 390, Welcome 390 va 1440, Home 320 ru);
axe 0; 320 da gorizontal scroll yo'q. Bundle: JS +1.06 kB (gzip +0.56 kB), CSS −0.14 kB;
ikonkalar bundle'dan tashqarida, `public/` da (jami ~33 KB).

### Yuklanish holatlari (2026-10-09, 2-bosqich)

Belgi bilan yuklanish: `components/States.tsx` — `LoadingMark` (belgi va matn) va
`SavingLabel` (saqlash tugmasi ichida). Ikki harakat, faqat `transform` va `opacity`:

| Harakat | Qiymat | Qayerda |
|---|---|---|
| Aylanish (`.logo-spin`) | 360°, 2.4 s, linear, cheksiz, markaz atrofida | Katta yuklanish: Feed |
| Pulsatsiya (`.logo-pulse`) | opacity 1 → 0.45 → 1, 1.6 s, ease-in-out, cheksiz | Kichik, ichki holatlar |

| Joy | Belgi | Matn (en / uz / ru) |
|---|---|---|
| Feed, birinchi yuklanish — kontent maydoni markazida | 72px full, aylanadi | 0–5 s: "Picking your films…" / "Filmlaringiz tanlanmoqda…" / "Подбираем ваши фильмы…"; 5–15 s: "Still looking…" / "Hali ham qidiryapmiz…" / "Всё ещё ищем…"; 15 s+: "The server is waking up, just a moment…" / "Server uyg'onmoqda, biroz kuting…" / "Сервер просыпается, подождите немного…" |
| Film sahifasi, izoh yozilayotganda — izoh slotining o'rnida | 32px compact, pulsatsiya | "Writing the explanation…" / "Izoh tayyorlanmoqda…" / "Готовим объяснение…" |
| Baho saqlanayotganda — tugma ichida (film sahifasi Rate, onboarding Next) | 20px compact, pulsatsiya | "Saving…" / "Saqlanmoqda…" / "Сохраняем…" |
| Qidiruv natijalari | Belgi yo'q, skeleton qoladi | — |
| Kartalardagi tez baholash (Home, Qidiruv) | Belgi yo'q: dialog darhol yopiladi, baho optimistik; xato bo'lsa toast (foydalanuvchi, 2026-10-09) | — |

Qoidalar:
- **Matn — `aria-live="polite"`** (`role="status"`), almashganda ekran o'qish dasturi
  eshitadi. Belgi `role="img"`, nomi tilga mos "Loading" / "Yuklanmoqda" / "Загрузка".
- **Reduced motion:** belgi qimirlamaydi, faqat matn qoladi — CSS global qoidasi ham,
  `LoadingMark` / `SavingLabel` klassni umuman qo'ymaydi (JS).
- **Saqlash tugma ichida** (qaror A, foydalanuvchi, 2026-10-09; briefdagi "yonida" o'rniga,
  CLS 0 uchun): yozuv, ko'rinmas "Saving…" namunasi va xabar bitta grid katakda — tugma doim
  ikkalasining kengrog'icha keng, saqlash boshlanganda ham, tugaganda ham hech narsa
  siljimaydi. Tugma o'chirilmaydi: `aria-disabled`, ikkinchi bosish e'tiborsiz.
- **CLS 0 uchun:** Feed matni to'liq kenglikda, ikki qator balandlikda band qilingan va har
  xabar yangi element (`key`) — markazlangan matn almashganda siljish sanalmaydi. Izoh
  yuklanishi eski skeleton balandligini (slot shriftida 3 qator, yolg'iz panelda 2)
  saqlaydi — ≥ 1100px da markazlangan ustun matn kelganda qimirlamaydi.
- Feed matnlari 5 va 15 s da almashadi (`FEED_LOADING_STEPS`): oxirgisi muhim — Render Free
  15 daqiqa tegilmasa uxlaydi va ~35 s da uyg'onadi (`docs/deploy.md`).

O'lchov (2026-10-09, mock, `mm.mock.delay` bilan): CLS 0 — Feed yuklanishi 1440 (0 s), 390
va 320 ru (16 s, "server uyg'onmoqda"), 1440 uz; Feed kelishi 1440 va 320 ru; izoh yuklanishi
va kelishi 1440, 390; saqlash 1440 va 390 (tugma kengligi saqlashdan oldin va paytida bir
xil: 171.2 / 219.3 px). axe 0 hammasida. Ikkita oldindan bor siljish (o'zgarmagan, HEAD'da
ham shu qiymat): izoh 1100px da to'rt qatorga chiqqanda 0.0016 (zaxira 3 qator) va 320 ru da
0.0016 (matn 4 qatorlik zaxiradan uzun) — bu bosqichga kirmaydi.
Bundle (1-bosqichga nisbatan): JS +1.74 kB (gzip +0.54 kB), CSS +1.05 kB (gzip +0.23 kB). Testlar: 236.

### O'tish effektlari (2026-10-09, 3-bosqich)

Qiymatlar 7-bo'lim jadvalida. Amalga oshirish:
- **Sahifa:** `AppShell` kontentni yo'l bo'yicha kalitlaydi (`.page-enter`), yangi sahifa —
  yangi element, 120 ms opacity. `transform` yo'q: u sahifadagi `position: fixed` panellarni
  (telefonda film tugmalari) animatsiya paytida o'zi bilan olib ketardi (foydalanuvchi
  qarori, variant B).
- **Animatsiya tugagach hech narsa qolmaydi** (`fill` yo'q) sahifa, kontent paydo bo'lishi va
  onboarding qadamlarida: opacity animatsiyasi amalda turgan element stacking context
  yaratadi va ichidagi dialog (z-index 70) yuqori panel ostida qolib ketardi.
- **Dialog:** `Dialog.tsx` yopilishni 120 ms kutadi (`DIALOG_CLOSE_MS`), keyin `onClose`;
  ichidagi tugmalar `useDialogClose` / `DialogCancel` orqali xuddi Escape kabi chiqadi.
  Reduced motion'da darhol yopiladi.
- **Onboarding:** qadam o'rami qadam bo'yicha kalitlangan; pastki panel (`.sticky-foot`) dan
  boshqa har bola siljiydi — o'ramga `transform` berilsa, fixed panel unga yopishib qolardi.
  `.onboarding { overflow-x: clip }`: 320 da yon scroll yo'q.
- **Reduced motion:** global CSS qoidasi hamma animatsiya va transition'ni o'chiradi; JS
  tomonda dialog kutmaydi.

O'lchov (2026-10-09, mock, haqiqiy Chrome): CLS 0 va axe 0 — film sahifasi, qidiruv, DNA
(320 ru), watchlist (kontent kelishi), ochiq dialog (1440, 390), onboarding 320; dialog
ochilishi 160 ms, yopilishi 120 ms, 40 ms da hali bor, 240 ms da yo'q, fokus ochgan
tugmaga qaytadi; poster 1.03, `transition` 120 ms ease-out, fokus halqasi `transition` 0s;
reduced motion'da ochiq dialogda ishlayotgan animatsiya yo'q, Escape darhol yopadi.
Onboarding qadam almashinuvi brauzerda o'lchanmadi (skript plitkalarni tanlay olmadi,
keyin xotira yetmadi) — yo'nalish testlarda tasdiqlangan, jonli ilovada ko'riladi.
Sahifa o'tishi: navigatsiyada `.page-enter` da `fade-in` 120 ms, `fill: none`; yon menyu va
yuqori panel joyidan qimirlamaydi, tugagach animatsiya qolmaydi; CLS 0 (1440, 390). Home
CLS 0 (1440, 390, 320 ru, yuklanish bilan) — o'ram `display: flow-root`: busiz Home hero'ning
manfiy margin'i o'ram orqali o'tib, o'ramni 84px siljitardi (0.0467, o'lchovda topildi).
Bundle (2-bosqichga nisbatan): JS +0.83 kB (gzip +0.36 kB), CSS +0.99 kB (gzip +0.19 kB).
Testlar: 244.

**Topilgan va tuzatilgan nuqson (2026-10-09):** film sahifasidagi Rate dialogi `.film-head`
ichida chizilardi, u esa `position: relative; z-index: 1` — alohida qatlam (stacking
context); `.main` esa o'lcham konteyneri (`container-type`). Shuning uchun dialog (z-index 70)
telefonda yuqori panel (20) va pastki menyu (30) ostida, 1440 da qidiruv qatori ostida
qolardi (HEAD'da ham shunday edi). **Tuzatildi:** `Dialog.tsx` endi `document.body` ga portal
bilan chiziladi; React hodisalari va konteksti komponent daraxti bo'ylab ketadi, klaviatura
boshqaruvi o'zgarmadi. Tekshiruv, haqiqiy Chrome (`elementFromPoint`, ekranning to'rt
burchagi va markazi): film sahifasi 390 va 1440, profil 390 — hammasida dialog; fokus
ichida, Escape va fon bosilishi yopadi, fokus ochgan tugmaga qaytadi; ochiq dialogda axe 0,
CLS 0. Testlar (`Dialog.test.tsx`): backdrop — `body` ning bevosita farzandi; Tab aylanadi,
fokus qaytadi. Ustida turishini jsdom tekshira olmaydi (layout yo'q, `elementFromPoint`
ishlamaydi) — bu brauzer o'lchovida.

### 10. Mobil paritet

`apps/mobile/lib/theme/tokens.dart` web tokenlarini aynan takrorlaydi. Mobil ilova hali
boshlanmagan (F6); neytral qiymatlar (qaror 5) Dart fayliga ham o'sha commit'da
yozilgan. Rang qoidasi va ikonkalar Flutter'da ham amal qiladi (Flutter'da lucide'ning
rasmiy porti bor — F6 da tanlanadi).

### 11. Qarorlar (foydalanuvchi, 2026-10-02)

1. **DNA rangi: monoxrom.** Shart: yassi oq emas — har nurning yorqinligi qiymatiga qarab
   o'zgaradi. Ekranning kuchi harakatdan va yirik tipografikadan keladi, rangdan emas.
2. **Asosiy amal tugmasi: oq to'ldirilgan pill, ekranda bittadan.** Glow yo'q.
3. **Navigatsiya: yon menyu qoladi**, qidiruv yuqori o'ngda.
4. **DNA ulashish rasmi: brauzerda.** Server varianti FR-7 backlog'ida qoladi — keyin link
   preview uchun kerak (TZ 1.11).
5. **Fon: toza kulrang.** Tusli fon "rangni posterlar beradi" qoidasiga qarshi ishlaydi.
   Barcha neytral tokenlar (fon, surface, chiziq, ikkilamchi matn) tussiz kulrangga
   o'tadi; `tokens.dart` o'sha commit'da.
6. **`lucide-react`: ruxsat berildi.**

---

## Kod bilan bog'liqlik

Rang va o'lcham qiymatlari ikki joyda yashaydi va ular bir xil bo'lishi shart:

- `apps/web/src/styles/tokens.css`
- `apps/mobile/lib/theme/tokens.dart`

F6 fazasida `tokens_test.dart` CSS faylini o'qib, Dart qiymatlari bilan solishtiradi —
qo'lda nusxalash xatosi shunda tutiladi.

## O'zgartirish tartibi

Dizayn o'zgarsa: avval spetsifikatsiya yangilanadi, keyin ikkala token fayli, keyin kod.
Teskarisi emas.
