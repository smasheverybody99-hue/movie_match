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

**Qizil (`--red`) faqat match uchun.** Match foizining raqami va uning grafik ko'rinishi:
ring, poster ustidagi foiz badge'i, hero'dagi foiz. Boshqa hech qayerda. Sabab: match foizi
mahsulotning imzosi; qizil hamma joyda bo'lsa, u kuchini yo'qotadi. Ekranda qizil ko'rinsa —
bu "moslik" degani.

Yangi rang qo'shilmaydi: hamma narsa `apps/web/src/styles/tokens.css` dagi tokenlar bilan.

| Token | Hozirgi vazifasi (v1) | v2 dagi vazifasi |
|---|---|---|
| `--bg` `#0a0a0f` | Ekran foni | O'zgarmaydi: chuqur qora fon |
| `--surface`, `--surface-2`, `--line` | Kartalar, inputlar, chegaralar | Neytral chrome, **toza kulrang** (qaror 5): tus yo'q, R = G = B |
| `--text`, `--muted`, `--faint` | Matn | O'zgarmaydi. Oddiy tugmalarning konturi ham shulardan |
| `--red` | Asosiy tugma, faol nav, tanlangan chip, input fokus, kuchli trait bar, progress nuqtalari, tanlangan poster, ring | **Faqat match:** ring, foiz badge'i, hero'dagi foiz |
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

**4a. Hero (AZM'dan yagona olinadigan narsa)**

- "For you" ning eng yuqori 3–5 ta filmi; backdrop butun kenglikda, desktop'da ~70vh,
  mobil'da ~55vh.
- Gradient: chapdan `--bg` dan shaffofga (matn o'qilishi uchun) va pastdan `--bg` ga
  (qatorlarga silliq o'tish).
- Chapda: film nomi (Playfair, katta), chiplar (yil · davomiylik · janr), **match foizi —
  qizil** (ekrandagi yagona qizil), ikki tugma — **"Nega menga mos?"** va **Watchlist**,
  ikkalasi neytral kontur. "Watch Now" yo'q.
- "Nega menga mos?": tavsiya javobida kesh'langan izoh bo'lsa — hero ichida ochiladi; yo'q
  bo'lsa — film sahifasining "Nega sizga?" qismiga o'tadi. **Hero o'zi LLM chaqirmaydi:**
  aylanish izoh so'ramaydi, aks holda har slayd pul va kunlik limit sarflaydi.
- Pastda nuqtalar: faol — oq, qolganlari — kulrang (qizil emas). Har 7 s da almashadi;
  hover va fokusda to'xtaydi; alohida pauza tugmasi (WCAG 2.2.2: 5 s dan uzoq harakat
  to'xtatilishi kerak); ← → tugmalari. Reduced motion: avtomatik aylanish yo'q.
- Unumdorlik: birinchi backdrop — `fetchpriority="high"` (bu sahifaning LCP elementi),
  qolganlari kerak bo'lganda yuklanadi. TMDB `w1280`.
- **API o'zgarishi:** tavsiyalardagi `MovieOut` da `backdrop_path` yo'q (faqat film
  sahifasida bor). `schemas.py` va `types.ts` ga qo'shiladi — bitta commit'da (CLAUDE.md).

**4b. Poster qatorlari (Netflix/IVI tuzilmasi, NOXX ko'rinishi)**

- Bo'limlar hozir ham gorizontal qator — tuzilma qoladi. Sarlavha oldida neytral ikonka
  (2-bo'lim jadvali).
- Posterlar kattaroq: desktop ~180px eni, mobil'da ekranda 2.4 ta (keyingisining chekkasi
  scroll borligini bildiradi). Nisbat 2:3. Nom poster ostida, kichik, 2 qatorgacha.
- **Match badge doim ko'rinadi** (qizil) — bu imzo.
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
  chiplar, **match ring (qizil)**.
- "Nega sizga?" bloki ring yonida/ostida, tavsifdan yuqorida (v1 qoidasi qoladi).
- Amallar: Baholash va Watchlist — neytral kontur pill; mobil'da pastda sticky.
- "Sizning ta'mingiz va shu film" taqqoslashi neytral: film — oq, siz — kulrang (hozir
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
| Sahifa o'tishlari | View Transitions API: React Router 7.18 dagi `viewTransition` (`Link`/`NavLink`). Qo'llamaydigan brauzer — oddiy o'tish | 200–250 ms |
| Poster hover | `transform: scale(1.08)` + soya + qatlam paydo bo'lishi | 200 ms |
| Match foizi | 0 dan qiymatgacha sanaladi (`useCountUp`, `requestAnimationFrame`) | 600 ms |
| Ring | Hozir bor (CSS `@property --p`) | 600 ms |
| DNA guli | Nurlar markazdan ketma-ket o'sadi | 40 ms oraliq, jami ~900 ms |
| Hero | Slaydlar crossfade | 400 ms |

Qoidalar: faqat `transform` va `opacity` (layout emas); har animatsiya element birinchi
paydo bo'lganda bir marta, har qayta chizishda emas.

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
| 0 | Poydevor: rang qoidasi, `lucide-react` (ruxsat bilan), emoji olib tashlash, qobiq (yon menyu ikonkalari, qidiruv maydoni), umumiy harakat hook'lari | 1.5–2 kun. **Bajarildi** (2026-10-02), skrinshot ko'rigini kutmoqda |
| 1 | Film sahifasi (backdrop hero) | 1 kun. **Bajarildi va tasdiqlandi** (2026-10-04) |
| 2 | Home: poster qatorlari va hover | 1 kun. **Bajarildi** (2026-10-04), skrinshot ko'rigini kutmoqda |
| 3 | Home: hero (`backdrop_path` API'ga) | 1.5–2 kun |
| 4 | Movie DNA: gul, Wrapped tuzilmasi, ulashish rasmi | 2–3 kun |
| 5 | Qolgan ekranlar yangi qoidalarga: Search (poster to'ri), Watchlist, Onboarding, Profile, Welcome | 1 kun |

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
