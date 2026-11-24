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
2. **Imzo.** Secret'lar qo'shilgach (pastda, "Release kaliti") APK release build, doimiy kalit
   bilan imzolangan: yangisi eskisining ustiga o'rnatiladi. Secret'larsiz u debug build, har
   run'da boshqa kalit — oldingi build'ni o'chirib o'rnatiladi. Debug'dan release'ga o'tishda bir
   marta o'chirish kerak.
3. O'rnatish — ikki yo'l:
   - **USB orqali** (telefon ulangan, USB debugging yoqilgan): `adb install app-debug.apk`;
   - **kompyutersiz:** APK'ni telefonga yuboring (Telegram "Saqlangan xabarlar", Google Drive
     yoki USB fayl uzatish), Fayllar ilovasida oching, "Noma'lum ilovalarni o'rnatish"ga o'sha
     ilova uchun ruxsat bering → O'rnatish. Play Protect "noma'lum dasturchi" desa — "Baribir
     o'rnatish" (debug build Play'da emas).

## Muammo bo'lsa: kirish

**Google bilan kirgandan keyin brauzer ilovaga qaytmay, web saytga ketadi.** Sabab: Supabase
**asosiy** loyihasida Redirect URLs ro'yxatida ilovaning manzili yo'q. Supabase ro'yxatda
yo'q manzil o'rniga Site URL'ga (web sayt) yuboradi. Tuzatish:

1. Supabase → **asosiy** loyiha (test loyihasi emas) → **Authentication** → **URL
   Configuration**.
2. **Redirect URLs** → **Add URL** → `com.moviematch.moviematch://login-callback` → **Save**.
3. Telefonda qaytadan "Google bilan davom etish". Yangi APK kerak emas.

2026-11-24 da aynan shu bo'lgan: manzil asosiy loyihada yo'q edi, foydalanuvchi qo'shgach
kirish ishladi. Tekshirish: ilova sozlamasi `SUPABASE_URL` (GitHub Actions variable) qaysi
loyihaga ishora qilsa, manzil o'sha loyihada bo'lishi kerak.

**"Kirish mavjud emas" deyiladi** — APK `SUPABASE_URL` / `SUPABASE_ANON_KEY` siz yig'ilgan:
android run'da "Sign-in settings present" ogohlantirishi bo'ladi (pastda, "Release kaliti" va
GitHub variables).

## Release kaliti (TZ 1.38)

Testerlarga beriladigan APK bitta doimiy kalit bilan imzolanadi: yangi versiya eskisining
ustiga o'rnatiladi. Keyinchalik Google Play'da xuddi shu kalit **upload key** bo'ladi.

**Kalit** (yaratildi 2026-11-23, JDK `keytool`):
- fayl: `C:\Users\User\.moviematch-keys\movie-match-release.jks` — PKCS12, RSA 2048, alias
  `upload`, 2054-04-10 gacha amal qiladi;
- egasi: `CN=Movie Match, O=Movie Match, C=UZ` (shaxsiy ma'lumot yo'q);
- sertifikat SHA-256 (ochiq ma'lumot, `.github/workflows/android.yml` shu bilan tekshiradi):
  `8D:72:C8:E5:50:67:2A:22:53:06:37:F2:EC:0B:09:38:6F:35:0B:FA:B7:E5:CA:C7:75:7B:AE:05:C7:B0:26:42`.

Kalit papkasi repo'dan ham, `develop` dan ham tashqarida: `develop` ni o'chirish (pastdagi
"Qaytarish") kalitga tegmaydi. Repo `*.jks`, `*.keystore`, `key.properties` va
`keystore-*.txt` ni ignore qiladi (`git check-ignore` bilan tekshirilgan).

Papkada uchta fayl bor:

| Fayl | Nima | Keyin |
|---|---|---|
| `movie-match-release.jks` | Kalitning o'zi | Saqlanadi (pastda) |
| `keystore-password.txt` | Parol (kalit va ombor uchun bitta) | Parol menejeriga ko'chiriladi, fayl o'chiriladi |
| `keystore-base64.txt` | `.jks` ning base64 ko'rinishi, GitHub secret uchun | Secret qo'shilgach o'chiriladi |

### GitHub secret'larini qo'shish

1. GitHub → repo → **Settings** → chapda **Secrets and variables** → **Actions** →
   **New repository secret**.
2. Name: `ANDROID_KEYSTORE_BASE64`. Secret: `keystore-base64.txt` ning butun matni (Notepad'da
   oching → Ctrl+A → Ctrl+C → joylang). → **Add secret**.
3. Yana **New repository secret**. Name: `ANDROID_KEYSTORE_PASSWORD`. Secret:
   `keystore-password.txt` ning matni (bo'sh joy va yangi qatorsiz). → **Add secret**.
4. Tekshirish: `apps/mobile` ga tegadigan keyingi push'da (yoki Actions → android →
   **Run workflow**) run'da "flutter build apk --release" qadami yashil, artifact nomi
   `movie-match-<sha>` (`-debug` siz) bo'ladi. Imzo noto'g'ri kalit bilan bo'lsa, run yiqiladi.
5. Ishlagach `keystore-base64.txt` ni o'chiring. `keystore-password.txt` ni parol
   menejeriga ko'chirgandan keyin o'chiring.

GitHub secret'ni qaytarib ko'rsatmaydi: u faqat CI ichida ishlatiladi, zaxira nusxa emas.

### Zaxira nusxasi

Kalit va parol **ikki joyda, alohida** saqlanadi:

- **Parol** — parol menejerida (masalan, Bitwarden yoki Google Password Manager,
  "Movie Match release key" nomi bilan). Telegram, email yoki repo'da emas.
- **`.jks` fayl** — kamida bitta nusxa noutbukdan tashqarida:
  - shifrlangan arxiv (7-Zip, AES-256, arxiv uchun **boshqa** parol, u ham menejerda),
    Google Drive yoki boshqa bulutda; va/yoki
  - USB fleshka, uyda saqlanadi.
- Nusxani tekshirish: arxivni ochib, `keytool -list -keystore <fayl>` paroldan keyin
  `upload` alias'ini ko'rsatsa, nusxa ishlaydi.

**Yo'qolsa:**
- *Hozir (APK, Play'siz):* yangi kalit yaratiladi, CI secret'lari almashtiriladi. Har bir
  tester ilovani **bir marta o'chirib**, qayta o'rnatadi. Baholar, watchlist va DNA serverda,
  ular yo'qolmaydi.
- *Play'da (F9b dan keyin):* bu kalit upload key bo'ladi, ilovani imzolash kalitini esa Google
  saqlaydi (Play App Signing). Upload key yo'qolsa, Play Console'da yangisini so'rash mumkin
  (Google tasdig'i bir necha kun olishi mumkin). Ilova yo'qolmaydi.

**Begona qo'lga tushsa:** u odam testerlarning telefonidagi ilova ustiga o'z APK'sini
o'rnatishi mumkin bo'ladi (Play'siz tarqatishda imzo — yagona himoya). Kalitni
almashtiring va testerlarga yangisini qayta o'rnatishni ayting.

## Flutter versiyasi — qaror

**3.50** o'rnatiladi (foydalanuvchi, 2026-11-23). `CLAUDE.md`, ADR 0001 va `README.md` 3.50 ga
yangilandi. O'rnatilgan: 3.50.1 (CI ham shu versiyada).
