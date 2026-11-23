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

Har bir sinov versiyasi boshqa kalit bilan imzolanadi, shuning uchun yangisi eskisining
ustiga o'rnatilmaydi. Telefon "Ilova o'rnatilmadi" deydi.

1. Eski ilovani o'chiring: ikonkani bosib turing → **O'chirish** (yoki Sozlamalar →
   Ilovalar → Movie Match → O'chirish).
2. Yangi APK'ni yuqoridagidek o'rnating.
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
2. Pastda **Artifacts** → `movie-match-debug-...` → zip yuklanadi. Ichida `app-debug.apk`.
3. Faylni, masalan, `movie-match-2026-11-30.apk` deb qayta nomlang va testerlar guruhiga
   Telegram orqali yuboring. Yangi versiya ekanini va eskisini o'chirish kerakligini
   yozing.

Artifact 14 kun saqlanadi. Har bir run'ning debug kaliti boshqa, shuning uchun
testerlar har yangilanishda eski ilovani o'chirib, yangisini o'rnatadi.
