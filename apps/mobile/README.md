# Movie Match — mobil (Flutter, Android)

Flutter 3.50.1, faqat Android (iOS — 2027-yil yanvarida alohida qaror, TZ 1.31). O'rnatish:
`docs/setup-android.md`. Faza: `docs/prompts/phase-06-mobile.md`.

## Ishga tushirish

API manzili `--dart-define` bilan beriladi, kodga yozilmaydi (`lib/config.dart`):

```bash
cd apps/mobile
flutter pub get
flutter run --dart-define=API_URL=https://movie-match-api-mgdn.onrender.com
```

Telefon USB orqali ulangan va `adb devices` uni `device` deb ko'rsatgan bo'lishi kerak.
Noutbukda build sekin (5.8 GB RAM): asosiy yo'l — CI'dagi APK (`docs/setup-android.md`,
"APK CI'dan").

## Tekshirish (gate)

```bash
flutter analyze   # nol issue, info ham emas
flutter test
```

## Qoidalar

- Ranglar faqat `lib/theme/tokens.dart` dan. Kodda hex yozilmaydi.
- Tokenlar `apps/web/src/styles/tokens.css` bilan aynan bir xil: `test/tokens_test.dart`
  CSS faylni o'qib solishtiradi. Birini o'zgartirsangiz, ikkinchisini ham.
- Material: `package:material_ui/material_ui.dart` (Flutter 3.50 da
  `package:flutter/material.dart` eskirgan).
- Shriftlar: web'dagi Playfair Display 700–900, Inter 400–800, JetBrains Mono 400 va 600,
  `assets/fonts/` da, OFL litsenziyalari yonida.
- Holat: Riverpod. HTTP: Dio. Navigatsiya: go_router.
