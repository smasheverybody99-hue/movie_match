# Movie Match — mobil (Flutter)

Bu papka hozircha to'liq Flutter loyihasi emas. `flutter create` buyrug'ini o'zingiz
bajarasiz — u platforma papkalarini (android/, ios/) generatsiya qiladi.

## Ishga tushirish

```bash
cd apps/mobile
flutter create --org com.moviematch --project-name movie_match .
flutter pub add flutter_riverpod dio go_router
flutter run
```

`flutter create` mavjud fayllarni o'chirmaydi: `lib/theme/tokens.dart` joyida qoladi.
U `lib/main.dart` ni yaratadi — uni quyidagi bilan almashtiring:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'theme/tokens.dart';

void main() => runApp(const ProviderScope(child: MovieMatchApp()));

class MovieMatchApp extends StatelessWidget {
  const MovieMatchApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Movie Match',
        theme: buildTheme(),
        home: const Scaffold(
          body: Center(child: Text('Movie Match')),
        ),
      );
}
```

## Qoidalar

- Ranglar faqat `lib/theme/tokens.dart` dan olinadi. Kodda hech qachon to'g'ridan-to'g'ri
  hex yozilmaydi.
- Tokenlar `apps/web/src/styles/tokens.css` bilan aynan bir xil bo'lishi kerak —
  birini o'zgartirsangiz, ikkinchisini ham o'zgartiring.
- Holat: Riverpod. HTTP: Dio. Navigatsiya: go_router.
- API bazaviy manzili `--dart-define=API_URL=...` orqali beriladi, kodga yozilmaydi.
