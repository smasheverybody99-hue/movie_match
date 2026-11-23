# F6: Flutter + Android SDK, Android Studio'siz (reja, o'rnatilmagan)

Yozildi 2026-11-23. **Hech narsa o'rnatilmagan.** Har bir qadam foydalanuvchi ruxsati bilan
(CLAUDE.md: dastur o'rnatish va PATH o'zgartirish).

Manbalar (o'qildi 2026-11-23):
- [docs.flutter.dev/install/manual](https://docs.flutter.dev/install/manual) — Flutter 3.50, sahifa 2026-11-11
- [docs.flutter.dev/platform-integration/android/setup](https://docs.flutter.dev/platform-integration/android/setup) — sahifa 2026-11-03
- [developer.android.com/studio](https://developer.android.com/studio), "Command line tools only"
- [developer.android.com/tools/sdkmanager](https://developer.android.com/tools/sdkmanager)

## Hozirgi holat (2026-11-13 da faqat o'qib tekshirilgan)

`flutter`, `dart`, `java`, `adb` yo'q, Android SDK ham yo'q. Git 2.55 bor. C: diskida
240 GB bo'sh joy bor.

## Nima o'rnatiladi va hajmi

| # | Qism | Yuklab olinadi | Diskda | Manba |
|---|---|---|---|---|
| 1 | JDK 17 (Eclipse Temurin, zip, installer'siz) | ~190 MB* | ~320 MB* | Flutter sahifasida JDK versiyasi yozilmagan. Android Gradle Plugin 8.x JDK 17 talab qiladi* |
| 2 | Flutter SDK 3.50, Windows zip (`flutter_windows_3.50.0-stable.zip`) | ~1.1 GB* | ~2.5 GB* (birinchi ishga tushirishdagi keshlar bilan) | Hajm sahifada yozilmagan |
| 3 | Android command-line tools (`commandlinetools-win-15859902_latest.zip`) | **155.7 MB** | ~300 MB* | developer.android.com |
| 4 | `platform-tools`, `platforms;android-36`, `build-tools;36.0.0` | ~200 MB* | ~400 MB* | Flutter sahifasida API 36 |
| 5 | Birinchi `flutter build apk`: Gradle va bog'liqliklar (`%USERPROFILE%\.gradle`) | ~0.5–1 GB* | 1–2 GB* | — |
| 6 | NDK va CMake: faqat plugin talab qilsa, Gradle o'zi yuklab oladi | ~1 GB* | ~2–3 GB* | Flutter sahifasida ro'yxatda bor |
| — | **Jami** | **~2–4 GB** | **~5–8 GB** | |

\* — taxmin, o'lchanmagan. Haqiqiy hajm yuklab olish paytida ko'rinadi.

**O'rnatilmaydi:**
- **Android Studio.**
- **Emulator va uning system image'i** (yana ~2–3 GB). Noutbuk xotirasi kam, emulator o'rniga haqiqiy telefon ishlatiladi.

## Joylashuv

Hamma narsa bitta papkaga tushadi. Unda bo'sh joy ham, maxsus belgilar ham yo'q, admin
huquqi ham kerak emas, `%LOCALAPPDATA%` va Program Files ishlatilmaydi:

```
C:\Users\User\develop\
  jdk-17\                 (1)
  flutter\                (2)
  android-sdk\
    cmdline-tools\latest\bin\sdkmanager.bat   (3)
    platform-tools\  platforms\  build-tools\ (4)
```

Gradle keshi `C:\Users\User\.gradle` ga yoziladi (5). Bu Gradle'ning standart joyi.

## Qadamlar

1. **JDK 17.** Temurin 17 zip'ini `develop\jdk-17` ga oching.
2. **Flutter.** Zip'ni archive sahifasidan yuklang va oching:
   ```powershell
   Expand-Archive flutter_windows_3.50.0-stable.zip -DestinationPath "$env:USERPROFILE\develop"
   ```
   Antivirus `bin\flutter.bat` ni karantinga olishi mumkin. Shunday bo'lsa, `bin` papkasini tekshiring.
3. **PATH (faqat foydalanuvchi PATH'i, tizim PATH'i emas).** Qo'shiladigan papka:
   `C:\Users\User\develop\flutter\bin`.
   Tekshirish: `flutter --version`, `dart --version`.
4. **Command-line tools.** Zip'ni oching va `cmdline-tools` ichida `latest` papkasini yarating. `lib`,
   `bin`, `NOTICE.txt` va `source.properties` ni shu `latest` ga ko'chiring. Natijada
   `develop\android-sdk\cmdline-tools\latest\bin\sdkmanager.bat` hosil bo'ladi.
5. **SDK paketlari.** JDK bilan ishga tushiriladi:
   ```powershell
   $env:JAVA_HOME = "$env:USERPROFILE\develop\jdk-17"
   & "$env:USERPROFILE\develop\android-sdk\cmdline-tools\latest\bin\sdkmanager.bat" `
     "platform-tools" "platforms;android-36" "build-tools;36.0.0"
   ```
   Google `sdkmanager` ni eskirgan deb belgilagan (o'rniga `android sdk install`), lekin u hali
   ishlaydi va hujjatda bor.
6. **Flutter'ga yo'llarni ko'rsatish:**
   ```powershell
   flutter config --android-sdk "$env:USERPROFILE\develop\android-sdk"
   flutter config --jdk-dir "$env:USERPROFILE\develop\jdk-17"
   flutter doctor --android-licenses     # o'qib, "y"; "All SDK package licenses accepted."
   flutter doctor
   ```
   `flutter doctor` "Android Studio not installed" desa, bu kutilgan holat, xato emas.
7. **Telefon.**
   - Settings → About phone → Build number'ni 7 marta bosing, Developer options ochiladi.
   - Developer options'da USB debugging'ni yoqing.
   - Windows uchun telefon ishlab chiqaruvchisining USB drayveri kerak (Pixel uchun: `"extras;google;usb_driver"`).
   - Kabelni ulang, telefonda "Allow USB debugging" ni tasdiqlang va `flutter devices` ni ishga tushiring.
8. **Birinchi build.** `apps/mobile` da `flutter create ...` bajariladi (`apps/mobile/README.md`),
   keyin `flutter build apk --debug`. Gradle shu yerda yuklab olinadi (5).

## Qaytarish

Hammasi o'chadi:
- `C:\Users\User\develop` papkasi;
- `C:\Users\User\.gradle` papkasi;
- `C:\Users\User\.android` (adb kaliti);
- foydalanuvchi PATH'idagi bitta qator.

Ro'yxatga (registry) hech narsa yozilmaydi. Istisno — USB drayveri, u Device Manager orqali o'chiriladi.

## Flutter versiyasi — qaror

**3.50** o'rnatiladi (foydalanuvchi, 2026-11-23). `CLAUDE.md`, ADR 0001 va `README.md` 3.50 ga
yangilandi. O'rnatishning o'zi hali ham foydalanuvchi ruxsatini kutadi.
