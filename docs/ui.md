# UI/UX spetsifikatsiyasi

To'liq dizayn tizimi va barcha ekran maketlari alohida sahifada:

**https://claude.ai/artifact/AMbQ9PQVCAryRVZU6j96G9**

U yerda bor:

- Rang tokenlari va har rangning vazifasi
- Tipografika shkalasi (Playfair Display + Inter + JetBrains Mono)
- Masofa, radius, tegish maydoni o'lchamlari
- Komponentlar: tugma, chip, input, film kartasi, trait bar, match ring
- Navigatsiya modeli (5 bo'lim)
- Ekran maketlari haqiqiy o'lchamda: welcome, onboarding ×2, home feed, film sahifasi,
  watchlist, Movie DNA, assistant, character quiz, character natijasi
- Desktop tartibi
- To'rtta majburiy holat: yuklanmoqda, bo'sh, xato, oflayn
- Platforma pariteti jadvali (web vs Flutter farqlari)
- Qabul mezoni

## Kod bilan bog'liqlik

Rang va o'lcham qiymatlari ikki joyda yashaydi va ular bir xil bo'lishi shart:

- `apps/web/src/styles/tokens.css`
- `apps/mobile/lib/theme/tokens.dart`

F6 fazasida `tokens_test.dart` CSS faylini o'qib, Dart qiymatlari bilan solishtiradi —
qo'lda nusxalash xatosi shunda tutiladi.

## O'zgartirish tartibi

Dizayn o'zgarsa: avval spetsifikatsiya yangilanadi, keyin ikkala token fayli, keyin kod.
Teskarisi emas.
