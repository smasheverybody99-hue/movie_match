# Movie Match — Texnik topshiriq (TZ)

Versiya 1.18 · 2026-10-10 · Holat: tasdiqlangan

Bu hujjat nima qurilishini belgilaydi. Qanday qurilishini `docs/architecture.md`,
qachon qurilishini `docs/roadmap.html`, qanday ko'rinishini esa dizayn tizimi hujjati
belgilaydi. Ziddiyat bo'lsa — shu TZ ustun.

---

## 1. Mahsulot

**Muammo.** Odam nima ko'rishni tanlashga filmni ko'rishdan ko'ra ko'proq vaqt sarflaydi.
Mavjud tizimlar nimani ko'rganini biladi, lekin **nega yoqqanini** bilmaydi. Shuning uchun
"trillerlar yoqadi" degan ikki xil odamga bir xil ro'yxat beradi.

**Yechim.** Har filmni 14 o'lchovli **trait vektori** bilan tavsiflash, foydalanuvchi
baholaridan uning ta'm vektorini qurish, va ikkisini taqqoslab tavsiya berish —
har tavsiyaga oddiy tilda sabab bilan.

**Asosiy da'vo.** Movie Match odamning ta'mini shunchalik tushunadiki, u haqiqatan
ko'radigan film tavsiya qiladi. Butun mahsulot shu bitta da'voga xizmat qiladi.

**Foydalanuvchi.** Kino ko'rishni yaxshi ko'radigan, yiliga 30+ film ko'radigan, tanlovga
vaqt sarflaydigan odam. Tasodifiy tomoshabin emas.

---

## 2. Doira

### MVP ichida (F0–F5)

1. Ro'yxatdan o'tish va kirish
2. Film bazasi va qidiruv
3. Onboarding — ta'mni o'rganish
4. Baholash, sevimlilar, watchlist
5. Shaxsiylashtirilgan tavsiyalar + match darajasi (foiz ichki)
6. "Nega sizga yoqadi" izohi
7. Movie DNA profili
8. AI assistant (tabiiy tilda so'rov)
9. Web ilova (React)

### MVP dan keyin (F6–F8)

10. Flutter mobil ilova
11. Character Match
12. Smart Watchlist guruhlari
13. Group Match

### Doiradan tashqarida (V3+)

Taste Twin (1000+ faol foydalanuvchisiz ishlamaydi) · TV/anime/kitob · ijtimoiy tasma ·
izohlar · reyting agregatori · striming ichida ko'rish

Bu ro'yxatga yangi funksiya **faqat yangi TZ versiyasi bilan** qo'shiladi.

### Backlog

Keyinga qoldirilgan ishlar: texnik qarz va keyingi fazaga tegishli g'oyalar
(CLAUDE.md: joriy fazaga sig'maydigan narsa shu yerga yoziladi). Funksiya emas —
yuqoridagi doiraga ta'sir qilmaydi.

| Band | Qachongacha | Qo'shilgan |
|---|---|---|
| `services/api/scripts/migrate_db.py` ga testlar (himoyalar: `lock_timeout`, COMMIT'dan keyin yangi ulanishda tekshiruv, `movies` soni). Hozircha faqat qo'lda sinalgan | Keyingi migratsiyadan oldin | 2026-09-29 |
| `services/api/scripts/select_catalogue.py` ga testlar (`select`: o'n yillik kvotasi, til chegarasi, ikkinchi o'tish, traitli filmlarning majburan kirishi va kvotaga hisoblanishi, sanasiz filmlar). Hozircha faqat qo'lda sinalgan (2026-10-01) | 2-bosqichdan keyin, ro'yxat qayta tuzilishidan oldin | 2026-10-01 |
| Embedding tokenlarini **guruhlab** sanash: har filmga alohida `count_tokens` o'rniga 25 ta matnni bitta chaqiruvda sanash; `tokens=reported` saqlanadi, hujjatda guruhlangan son per-request yig'indisidan ~0.56% kam ekani qayd etiladi (2026-10-02, 25 film: 4 265 vs 4 289). **Nega namuna (har 25-film) + kalibrlangan nisbat emas:** chaqiruvlar soni bir xil, lekin guruhda har filmning o'zi sanaladi; nisbat (4.6 belgi/token) shu 25 filmda jami +2%, alohida filmda 9% gacha xato berdi va til tarkibi o'zgarsa (yangi katalog) qayta kalibrlashni talab qiladi, natija esa `tokens=estimated` bo'lib qoladi. Maqsad: run vaqti — har film uchun bitta tarmoq so'rovi kamayadi. 2026-10-02 dan `count_tokens` xatosi run'ni to'xtatmaydi, shuning uchun bu shoshilinch emas | 5 000 film bosqichidan oldin | 2026-10-02 |
| Movie DNA AI xulosasi (FR-7). Hozir web uchta eng kuchli traitdan shablon jumla quradi; `/me/dna` `summary: null` qaytaradi. AI versiyasi uchun kesh jadvali (migratsiya) va narx qarori kerak | F5 dan oldin | 2026-09-29 |
| DNA ulashish uchun server tomonda rasm (FR-7). Ulashish rasmining o'zi brauzerda yasaladi (dizayn brifi v2, `docs/ui.md`, 2026-10-02); server varianti **link preview** (ommaviy havola ochilganda ko'rinadigan rasm) uchun keyin kerak. Ommaviy havola (token, maxfiylik) dizayni kerak | F5 dan oldin | 2026-09-29 |
| Movie DNA: **Wrapped tuzilmasi** (vertikal "hikoya" bloklari: baholar soni, eng kuchli tomon, gul, xulosa, statistika, ulashish) va **brauzerda chiziladigan ulashish rasmi** (`canvas`, 1080×1920, `navigator.share`). Dizayn 4-bosqichidan ko'chirildi (foydalanuvchi qarori, 2026-10-06): 4-bosqichda faqat radial DNA diagrammasi quriladi. Tavsifi `docs/ui.md`, 6-bo'lim — o'zgarishsiz qoladi | 4-bosqichdan keyin, alohida qaror | 2026-10-06 |
| Qidiruvda striming provayderi filtri (F3 prompti). Katalogda provayder ma'lumoti yo'q — avval ingestion (TMDB watch providers) | F5 dan oldin | 2026-09-29 |
| Onboardingda "nimasi yoqdi?" chiplari 14 ta traitning hammasini ko'rsatadi; dizaynda filmga xos ~5 ta. Filmning kuchli traitlarini onboarding javobiga qo'shish kerak | F5 dan oldin | 2026-09-29 |
| Izohlarning kunlik limiti (FR-6, `explanation_daily_calls_per_user` = 20) tugaganda foydalanuvchi buni bilmaydi: film sahifasi jim zaxira matnga ("Siz bilan umumiy jihatlari: …") o'tadi. Interfeys limit tugaganini aytishi kerak (masalan, "Bugungi izohlar tugadi, ertaga yangilanadi"), yoki zaxira matnga o'tish aniq belgilanishi kerak. Buning uchun API sababni berishi kerak: hozir `text: null` olti holatda bir xil (limit, generator yo'q, ta'm profili yo'q, umumiy trait yo'q, provayder xatosi, rad etilgan javob). F2 qo'lda tekshiruvida topildi (2026-10-02): ~20 ta izoh yaratilgan, limitga yetilgan, keyin zaxira matn. Narx muammo emas (o'lchangan, 2026-10-02, 19 ta cost qatori): izoh o'rtacha 187 kirish / 29.6 chiqish tokeni → standart tarifda ($0.30 / $2.50) $0.00013; limit to'liq ishlatilsa oyiga 600 ta ≈ $0.08 — TZ §5 maqsadi ($0.20) ichida | F5 dan oldin | 2026-10-02 |
| Izoh keshining kalitiga sabablar: `explanations` qatorida izoh qaysi sabablar bilan yozilgani saqlanadi, sabablar o'zgarsa (yangi qoida, katalog o'sishi, ta'm o'zgarishi) — kesh o'tkazib yuboriladi va izoh qayta yoziladi. Migratsiya kerak. Hozircha qoida o'zgarganda eski izohlar qo'lda o'chiriladi (2026-10-02: bitta foydalanuvchining izohlari, ruxsat bilan) | F5 dan oldin | 2026-10-02 |
| Traitlarni qayta baholash (trait ta'riflari va prompt): `visual_style` (o'rtacha 75.8, σ 14.3) va `emotional_intensity` (72.5, σ 14.3) deyarli hamma filmda baland — trait ajratmaydi; promptga "oddiy film = 50" kabi shkala ko'rsatmasi kerak. **Arzon, lekin jarayon qimmat:** 500 film ≈ $0.28 standart tarifda (bepul tarifda $0), lekin qayta baholash 50 filmlik qo'lda ko'rikni bekor qiladi (qayta o'tkaziladi) va barcha embeddinglarni qayta hisoblashni talab qiladi (embedding matnida trait xulosasi bor) | Alohida qaror; 5 000 film bosqichidan oldin | 2026-10-02 |
| Film ma'lumotini tarjima qilish (nom, tavsif) o'zbek va rus tillariga. Hozir interfeys uch tilda, film matni esa ingliz tilida (TMDB `en-US`). Variantlar: TMDB'ning `translations` ma'lumoti (rus tilida ko'p, o'zbekchada kam) yoki LLM tarjimasi (pul, kesh kerak). **Foydalanuvchi so'rovi (2026-10-09):** rus tili uchun TMDB `language=ru-RU`, hozircha backlog'da qoldi (foydalanuvchi qarori). Janr nomlari shu kuni interfeys lug'ati orqali tarjima qilindi (§5). Kerak bo'ladi: tarjimalar jadvali va migratsiya, ingestion'da har film uchun til bo'yicha so'rov, API'ga `lang` parametri, qidiruv ruscha nom bo'yicha | F5 dan oldin | 2026-10-02 |
| **Ta'm yoqmagan filmlardan ham o'rgansin** (FR-5). Ta'm vektori faqat yoqqan filmlardan quriladi; 5 va past baholar vazni 0 — bu foiz bahoni bashorat qila olmasligining ehtimoliy asosiy sababi (2026-10-05: AUC 0.52, leave-one-out 0.44). Alohida traitlarda signal bor (bitta akkaunt: `realism` AUC 0.75, `emotional_intensity` 0.73, `plot_twist` 0.67), lekin 14 traitli masofada ular suyulib ketadi; 25 filmda 14 trait sinalgani uchun bu tasodif ham bo'lishi mumkin. **Nima kerak:** foydalanuvchida kamida 30 ta 8+ va 30 ta ≤ 5 baho (13 va 12 da AUC xatosi ±0.12, 30 va 30 da ±0.07); 14 ta vaznni foydalanuvchining o'zidan o'rganish uchun ~150 baho. **Qanday o'lchanadi:** 8+ va ≤ 5 guruhlari bo'yicha AUC, leave-one-out bilan (har film o'zisiz qurilgan profilga qarshi); muvaffaqiyat — AUC ≥ 0.70 va 95% ishonch oralig'ining pastki chegarasi 0.5 dan yuqori. Hozirgi o'lchov skripti tavsifi: `docs/STATUS.md` | Alohida qaror; baholar to'plangach | 2026-10-05 |
| ~~500 filmni o'n yillik/til kvotasi bilan tanlash (FR-2). Bazadagi 5 000 film 5 000 uchun rejalashtirilgan; `traits submit --limit 500` eng mashhurlarini oladi va o'n yillik taqsimoti buzilishi mumkin. Yechim: `ingest --plan-only --target 500` (TMDB, bepul) ro'yxatini `traits submit --ids` ga berish~~ **Bajarildi (2026-10-01):** `services/api/scripts/select_catalogue.py` kvota siyosatini bizning 5 000 lik katalogimizga qo'llaydi, traitli 50 film majburan kiradi; ro'yxat `docs/catalogue-500.md` (54% ingliz, 26 til). `ingest --plan-only` (TMDB) varianti rad etildi: kunlik o'zgaradi, 75% ingliz chiqdi | 1-bosqichdan keyin, 500 ga o'tishdan oldin | 2026-09-30 |
| CORS preflight keshi: `Access-Control-Max-Age` 600 → 7200 (Chrome chegarasi 2 soat). Hozir 600 — Starlette standarti, jonli API'da tekshirilgan. Foyda: 10 daqiqadan 2 soatgacha oraliqda qaytgan foydalanuvchiga har URL uchun ~0.35 s; preflight keshi URL bo'yicha, shuning uchun har yangi film sahifasi baribir so'raydi. Foydalanuvchi qarori bilan hozir qilinmaydi (`docs/phase-3-status.md`, "Browser timings") | Ochiq | 2026-10-09 |
| Feed keshi foydalanuvchi bo'yicha: `recommend()` natijasi xotirada, kalit — `taste_updated_at`, ko'rilgan filmlar to'plami (baho, watched, dismiss) va 10 daqiqalik muddat; izohlar har so'rovda yangidan. Kutilgan natija: kesh topilganda server ~0.1–0.3 s, topilmaganda o'zgarmaydi. Render Starter qaroridan keyin qaytiladi: Starter'da (0.5 CPU) keshsiz ham feed ~1 s bo'lishi kutiladi va kesh foydasi kamayadi | Render Starter qaroridan keyin | 2026-10-09 |
| To'liq sahifa o'tishi (eski sahifa so'nadi, yangisi 8px ko'tariladi, qobiq qimirlamaydi): `createBrowserRouter` + `RouterProvider` ga o'tish kerak — `BrowserRouter` da React Router'ning `viewTransition` ishlamaydi (`docs/ui.md`, 7). ~1–1.5 soat. 2026-10-09 da qilinmadi: router o'zgarishi marshrutlar va kirish himoyasiga tegadi, yakunlash kunida xavfli. Hozir: 120 ms opacity paydo bo'lish | Ochiq | 2026-10-09 |
| Dialog qatlami uchun avtomatik brauzer testi: telefon va keng ekranda ochiq dialog yuqori panel, pastki menyu va qidiruv qatori ustida turishini `elementFromPoint` bilan tekshirish. jsdom'da layout yo'q, shuning uchun brauzer test vositasi kerak (Playwright) — o'rnatish alohida qaror. Hozircha qo'lda brauzer o'lchovi (`docs/ui.md`, "Topilgan va tuzatilgan nuqson", 2026-10-09) | Ochiq | 2026-10-09 |

---

## 3. Trait vektori — mahsulotning yadrosi

14 o'lchov, har biri 0–100. To'liq ro'yxat va ta'riflar:
`packages/shared/traits.json`. Tartib hech qachon o'zgarmaydi.

| # | Kalit | O'zbekcha | Izoh |
|---|---|---|---|
| 1 | `psychological_complexity` | Psixologik murakkablik | Ichki holat, ishonchsiz idrok |
| 2 | `plot_twist` | Syujet burilishi | Oldingi voqealarni qayta ma'nolantiruvchi ochilish |
| 3 | `mystery` | Sirlilik | Ma'lumotni yashirish, tomoshabinni yechimga jalb qilish |
| 4 | `character_depth` | Personaj chuqurligi | Axloqiy noaniqlik, ichki dunyo |
| 5 | `emotional_intensity` | Hissiy zichlik | Hissiy ta'sirga tayanish darajasi |
| 6 | `pacing` | Temp | 0 = sekin, 100 = to'xtovsiz |
| 7 | `humor` | Hazil | Komediya miqdori va markaziyligi |
| 8 | `romance` | Romantika | Romantik chiziq og'irligi |
| 9 | `action` | Ekshn | Jismoniy sahnalar, quvish, jang |
| 10 | `violence` | Zo'ravonlik | Ochiqligi va chastotasi (filtr uchun ham) |
| 11 | `visual_style` | Vizual uslub | Operatorlik va dizayn o'ziga xosligi |
| 12 | `realism` | Realizm | 0 = fantastik, 100 = hayotiy |
| 13 | `darkness` | Qorong'ulik | 0 = yorug', 100 = umidsiz |
| 14 | `ending_ambiguity` | Ochiq tugash | 0 = to'liq yechilgan, 100 = ataylab ochiq |

**Qoidalar:**
- Trait sifatni o'lchamaydi. "Yaxshi film" degan o'lchov yo'q.
- 50 — "o'rtacha film uchun normal", "noma'lum" emas.
- Yangi o'lchov qo'shish = `traits.json` ga qo'shish + `app/traits.py` ga qo'shish +
  butun bazani qayta hisoblash. Bu qimmat, shuning uchun ro'yxat boshidan to'liq.

---

## 4. Funksional talablar

Har talabning qabul mezoni bor. Mezon bajarilmasa, talab bajarilmagan hisoblanadi.

### FR-1 · Autentifikatsiya

Foydalanuvchi Google, Apple yoki email (magic link) orqali kiradi.

**Qabul mezoni:**
- Uchala usul ham ishlaydi va bir xil foydalanuvchi profiliga olib keladi.
- Token muddati tugaganda avtomatik yangilanadi, foydalanuvchi qayta kirmaydi.
- Akkauntni o'chirish barcha ma'lumotni 30 kun ichida butunlay o'chiradi.
- Mehmon rejimi yo'q — tavsiya uchun profil shart.

### FR-2 · Film bazasi

**500 film** birinchi versiyada: nomi, yili, davomiyligi, tavsifi, janrlari,
aktyorlari, rejissyori, kalit so'zlari, posteri.

Son `catalogue_target` sozlamasida turadi, kodda emas — ko'tarish bitta qator o'zgarishi.
20 000 dan 5 000 ga (v1.2), keyin 5 000 dan 500 ga (v1.5) tushirildi: trait va embedding
narxi film soniga to'g'ri proporsional (`docs/costs.md`), provayder hali tanlanmagan, va
birinchi maqsad — mahsulot ishlashini tasdiqlash. Kamroq mashhurlari shundan keyin
qo'shiladi. Bazada 5 000 film allaqachon yuklangan; ulardan faqat trait'lisi tavsiya va
onboarding'da qatnashadi.

**Qabul mezoni:**
- TMDB'dan kunlik sinxronizatsiya, uzilishdan keyin davom eta oladi.
- Har filmda trait vektori va embedding bor (100% qamrov).
- Katalog o'n yilliklar bo'ylab taqsimlanadi va bitta til bir o'n yillik kvotasining
  55% dan ortig'ini egallamaydi — aks holda katalog faqat so'nggi yillardagi Gollivud bo'lib qoladi.
- Qidiruv 300 ms ichida javob beradi.
- Ma'lumot manbai `app/pipelines/tmdb.py` dan tashqariga sizib chiqmaydi.
- TMDB bepul tarifida quriladi; tijorat litsenziyasi monetizatsiyadan oldin kerak (ADR 0002).
- MovieLens va IMDb datasetlari ishlatilmaydi — litsenziyalari tijoratni taqiqlaydi.

### FR-3 · Onboarding

Yangi foydalanuvchi uchta qadamdan o'tadi: filmlar tanlash → baholash → tayyor.

**Qabul mezoni:**
- Kamida 10 ta film baholanmaguncha tavsiya ko'rsatilmaydi.
- Butun jarayon 3 daqiqadan kam vaqt oladi (o'lchanadi). **Holat (2026-10-10):** bajarildi deb
  hisoblanadi — foydalanuvchi jonli saytda o'tdi, kutish sezilmadi; alohida vaqt o'lchovi
  qilinmaydi (foydalanuvchi qarori). Deploy'dan oldin 3:10 edi, 58 s i baho saqlash kutishi.
- 8.0 dan yuqori baho qo'yilganda "nimasi yoqdi?" chiplari chiqadi.
- Yarim yo'lda chiqib ketgan foydalanuvchi qaytganda o'sha joydan davom etadi.

### FR-4 · Baholash va ro'yxatlar

Foydalanuvchi film baholaydi (0.5–10.0), watchlistga qo'shadi, ko'rilgan deb belgilaydi.

**Qabul mezoni:**
- Baho darhol saqlanadi, optimistik UI, xatolikda orqaga qaytariladi.
- Bitta film bitta foydalanuvchida bitta bahoga ega (qayta baholash yangilaydi).
- Baho qo'yilgach ta'm vektori 5 soniya ichida qayta hisoblanadi.

### FR-5 · Tavsiyalar

Foydalanuvchi bosh sahifada sababli bo'limlarga ajratilgan tavsiyalar oladi.

**Qabul mezoni:**
- Har tavsiyada match foizi (0–100, **ichki**: tartiblash, qo'lda tekshirish va nosozlik
  tahlili uchun; interfeys raqamni ko'rsatmaydi), **match darajasi** (quyida) va sabab
  traitlari (0–3 ta, quyidagi qoida bo'yicha). Film hech bir traitda ajralib turmasa,
  ro'yxat bo'sh — interfeys "umuman mos" deydi.
- Foydalanuvchining katalogdagi eng uzoq 25% filmi tavsiya qilinmaydi (`match_floor_share`;
  1.13 gacha "60% dan past match ko'rsatilmaydi" edi — u 473 filmdan 2 tasini chiqarardi).
- Ko'rilgan va rad etilgan filmlar chiqmaydi.
- Bir bo'limda bitta rejissyordan 2 tadan ko'p film bo'lmaydi (xilma-xillik).
- Javob 500 ms ichida (kesh bilan 100 ms).

**Match formulasi** — ochiq va qo'lda tekshirilishi mumkin:

```
w[i]     = foydalanuvchining i-o'lchovdagi izchilligi (0..1)
d        = sqrt( Σ w[i] * (taste[i] - movie[i])² / Σ w[i] ) / 100
match    = round( 100 * (1 - d) )
```

Izchillik: foydalanuvchi yuqori baholagan filmlarda o'lchov qiymatlari qanchalik
bir joyda to'planganidan kelib chiqadi. Tarqoq bo'lsa — o'sha o'lchov shu odam uchun
muhim emas, vazni past.

**Match darajasi** (1.13, 2026-10-05) — interfeys ko'rsatadigan yagona match signali.
Foiz bahoni bashorat qilishini ko'rsata olmadik (bitta akkaunt, 13 ta 8+ va 12 ta ≤5
film: AUC 0.52, leave-one-out 0.44; `docs/STATUS.md`), lekin u trait bo'yicha uzoqlikni
o'lchaydi. Muammo raqamning soxta aniqligi edi. Daraja — rostgo'y da'vo: "katalogda sizga
eng yaqinlaridan biri".

```
raw[f]   = 100 * (1 - d)   — match foizining yaxlitlanmagan qiymati, katalogdagi har bir
                             traitli film f uchun shu foydalanuvchiga
o'rin    = raw bo'yicha kamayish tartibida (1 — eng yaqini); teng qiymat chegarada ichkarida
kuchli   : o'rin <= N                    N = match_strong_top_n   (standart 5)
yaxshi   : o'rin <= ceil(0.15 * katalog) match_good_share         (standart 0.15; 1.14 gacha 0.35)
           — hisoblanadi va API javobida qoladi, interfeysda ko'rsatilmaydi (1.16)
pastki   : o'rin >  ceil(0.75 * katalog) match_floor_share        (standart 0.25)
```

**Interfeysda daraja ikki holatda** (1.16): **"STRONG MATCH"** (qizil) — eng yaqin N=5
film; qolgan hammasi — neytral kicker **"YOU AND THIS FILM"**. "Yaxshi" hisoblanadi va
API'da `band: "good"` bo'lib qoladi (tartiblash va keyingi qaror uchun; sozlama ham
qoladi), lekin film sahifasi, Home (hero va kartalar) va watchlist uni chizmaydi.
Sabab — o'lchov: Home ta'rifan eng yaqin filmlardan tuziladi, shuning uchun "yaxshi"
Home'dagi film sahifalarining 68% ida (0.15 da; 0.35 da 90%) chiqardi — hech narsani
ajratmaydigan yorliq shovqin (`docs/STATUS.md`, "35% → 15%").

"Kuchli" — mutlaq son (ulush emas): Home'dagi qizil belgilar katalog o'sganda ham kam
qoladi (5 da bitta akkauntning birinchi ekranida 2–3 ta; 10% bo'lsa 11 ta edi). Qizil —
faqat "kuchli". Film sahifasida ring yo'q: daraja (yoki neytral kicker) "Why you"
panelining sarlavhasi, jumla asosiy signal; Home hero'da ham xuddi shu kicker. Chegaralar har foydalanuvchi uchun saqlangan
sonlardan qayta hisoblanadi (`users.taste_*`, `movie_traits.vector`).

**Sabab qoidasi** (2026-10-02; match foiziga ta'sir qilmaydi) — qaysi traitlar "sabab"
deb ko'rsatiladi:

```
μ[i], σ[i] = katalogdagi barcha traitli filmlarning i-o'lchov bo'yicha o'rtachasi va
             standart og'ishi (populyatsiya)
z_film[i]  = (movie[i] - μ[i]) / σ[i]        z_taste[i] = (taste[i] - μ[i]) / σ[i]
sabab      : z_film[i] >= 0.5  va  z_taste[i] >= 0      (ikkalasi sozlama)
kuch       = w[i] * z_film[i];  eng kuchli 3 tasi
```

Film shu traitda oddiy filmdan sezilarli yuqori va foydalanuvchi ham o'sha tomonga
og'gan bo'lsa — sabab. Deyarli hamma filmda baland trait (masalan, katalogda
`visual_style` o'rtachasi 76) har filmga sabab bo'lib chiqmaydi.

### FR-6 · "Nega sizga yoqadi"

Har tavsiyaga 1–2 jumlalik oddiy tildagi izoh.

**Qabul mezoni:**
- Izoh faqat haqiqiy trait mosligiga asoslanadi, umumiy maqtov emas.
- Har (foydalanuvchi, film) juftligi uchun bir marta generatsiya qilinadi va keshlanadi.
- Kesh bo'lmasa ham ekran bloklanmaydi — skeleton ko'rsatiladi.

### FR-7 · Movie DNA

Foydalanuvchi o'z ta'm profilini 14 o'lchovda va bitta jumlalik xulosada ko'radi.

**Qabul mezoni:**
- 10 tadan kam baho bo'lsa — "yana N ta baholang" ekrani.
- Profil har yangi bahodan keyin yangilanadi.
- Ulashish uchun server tomonda rasm generatsiya qilinadi.

### FR-8 · AI Assistant

Tabiiy tildagi so'rov strukturali qidiruvga aylantiriladi.

**Qabul mezoni:**
- "90 daqiqam bor, miyamni portlatsin" kabi so'rov ishlaydi.
- Javob oqim bilan keladi, birinchi belgi 2 soniya ichida.
- Foydalanuvchiga kuniga 30 ta so'rov; limit tugaganda aniq matn ko'rsatiladi.
- Kino mavzusidan tashqari savolga javob bermaydi.
- Prompt injection urinishi tizim ko'rsatmasini o'zgartira olmaydi.

### FR-9 · Character Match (F7)

Foydalanuvchi ta'mi va ixtiyoriy quiz asosida personaj moslik natijasi.

**Qabul mezoni:**
- Quizsiz ham natija beradi (faqat ta'm asosida).
- Natijada **rasm yo'q** — faqat matn nomi va emoji.
- Disclaimer har doim ko'rinadi.
- "Bu personajga o'xshash filmlar" tugmasi tavsiyaga qaytaradi.
- Umumiy mulkdagi personajlar bazada ustunlik qiladi.

---

## 5. Nofunksional talablar

| Kategoriya | Talab | Qanday o'lchanadi |
|---|---|---|
| Tezlik (web) | LCP < 2.5s, INP < 200ms | Lighthouse CI |
| Tezlik (API) | p95 < 300ms, tavsiya < 500ms | Load test |
| Tezlik (mobil) | Sovuq start < 2s | Profil rejimi |
| Ishonchlilik | 99.5% uptime | Uptime monitor |
| Xavfsizlik | Kalitlar faqat env'da, JWT tekshiruvi har so'rovda | Kod ko'rigi + test |
| Maxfiylik | Eksport va o'chirish ishlaydi | Qo'lda test |
| Qulaylik | Kontrast 4.5:1, klaviatura navigatsiyasi, 44px tegish | axe + qo'lda |
| Tillar | Ingliz — standart til va barcha kalitlarning manbasi; o'zbek — ikkilamchi; rus — qo'shimcha variant. Standart har doim ingliz (brauzer tili aniqlanmaydi); o'zbek va rus faqat til menyusidan tanlanadi, tartib: English, O'zbek, Русский. Tanlov saqlanadi va keyingi kirishda shu tilda ochiladi. Interfeys tarjima qilinadi; film ma'lumoti (nom, tavsif, trait xulosasi) TMDB'dan ingliz tilida keladi. Janr nomlari — TMDB'ning qat'iy ro'yxati (19 ta), interfeys lug'atida tarjima qilinadi (`genre.*`), yangi janr kalit olguncha inglizcha ko'rinadi | i18n kaliti qattiq kodlanmaydi; uchala lug'atda kalitlar to'plami bir xil (test, CI) |
| Xarajat | LLM har foydalanuvchiga oyiga < $0.20 | Hisoblagich |

---

## 6. API shartnomasi (asosiy)

To'liq shartnoma — `services/api/app/schemas.py` va `/docs` (OpenAPI).

| Metod | Yo'l | Vazifa | Auth |
|---|---|---|---|
| GET | `/health` | Tiriklik | yo'q |
| GET | `/movies?q=&year_from=&year_to=&max_runtime=&trait=key:min` | Qidiruv va filtrlar | yo'q |
| GET | `/movies/{id}` | Film detali; token bilan shaxsiy match, daraja va sabablar | ixtiyoriy |
| POST | `/ratings` | Baho qo'yish | ha |
| GET | `/ratings` | O'z baholari | ha |
| DELETE | `/ratings/{movie_id}` | Bahoni olib tashlash | ha |
| GET | `/watchlist` | Watchlist (har qatorda shaxsiy match va daraja) | ha |
| POST | `/watchlist` | Qo'shish | ha |
| DELETE | `/watchlist/{movie_id}` | O'chirish | ha |
| POST | `/watchlist/{movie_id}/watched` | Ko'rildi deb belgilash | ha |
| GET | `/recommendations` | Tavsiyalar | ha |
| GET | `/recommendations/{movie_id}/explanation` | "Nega sizga yoqadi" (kesh yoki yangi, kunlik limit) | ha |
| POST | `/dismissals` | "Men uchun emas" | ha |
| DELETE | `/dismissals/{movie_id}` | Rad etishni bekor qilish | ha |
| GET | `/onboarding/films?limit=&offset=` | Onboarding uchun filmlar | ha |
| GET | `/me` | Akkaunt xulosasi | ha |
| DELETE | `/me` | Akkaunt ma'lumotini o'chirish | ha |
| GET | `/me/dna` | Movie DNA: ta'm vektori, statistika | ha |
| POST | `/assistant/chat` | Assistant (SSE oqim) | ha |
| GET | `/character/match` | Character Match | ha |

Xato formati bir xil: `{"detail": "..."}`. Status kodlar standart.

---

## 7. Test strategiyasi va faza darvozasi

Bu bo'lim ishlash tartibini belgilaydi va majburiy.

### Darvoza qoidasi

Har faza oxirida shu buyruqlar ishga tushiriladi:

```bash
# API
cd services/api && ruff check . && ruff format --check . && pytest -q

# Web
cd apps/web && npm run lint && npm run typecheck && npm run build && npm test

# Mobil (F6 dan boshlab)
cd apps/mobile && flutter analyze && flutter test
```

**Keyingi fazaga o'tish sharti — barchasi 100% muvaffaqiyatli.** Bitta test yiqilsa
ham keyingi faza boshlanmaydi. Tuzatiladi, qayta ishga tushiriladi, so'ng o'tiladi.

### Testlar zaif bo'lib qolmasligi uchun

100% o'tish o'z-o'zidan sifat kafolati emas — test yozmasang, hammasi o'tadi.
Shuning uchun har fazada qo'shimcha shartlar bor:

1. **Qamrov:** `services/api/app/services/` va `app/pipelines/` uchun kamida **80%**.
   Router qatlami uchun kamida bitta test har endpoint'ga.
2. **Har faza promptida majburiy testlar ro'yxati** bor — ular yozilmasa, faza tugamagan.
3. **Salbiy holatlar majburiy:** har endpoint uchun auth yo'q, noto'g'ri kirish,
   topilmadi holatlari testlanadi.
4. **Qo'lda qabul ro'yxati:** har fazada avtomatlashtirib bo'lmaydigan tekshiruvlar
   (ko'rinish, oqim) qo'lda bajarilib belgilanadi.

### Test turlari

| Tur | Qayerda | Nimani tekshiradi |
|---|---|---|
| Unit | `tests/unit/` | Formulalar, konvertatsiyalar, validatsiya — DB'siz |
| Integratsiya | `tests/integration/` | Endpoint + DB, test bazasida |
| Kontrakt | `tests/contract/` | API javobi web tiplari bilan mos |
| Komponent | `apps/web/src/**/*.test.tsx` | React komponent holatlari |
| Widget | `apps/mobile/test/` | Flutter widget holatlari |

---

## 8. Muvaffaqiyat mezonlari

| Qachon | Metrika | Maqsad |
|---|---|---|
| F5 (alfa) | Tavsiya qilingan film 7 kun ichida ko'rildi | ≥ 15% |
| F5 (alfa) | Onboardingni tugatganlar ulushi | ≥ 70% |
| Launch | D7 retention | ≥ 25% |
| Launch | Birinchi haftada baholar soni (o'rtacha) | ≥ 10 |
| Launch | Assistant so'rovi (foydalanuvchiga) | ≥ 2 |

F5 metrikasi maqsadga yetmasa — mobil ilovaga o'tilmaydi, tavsiya dvigateli qayta
ko'rib chiqiladi. Bu qaror roadmap'da darvoza sifatida belgilangan.

---

## 9. Hujjat o'zgarishi

Bu TZ o'zgarsa, versiya raqami oshadi va o'zgarish shu bo'limda qayd etiladi.

| Versiya | Sana | O'zgarish |
|---|---|---|
| 1.0 | 2026-09-24 | Birinchi versiya |
| 1.1 | 2026-09-25 | Ma'lumot manbai qarori: TMDB bepul tarifi, litsenziya monetizatsiyadan oldin (ADR 0002) |
| 1.2 | 2026-09-25 | Katalog 20 000 dan 5 000 ga; son sozlamaga chiqarildi; o'n yillik va til taqsimoti qo'shildi |
| 1.3 | 2026-09-29 | 2-bo'limga "Backlog" kichik bo'limi; birinchi band: migrate skriptiga testlar |
| 1.4 | 2026-09-29 | §6 API jadvali F2–F3 endpointlari bilan to'ldirildi; backlog'ga F3 dan qolgan to'rt band (DNA AI xulosasi, ulashish rasmi, provayder filtri, filmga xos chiplar) |
| 1.5 | 2026-09-30 | FR-2: katalog 5 000 dan 500 ga (xarajat); `catalogue_target = 500` |
| 1.6 | 2026-10-01 | Backlog: 500 filmni kvota bilan tanlash bajarildi (`scripts/select_catalogue.py`, `docs/catalogue-500.md`); yangi band — shu skriptga testlar |
| 1.7 | 2026-10-02 | Backlog: embedding tokenlarini guruhlab sanash (5 000 film bosqichi uchun), nega namuna emas |
| 1.8 | 2026-10-02 | §5 Tillar: ingliz standart va kalitlar manbasi, o'zbek ikkilamchi, rus qo'shimcha (foydalanuvchi qarori); backlog — film ma'lumotini tarjima qilish |
| 1.9 | 2026-10-02 | Backlog: izohlar limiti tugaganini interfeys aytishi kerak (F2 qo'lda tekshiruvidan) |
| 1.18 | 2026-10-10 | FR-3: jonli saytda bajarildi, alohida vaqt o'lchovisiz (foydalanuvchi qarori) |
| 1.17 | 2026-10-09 | §5 Tillar: janr nomlari interfeys lug'atida tarjima qilinadi; backlog — film nomi va tavsifining ruscha tarjimasiga foydalanuvchi so'rovi (TMDB `ru-RU`) yozildi |
| 1.16 | 2026-10-06 | FR-5: interfeysda daraja ikki holatda — "Strong match" (qizil) va neytral "You and this film"; "good" hisoblanadi va API'da qoladi, lekin ko'rsatilmaydi. Asos: Home'dagi film sahifalarining 68% ida chiqardi (0.15), ajratmaydi (foydalanuvchi qarori) |
| 1.15 | 2026-10-06 | Backlog: dizayn 4-bosqichi (Movie DNA) faqat radial diagrammaga qisqardi; Wrapped tuzilmasi va brauzerdagi ulashish rasmi backlog'ga (foydalanuvchi qarori) |
| 1.14 | 2026-10-05 | FR-5: "yaxshi" darajasi eng yaqin 35% dan 15% ga (`match_good_share` 0.15): 35% da 500 dan 175 film, har uchinchi film sahifasi — yorliq ma'nosini yo'qotardi (foydalanuvchi qarori). O'lchov: `docs/STATUS.md`. Film sahifasida daraja — panel sarlavhasi |
| 1.13 | 2026-10-05 | FR-5: interfeys match foizini emas, match darajasini ko'rsatadi (kuchli — eng yaqin N=5 film, qizil; yaxshi — eng yaqin 35%, neytral); foiz API'da ichki qoladi; "60% dan past" o'rniga eng uzoq 25% tavsiya qilinmaydi. Asos: foiz 8+ va ≤ 5 baholarni ajratmadi (AUC 0.52). Backlog — ta'm yoqmagan filmlardan ham o'rgansin |
| 1.12 | 2026-10-02 | FR-5: sabab traitlari katalogga nisbatan tanlanadi (formula yuqorida), ro'yxat bo'sh bo'lishi mumkin; backlog — izoh keshi kalitiga sabablar, traitlarni qayta baholash (arzon, jarayon qimmat) |
| 1.11 | 2026-10-02 | Backlog FR-7: ulashish rasmi brauzerda, server varianti link preview uchun qoladi |
| 1.10 | 2026-10-02 | O'sha bandda izoh narxi taxmindan o'lchovga: $0.00013 bittasi, oyiga ≤ $0.08 (avvalgi "$0.24, maqsaddan yuqori" ogohlantirishi noto'g'ri taxminga asoslangan edi) |
