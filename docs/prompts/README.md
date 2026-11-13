# Fazali promptlar

Har fayl — Claude'ga beriladigan bitta to'liq vazifa. Ishlatish tartibi:

1. Fazaning faylini to'liq nusxalab, Claude Code'ga bitta xabar sifatida yuboring.
2. Claude ishlab bo'lgach, **darvoza buyruqlarini o'zingiz ishga tushiring** — Claude
   ularni bajarganini aytgani yetarli emas, natijani o'z ko'zingiz bilan ko'ring.
3. Hammasi 100% o'tgandagina keyingi faylga o'ting.
4. O'tmasa: xato matnini Claude'ga yuboring, tuzattiring, qaytadan ishga tushiring.

## Nega darvoza kerak

Kod tez yoziladi, lekin sifat tekshirilmasa jimgina yig'ilib boradi va uchinchi fazada
portlaydi. Darvoza — shu jimgina yig'ilishni to'xtatadi.

Muhim: "hamma testlar o'tdi" degani "kod to'g'ri" degani emas. Test yozilmasa, o'tadigan
narsa ham bo'lmaydi. Shuning uchun har promptda **majburiy testlar ro'yxati** bor —
ularning har biri yozilgan bo'lishi kerak, va qamrov chegarasi tekshiriladi.

## Fazalar

Tartib TZ 1.30 dan (2026-11-13, foydalanuvchi qarori): faza raqami identifikator, bajarilish
tartibi chapdagi ustunda. Oldingi "Hafta" ustuni (17 haftalik reja) tarix uchun
`docs/roadmap.html` da qoldi.

| Tartib | Fayl | Faza | Maqsad sana | Darvoza |
|---|---|---|---|---|
| 1 | `phase-00-foundation.md` | Poydevor | bajarilgan | Lint + build + smoke testlar |
| 2 | `phase-01-data.md` | Ma'lumot va Movie DNA | bajarilgan | Pipeline testlari + 50 film qo'lda ko'rik |
| 3 | `phase-02-engine.md` | Tavsiya dvigateli | bajarilgan | Formula testlari + endpoint testlari |
| 4 | `phase-03-web.md` | Web ilova | Lighthouse (band 5) qolgan | Komponent testlari + a11y + Lighthouse |
| 5 | `phase-04-assistant.md` | AI assistant | 2026-11-15 | Tool-use testlari + injection testlari |
| 6 | `phase-05-alpha.md` | Yopiq alfa | kod 2026-11-18, testerlar 2026-11-19, qaror 2026-12-03 | Texnik gate + **mahsulot darvozasi** (12 tester, 2 hafta, 15% / 70%) |
| 7 | `phase-06-mobile.md` | Flutter ilova, **Android birinchi**, alfa paytida | Android yopiq testi 2026-11-28 | Widget testlari + qurilma ko'rigi |
| 8 | `phase-09a-web-launch.md` | Web launch tayyorligi va ochiq web launch | 2026-12-05 | Xavfsizlik + tiklash; F5 mahsulot darvozasi o'tgan (15% va 70%) |
| 9 | `phase-09b-store-launch.md` | Do'konga ariza (Google Play) | ariza 2026-12-12; ko'rinish 2026-12-19 dan oldin emas | F6 gate'i, F9a, Play yopiq testi 14 kun; F7/F8 ni kutmaydi (TZ 1.31) |
| 10 | `phase-08-social.md` | Smart Watchlist, Group Match, sayqal | do'kondan keyin, yangilanish | Performance byudjeti |
| 11 | `phase-07-character.md` | Character Match (yurist ko'rigigacha flag ortida) | F8 dan keyin, yangilanish | Matching testlari + huquqiy ko'rik |
| — | iOS | hozir rejalanmaydi | alohida qaror, 2027-yil yanvar | — |

**Darvoza qoidasi o'zgardi (TZ 1.30, 1.31):** qurish alfa paytida ketadi (F6, F9a), lekin ochiq
launch (web va do'kon) faqat F5 mahsulot darvozasidan keyin — 15% ham, 70% ham. 15%
yiqilsa dvigatel qayta ishlanadi; 70% yiqilsa onboarding tuzatiladi va qayta o'lchanadi;
ikkala holda ham launch to'xtaydi. Texnik gate qoidasi o'zgarmagan: bitta test yiqilsa ham
keyingi faza boshlanmaydi.

## Har promptda o'zgartiriladigan joy

Promptlar umumiy yozilgan. Agar biror qaror o'zgarsa (masalan Next.js'ga o'tsangiz),
avval `docs/TZ.md` va `CLAUDE.md` ni yangilang — promptlar ularga tayanadi.
