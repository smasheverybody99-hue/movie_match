# ADR 0008 — "Sabab" yaqinlikni bildiradi, yo'nalishni emas

- **Holat:** qabul qilindi (2026-10-22)
- **Qaror:** foydalanuvchi
- **O'rnini bosadi:** TZ 1.23 ning kesimlari (sabab 0.5 σ "bir xil tomonda", farq 1.0 σ
  "qarama-qarshi tomonda"). TZ 1.23 ning qolgan qismi — simmetrik bitta qoida, sabablar
  ustunligi, `named_traits` + `trait_side` shartnomasi — o'z kuchida.
- **TZ:** 1.27. **Kod:** `app/services/matching.py` (`trait_notes`, `DeviationRule`),
  `app/config.py` (uch sozlama), `app/services/explain.py` (`SYSTEM_PROMPT`).

## Muammo

Jonli saytda (2026-10-22, akkaunt `d394a840`, film **Up**) panel sarlavhasi
**"WHY IT SUITS YOU"**, ostidagi jumla esa:

> "This film stays far away from typical movie violence, keeping things **much gentler than
> you usually prefer**. It also gives you a story that leaves plenty of loose ends instead
> of wrapping everything up neatly."

Ya'ni sarlavha moslikni aytadi, jumla esa tafovutni. Bu TZ 1.23/1.24/1.25 da uch marta
tuzatilgan ziddiyatning yana bir ko'rinishi, lekin bu safar sababi boshqa joyda: qoidaning
o'zida. Jumla rost, sarlavha ham qoidaga ko'ra rost — **"sabab" so'zining ma'nosi noto'g'ri
edi.**

Nega shunday chiqqani, o'sha filmning haqiqiy raqamlari bilan (katalog 500 film):

| trait | katalog μ | σ | ta'm | film | og'ish | kattalik | yo'nalish (ta'm−μ)/σ |
|---|---|---|---|---|---|---|---|
| `ending_ambiguity` | 28.8 | 23.3 | 25.6 | 10 | −15.6 | 0.67 σ | **−0.14 σ** |
| `violence` | 44.0 | 27.2 | 41.7 | 25 | −16.7 | 0.61 σ | **−0.08 σ** |

Eski qoida: og'ish ta'm yo'nalishi bilan bir xil tomonda va kattalik ≥ 0.5 σ → sabab.
Ikkala shart ham bajarilgan. Lekin foydalanuvchining "yo'nalishi" — oddiy filmdan 2.3 va
3.2 **ball** narida, ya'ni amalda nol; film esa ulardan 16 ball narida. Qoida "sizga mos"
deb atagan narsa aslida "siz o'rtachada turasiz, film esa ancha pastda" edi. LLM shuni
o'qib, rost jumla yozdi — faqat u mosliknikidan boshqa jumla edi.

Bu chetki hol emas, tizimli: `d394a840` uchun 500 filmdan **495 tasi** (99.0%) sabab
tomonida edi. Bir traitda ta'mning o'rtachadan 2–3 ball narida turishi butun katalogni
"sizga mos" ga aylantiradi, chunki arzon 0.5 σ kesimi oson o'tiladi va **sabablar ustun**
qoidasi haqiqiy tafovutlarni jim qiladi (Up da `humor` 1.12 σ va `mystery` 1.08 σ —
ikkisi ham gapirmagan).

## Qaror

Kattalik o'lchovi bitta qoladi, lekin ikki tomonda **teskari** ma'no beradi:

```
kattalik[i]  = |movie[i] - taste[i]| / σ[i]     film foydalanuvchidan qancha narida
yo'nalish[i] = |taste[i] - μ[i]|     / σ[i]     foydalanuvchi oddiy filmdan qancha narida

sabab : kattalik <= 0.35  VA  yo'nalish >= 0.40      (ikkisi ham sozlama)
farq  : kattalik >= 1.0                              (sozlama)
boshqa holda: hech narsa

sabablar saralanishi: eng KICHIK kattalik birinchi  (eng yaqin trait yetakchi)
farqlar saralanishi:  eng KATTA w·kattalik birinchi
sabablar ustun; ikkisi ham bo'lmasa panel jim
```

### Nega yaqinlik

"Sizga mos" — moslik haqidagi da'vo, shuning uchun u **moslikni** o'lchashi kerak: film
foydalanuvchining o'z darajasida turishi. Eski qoida yo'nalishni o'lchardi, va yo'nalish
mosliknikidan boshqa narsa — 16 ball narida turgan film ham "bir xil tomonda" bo'lishi
mumkin. Yangi ma'noda jumla ("ayni sizning darajangizda") raqamlardan to'g'ridan-to'g'ri
kelib chiqadi va sarlavha bilan ziddiyat hosil qilishi mumkin emas.

### Nega yo'nalish qo'riqchi bo'lib qoladi (0.40 σ)

Yaqinlikning o'zi yetarli emas: katalog o'rtachasida turgan traitda film bilan ustma-ust
tushish foydalanuvchi haqida hech narsa aytmaydi ("sizga mos: siz ham, bu film ham
o'rtacha darajada zo'ravon"). Shuning uchun yaqinlik faqat foydalanuvchining **aniq
ta'mi bor** traitida gapiradi. 0.40 σ ni o'lchov tanladi (pastdagi jadval): 0.30 da hovuz
kengayib ketadi va aynan tuzatilayotgan nuqson qaytadi, 0.50 da esa hovuz 3–5 traitgacha
qisqarib takrorlanish kuchayadi.

### Nega eng kichik kattalik bo'yicha saralash

Panel uchta trait nomlaydi (`WHY_TRAITS` = 3, o'zgarmadi). Da'vo yaqinlik bo'lgani uchun
ro'yxatni **eng yaqin** trait boshlashi kerak — yo'nalishning kuchi emas, chunki kuchli
yo'nalish o'zi moslik emas. Bu saralash takrorlanishga ta'sir qilmaydi (pastda o'lchangan),
lekin jumlaning birinchi yarmi eng ishonchli dalildan boshlanishini kafolatlaydi.

### Nega farq tomoni o'zgarmaydi

Farq — masofa haqidagi da'vo, u allaqachon masofani o'lchaydi va 1.0 σ kesimi 2026-10-15
da o'lchab tanlangan. `DIFFERENCE_SYSTEM_PROMPT` ham o'zgarmaydi.

## O'lchov

**Qaysi akkauntda:** uchta akkaunt — `d394a840` (jonli saytda kirgan akkaunt, 12 baho),
`77b25c1f` (12 baho; 2026-10-16 dagi "500 filmdan 43 tasi farq tomonida" o'lchovi shu
akkauntda qilingan edi) va `821bfa0e` (12 baho). Har biri uchun **butun katalog, 500
film**; μ va σ shu 500 filmdan. Sana 2026-10-22, `trait_notes` ning o'zi bilan.

Ikki akkauntning ta'mi deyarli bir xil bo'lsa ham eski qoida ularni teskari tomonga
qo'yardi: `d394a840` `ending_ambiguity` da o'rtachadan 3.2 ball **past**, `77b25c1f` 1.0
ball **yuqori** — shuning uchun biri uchun hamma film sabab, ikkinchisi uchun 43 tasi farq
edi. Yangi qoidada tomon bitta trait ishorasiga emas, o'lchanadigan yaqinlikka bog'liq.

| Akkaunt | Qoida | sabab | farq | jim |
|---|---|---|---|---|
| `d394a840` | eski (1.23) | 495 (99.0%) | 5 (1.0%) | 0 |
| | **yangi (1.27)** | **224 (44.8%)** | **276 (55.2%)** | **0 (0.0%)** |
| `77b25c1f` | eski (1.23) | 457 (91.4%) | 43 (8.6%) | 0 |
| | **yangi (1.27)** | **253 (50.6%)** | **247 (49.4%)** | **0 (0.0%)** |
| `821bfa0e` | eski (1.23) | 430 (86.0%) | 70 (14.0%) | 0 |
| | **yangi (1.27)** | **331 (66.2%)** | **169 (33.8%)** | **0 (0.0%)** |

Jim qolish uch akkauntda ham 0% — sabab nomzodi yo'q filmda 1.0 σ dan nariga chiqqan
kamida bitta trait topiladi.

### Yo'nalish qo'riqchisi (sabab ulushi, uchta akkaunt)

| yo'nalish ≥ | kattalik ≤ 0.35 | kattalik ≤ 0.50 |
|---|---|---|
| 0.30 | 44.8 / 63.2 / 88.0% | 63.4 / 78.6 / 96.0% |
| **0.40** | **44.8 / 50.6 / 66.2%** | 63.4 / 67.2 / 77.0% |
| 0.50 | 44.8 / 50.6 / 61.0% | 63.4 / 67.2 / 73.4% |

### Takrorlanish

Sabab sifatida nomlangan har xil traitlar soni va eng ko'p nomlangan traitning ulushi
(sabab tomonidagi filmlardan):

| Akkaunt | har xil trait | eng ko'p nomlangani |
|---|---|---|
| `d394a840` | 3 | `character_depth` — **64.3%** |
| `77b25c1f` | 4 | `emotional_intensity` — **51.8%** |
| `821bfa0e` | 6 | `character_depth` — **43.5%** |

**"Eng kichik kattalik bo'yicha saralash" takrorlanishni kamaytirmadi:** yo'nalish kuchi
bo'yicha saralashda ham aynan shu raqamlar chiqadi (64.3 / 51.8 / 43.5%). Sababi
o'lchangan — sabab tomonidagi filmlarning 96–100% ida nomzod uchtadan ko'p emas
(`d394a840`: 1 nomzod 135 film, 2 nomzod 80, 3 nomzod 9, uchdan ko'p 0), ya'ni uchta
nomzod ham nomlanadi va tartib natijaga ta'sir qilmaydi. Takrorlanish hovuz hajmidan
kelib chiqadi, hovuz esa akkauntning ta'm shaklidan: `d394a840` da 0.40 σ dan yuqori
yo'nalishi bor traitlar faqat uchta (`character_depth` 0.73, `psychological_complexity`
0.58, `emotional_intensity` 0.54).

**Shuning uchun takrorlanish bu ADR bilan hal bo'lmaydi** va backlog'ga yoziladi
(`docs/TZ.md` 2-bo'lim): hal qiladigan tugmalar boshqa joyda — `WHY_TRAITS`, jumla matni,
yoki filmlar bo'yicha nomlangan traitni almashtirish. Bu yerda u o'lchandi va qayd etildi.

## Oqibatlari

- **Izoh keshi bekor qilinadi (sabab tomoni).** Mavjud keshlangan izohlar eski ma'nodagi
  "sabab" uchun yozilgan, ya'ni yangi sarlavha ostida ziddiyat saqlanib qolardi. Kesh
  kalitiga qoida versiyasini qo'shish migratsiya talab qiladi (backlog, `docs/TZ.md`
  2-bo'lim, 2026-10-02 dan beri turgan band), shuning uchun **arzon yo'l tanlandi**: eski
  qoidada sabab tomonida bo'lgan qatorlar bir marta o'chirildi. Jadvalda jami 15 qator
  bor edi; o'chirilganlari qayta yozilsa ~$0.00013 × n, ya'ni sentdan kam. Farq
  tomonidagi qatorlar qoladi — ularning prompti o'zgarmadi. Bu 2026-10-02 dagi amaliyotni
  takrorlaydi ("qoida o'zgarganda eski izohlar qo'lda o'chiriladi").
- **Match foizi va darajalari o'zgarmaydi.** Qoida faqat qaysi traitlar nomlanishini va
  qaysi tomonda nomlanishini belgilaydi (FR-5 formulasi tegilmagan).
- **Jimlikning ma'nosi o'zgardi.** Oldin jimlik "film 14 traitda ta'mga eng yaqin" degani
  edi; endi u "hech bir trait na yetarlicha yaqin va aniq, na 1 σ narida" degani — ya'ni
  film o'rta oraliqda. `Kicker` xatti-harakati o'zgarmaydi (`strong` + jim da qizil
  sarlavha qoladi: band rost), lekin asosi boshqa va `docs/ui.md` da yangilandi.
- **Qo'lda tekshirilishi saqlanadi:** har bir izoh ikki sonni ayirib σ ga bo'lish bilan
  tekshiriladi (CLAUDE.md).

## Ko'rib chiqilgan va rad etilgan variantlar

1. **Faqat kesimni ko'tarish** (sabab 0.5 → 1.0, yo'nalish testi qoladi). Ziddiyatni hal
   qilmaydi: "sizga mos" baribir yo'nalishni bildiradi, faqat kamroq filmda. Jim qolish
   2026-10-15 da o'lchangan: banded filmlarning 72% i.
2. **"Sabablar ustun" ni olib tashlash, ikki tomonga 1.0 σ, eng katta kattalik g'olib.**
   O'lchandi (2026-10-22): `d394a840` da farq 1.0 σ dan o'tgan ikki trait bilan g'olib
   bo'lardi va film "humor, mystery bo'yicha farq qiladi" deb ta'riflanardi — rost, lekin
   14 traitdan 6 tasida ikkisi deyarli ustma-ust tushgan filmni endi hech qachon "mos"
   deb atamaydi.
3. **Yaqinlik va masofani bir shkalada taqqoslash** (sabab kuchi = yo'nalish/σ, farq kuchi
   = kattalik, ustuvorliksiz eng kuchli g'olib). O'lchandi va rad etildi: ikki o'lchov bir
   shkalada emas — sabab kuchi akkauntning eng kuchli yo'nalishi bilan cheklangan
   (0.66–0.83), farq kuchi 1.0 dan boshlanadi, shuning uchun farq nomzodi bor bo'lsa
   deyarli har doim g'olib. Natija: sabab 99% dan **1%** ga tushardi (`d394a840` 4 film,
   `77b25c1f` 6, `821bfa0e` 9), ya'ni muammo hal bo'lmay, teskari aylanardi.
4. **Yo'nalish qo'riqchisini olib tashlash** (faqat yaqinlik). Rad etildi: katalog
   o'rtachasida turgan traitda moslik foydalanuvchi haqida hech narsa aytmaydi, va aynan
   shu traitlar eng ko'p filmda yaqin chiqadi.
