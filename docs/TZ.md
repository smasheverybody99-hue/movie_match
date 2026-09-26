# Movie Match — Texnik topshiriq (TZ)

Versiya 1.2 · 2026-09-25 · Holat: tasdiqlangan

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
5. Shaxsiylashtirilgan tavsiyalar + match foizi
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

**5 000 film** birinchi versiyada: nomi, yili, davomiyligi, tavsifi, janrlari,
aktyorlari, rejissyori, kalit so'zlari, posteri.

Son `catalogue_target` sozlamasida turadi, kodda emas — ko'tarish bitta qator o'zgarishi.
20 000 dan 5 000 ga tushirildi, chunki trait ekstraksiyasi narxi film soniga to'g'ri
proporsional, va mashhur filmlar shu miqdorda ham qamrab olinadi. Kamroq mashhurlari
mahsulot ishlayotgani tasdiqlangandan keyin qo'shiladi.

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
- Butun jarayon 3 daqiqadan kam vaqt oladi (o'lchanadi).
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
- Har tavsiyada match foizi (0–100) va sabab traitlari bor.
- 60% dan past match ko'rsatilmaydi.
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
| Tillar | O'zbek va ingliz, birinchi kundan | i18n kaliti qattiq kodlanmaydi |
| Xarajat | LLM har foydalanuvchiga oyiga < $0.20 | Hisoblagich |

---

## 6. API shartnomasi (asosiy)

To'liq shartnoma — `services/api/app/schemas.py` va `/docs` (OpenAPI).

| Metod | Yo'l | Vazifa | Auth |
|---|---|---|---|
| GET | `/health` | Tiriklik | yo'q |
| GET | `/movies?q=` | Qidiruv | yo'q |
| GET | `/movies/{id}` | Film detali | ixtiyoriy |
| POST | `/ratings` | Baho qo'yish | ha |
| DELETE | `/ratings/{movie_id}` | Bahoni olib tashlash | ha |
| GET | `/watchlist` | Watchlist | ha |
| POST | `/watchlist` | Qo'shish | ha |
| GET | `/recommendations` | Tavsiyalar | ha |
| GET | `/me/dna` | Movie DNA | ha |
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
