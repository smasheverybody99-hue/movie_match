# Movie Match — Android ilovani o'rnatish (testerlar uchun)

Ilova hozircha Google Play'da yo'q (TZ 1.37). Uni **APK fayl** sifatida olasiz: tashkilotchi
sizga Telegram orqali yuboradi. Bu sinov versiyasi.

**Kerak:**
- Android 7.0 yoki yangiroq telefon;
- Gmail akkaunt (ilovaga Google orqali kirasiz);
- internet.

## O'rnatish

1. Telegram'da kelgan `movie-match-....apk` faylini bosing — u yuklab olinadi.
2. Yana bir marta bosing → **O'rnatish**.
   - Telefon "Bu manbadan ilova o'rnatishga ruxsat yo'q" desa: **Sozlamalar** ni bosing →
     **Shu manbadan ruxsat berish** ni yoqing (bu Telegram uchun) → orqaga qayting →
     **O'rnatish**.
3. Google Play Protect ogohlantirishi mumkin ("Noma'lum ilova" yoki "Xavfli bo'lishi
   mumkin"). **Batafsil** → **Baribir o'rnatish** ni bosing. Sababi: ilova Play'dan emas va
   sinov versiyasi.
4. Ilovani oching va **Google bilan kirish** ni tanlang.

Xiaomi, Redmi va POCO telefonlari o'rnatishdan oldin o'zlarining xavfsizlik tekshiruvini
ko'rsatishi mumkin. Unda ham **O'rnatish** ni bosing.

## Yangi versiya kelganda

Yangi APK'ni yuqoridagidek oching va **Yangilash** (yoki **O'rnatish**) ni bosing. U eskisining
ustiga o'rnatiladi, qayta kirish shart emas.

Telefon "Ilova o'rnatilmadi" desa (tashkilotchi bu haqda oldindan yozadi, masalan birinchi
"doimiy" versiyaga o'tishda):

1. Eski ilovani o'chiring: ikonkani bosib turing → **O'chirish** (yoki Sozlamalar →
   Ilovalar → Movie Match → O'chirish).
2. Yangi APK'ni o'rnating.
3. Qayta kiring. Baholaringiz, watchlist va Movie DNA serverda saqlanadi, ular
   yo'qolmaydi.

## Muammo bo'lsa

Tashkilotchiga yozing:
- telefon modeli va Android versiyasi (Sozlamalar → Telefon haqida);
- nima qilganingiz va nima bo'lgani;
- iloji bo'lsa, skrinshot.

---

## Tashkilotchi uchun: APK'ni qayerdan olish

APK'ni GitHub Actions yig'adi (`.github/workflows/android.yml`) — `apps/mobile` ga
tegadigan har push'dan keyin.

1. GitHub'ga kiring (artifact'ni faqat kirgan foydalanuvchi yuklay oladi) → repo →
   **Actions** → chapda **android** → kerakli branch'dagi oxirgi yashil run.
2. Pastda **Artifacts** → `movie-match-...` → zip yuklanadi. Ichida `app-release.apk`
   (signing secret'lari qo'shilmagan bo'lsa — `movie-match-debug-...` va `app-debug.apk`).
3. Faylni, masalan, `movie-match-2026-11-30.apk` deb qayta nomlang va testerlar guruhiga
   Telegram orqali yuboring. Yangi versiya ekanini yozing; eskisini o'chirish kerak
   bo'lsa (debug'dan release'ga o'tish), buni alohida ayting.

Artifact 14 kun saqlanadi. Release APK'lar bitta doimiy kalit bilan imzolanadi
(`docs/setup-android.md`, "Release kaliti"), shuning uchun yangisi eskisining ustiga
o'rnatiladi. Debug APK'dan release'ga o'tishda testerlar bir marta o'chirib qayta o'rnatadi:
buni guruhga yozing.
