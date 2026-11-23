# F6: Flutter + Android SDK, Android Studio'siz

Reja yozildi 2026-11-23; **o'rnatildi 2026-11-23** (foydalanuvchi ruxsati bilan, CLAUDE.md:
dastur o'rnatish va PATH o'zgartirish). Android Studio va emulyator o'rnatilmadi.

## O'rnatildi (2026-11-23, o'lchangan)

| Qism | Yuklab olindi | Diskda |
|---|---|---|
| JDK 17 — Temurin 17.0.21.1, `develop\jdk-17` | 182 MB | 305 MB |
| Flutter **3.50.1** (3.50 ning 2026-11-20 dagi patch'i), Dart 3.14.0, `develop\flutter` | 1.78 GB | 3.3 GB |
| Command-line tools, `develop\android-sdk\cmdline-tools\latest` | 148 MB | 172 MB |
| platform-tools (adb 37.0.3), platforms;android-36, build-tools;36.0.0 | — | 287 MB |
| pub keshi, `develop\pub-cache` | — | 185 MB |
| Gradle 9.5.0-bin va bog'liqliklar, `~\.gradle` (to'xtatilgan build'dan keyin) | o'lchanmagan | 1.1 GB |

Zip'lar sha256 bilan tekshirildi va o'chirildi. `flutter doctor`: Flutter ✓, Android toolchain ✓
(hamma litsenziyalar qabul qilingan), Visual Studio ✗ — faqat Windows desktop uchun, kerak emas.
Flutter va Dart analytics o'chirilgan.

**Mahalliy build (2026-11-23):** birinchi `flutter build apk --debug` 15 daqiqada tugamadi va
to'xtatildi (foydalanuvchi sharti). Xotira (har ~2 s, 411 o'lchov): java eng ko'pi 1.5 GB, bo'sh
RAM eng kami 181 MB (48 o'lchovda 300 MB dan kam), committed 13.9 GB — 5.8 GB RAM'da tizim
diskka swap qiladi. Shablondagi `-Xmx8G` `-Xmx2G` ga tushirilgan. Shuning uchun **asosiy yo'l —
CI'dagi APK** (pastda).

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
- `C:\Users\User\.gradle` papkasi (Gradle va bog'liqliklar);
- `C:\Users\User\.android` (adb kaliti);
- `%LOCALAPPDATA%\kotlin` (Kotlin daemon, build paytida yaratilgan);
- `%APPDATA%\.dart-tool`, `%APPDATA%\.flutter_settings`, `%APPDATA%\.flutter_tool_state`
  (Flutter va Dart sozlamalari, kichik);
- foydalanuvchi PATH'idagi bitta qator: `C:\Users\User\develop\flutter\bin`;
- foydalanuvchi o'zgaruvchisi `PUB_CACHE` (`C:\Users\User\develop\pub-cache`).

Ro'yxatga (registry) hech narsa yozilmaydi. Istisno — USB drayveri, u Device Manager orqali o'chiriladi.

## APK CI'dan (asosiy yo'l)

`.github/workflows/android.yml` har push'da (`apps/mobile` o'zgarsa) `flutter analyze`,
`flutter test` va `flutter build apk --debug` ni bajaradi va APK'ni artifact qiladi (14 kun).

1. GitHub'ga kiring (artifact'ni faqat kirgan foydalanuvchi yuklay oladi) → repo → **Actions** →
   chapda **android** → branch'dagi oxirgi yashil run → pastda **Artifacts** →
   `movie-match-debug-...` → zip yuklanadi. Ichida `app-debug.apk`.
2. **Oldingi build'ni o'chiring** (Sozlamalar → Ilovalar → Movie Match → O'chirish). Har CI run
   APK'ni o'zining vaqtinchalik debug kaliti bilan imzolaydi; imzo boshqa bo'lsa, Android ustiga
   o'rnatmaydi.
3. O'rnatish — ikki yo'l:
   - **USB orqali** (telefon ulangan, USB debugging yoqilgan): `adb install app-debug.apk`;
   - **kompyutersiz:** APK'ni telefonga yuboring (Telegram "Saqlangan xabarlar", Google Drive
     yoki USB fayl uzatish), Fayllar ilovasida oching, "Noma'lum ilovalarni o'rnatish"ga o'sha
     ilova uchun ruxsat bering → O'rnatish. Play Protect "noma'lum dasturchi" desa — "Baribir
     o'rnatish" (debug build Play'da emas).

## Flutter versiyasi — qaror

**3.50** o'rnatiladi (foydalanuvchi, 2026-11-23). `CLAUDE.md`, ADR 0001 va `README.md` 3.50 ga
yangilandi. O'rnatilgan: 3.50.1 (CI ham shu versiyada).
