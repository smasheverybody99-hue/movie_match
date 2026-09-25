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

| Fayl | Faza | Hafta | Darvoza |
|---|---|---|---|
| `phase-00-foundation.md` | Poydevor | 1 | Lint + build + smoke testlar |
| `phase-01-data.md` | Ma'lumot va Movie DNA | 2–3 | Pipeline testlari + 50 film qo'lda ko'rik |
| `phase-02-engine.md` | Tavsiya dvigateli | 4–5 | Formula testlari + endpoint testlari |
| `phase-03-web.md` | Web ilova | 6–7 | Komponent testlari + a11y + Lighthouse |
| `phase-04-assistant.md` | AI assistant | 8 | Tool-use testlari + injection testlari |
| `phase-05-alpha.md` | Yopiq alfa | 9 | **Mahsulot darvozasi** — metrika |
| `phase-06-mobile.md` | Flutter ilova | 10–12 | Widget testlari + qurilma ko'rigi |
| `phase-07-character.md` | Character Match | 13–14 | Matching testlari + huquqiy ko'rik |
| `phase-08-social.md` | Ijtimoiy va sayqal | 15 | Performance byudjeti |
| `phase-09-launch.md` | Launch tayyorligi | 16–17 | Xavfsizlik + tiklash + do'kon |

## Har promptda o'zgartiriladigan joy

Promptlar umumiy yozilgan. Agar biror qaror o'zgarsa (masalan Next.js'ga o'tsangiz),
avval `docs/TZ.md` va `CLAUDE.md` ni yangilang — promptlar ularga tayanadi.
