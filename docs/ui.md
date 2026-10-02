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
- **Hover** (sichqoncha, `pointer: fine`): poster 1.05 ga kattalashadi, ustida qorong'u
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
| Poster hover | `transform: scale(1.05)` + qatlam paydo bo'lishi | 200 ms |
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
| 1 | Film sahifasi (backdrop hero) | 1 kun |
| 2 | Home: poster qatorlari va hover | 1 kun |
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
