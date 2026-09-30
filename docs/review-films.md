# Trait review list — 50 films

1-fazadagi qo'lda ko'rik uchun filmlar. Trait run'ining 1-bosqichi aynan shularni
baholaydi, keyin `report.py` ularning raqamlarini chiqaradi va odam ularni tekshiradi.
1-faza qoidasi: 50 tadan 5 tasidan ko'prog'i aniq noto'g'ri bo'lsa, 2-bosqichdan oldin
trait prompti tuzatiladi.

**Holat: tasdiqlangan (2026-09-30).** 50 film, hammasi katalogda. 23-o'rin
dastlab *Home Alone* (1990) edi; u katalogda yo'q bo'lgani uchun foydalanuvchi uning
o'rniga *Dumb and Dumber* (1994) ni tanladi.

## Nega aynan shu filmlar

Bu ro'yxat mexanik tanlanmagan. Filmlarni foydalanuvchi o'zi tanlagan — hammasini ko'rgan.
Sabab oddiy: ko'rilmagan filmning trait raqamini hech kim tekshira olmaydi. "Sirlilik 85"
to'g'rimi yoki yo'qmi, buni faqat filmni eslaydigan odam aytadi.

Shu sababli o'n yillik va til taqsimoti avvalgi qoralamadagidek emas (u eng ko'p ovoz
olgan filmlardan o'n yillik bo'yicha tanlangan edi). Hozirgi ro'yxat:

- **Yillar:** asosan 1990–2023 (1985 dan bitta film). O'n yilliklar bo'yicha: 1980-lar 1,
  1990-lar 11, 2000-lar 14, 2010-lar 20, 2020-lar 4.
- **Til:** ingliz tili ustun — 48 ta; 2 ta yapon animatsiyasi (*Spirited Away*,
  *Your Name.*).
- **Janr:** 13 ta animatsiya; triller, sirli va psixologik filmlar ko'p.

**Bu ataylab.** Ko'rik trait raqamlari to'g'riligini tekshiradi, katalogning xilma-xilligini
emas. Katalog kvotalari (TZ FR-2) katalogga tegishli, bu ro'yxatga emas. Keng doiradagi
tekshiruv — 2-bosqichdagi 500 film.

## Almashtirilgan film

- **23-o'rin.** Foydalanuvchi ro'yxatida *Home Alone* (1990) edi. U katalogda yo'q (TMDB id
  771 bo'yicha ham, nomi bo'yicha ham; faqat davomlari bor), shuning uchun foydalanuvchi
  uning o'rniga *Dumb and Dumber* (1994, id 8467) ni tanladi. Katalogda uning 2014-yilgi
  davomi *Dumb and Dumber To* (100042) ham bor — ro'yxatdagisi 1994-yilgi asl film.

Bu bo'lim ataylab jadval emas: `--ids` fayldagi har bir jadval qatorining birinchi
ustunini TMDB id deb o'qiydi.

## Qanday tahrirlash

- Jadval shaklini saqlang. Faqat birinchi ustun o'qiladi; qolganlari ko'ruvchi uchun.
- Almashtiruvchi katalogda bo'lishi kerak. Tekshirish:
  `python -m app.pipelines.report <id>` — katalogda bo'lmasa "not in the catalogue" deydi.
- TMDB id film URL'ida bor: themoviedb.org/movie/**550**-fight-club.

## Qanday ishlatiladi (`services/api` ichidan)

```
python -m app.pipelines.traits submit --ids ../../docs/review-films.md --dry-run
python -m app.pipelines.traits submit --ids ../../docs/review-films.md --yes   # pullik
python -m app.pipelines.report ../../docs/review-films.md
```

`--yes` bilan ishga tushirish — pullik run. U faqat provayder tanlangandan va narx
tasdiqlangandan keyin qilinadi (CLAUDE.md, ADR 0006).

## Films

Tartib — foydalanuvchi ro'yxatidagi tartib. Id, yil, til va janrlar katalogdan
(asosiy baza, 2026-09-30) o'qilgan.

| TMDB id | Title | Year | Lang | Genres | Verdict |
|---:|---|---:|---|---|---|
| 550 | Fight Club | 1999 | en | Drama, Thriller | |
| 807 | Se7en | 1995 | en | Crime, Mystery, Thriller | |
| 475557 | Joker | 2019 | en | Crime, Drama, Thriller | |
| 11324 | Shutter Island | 2010 | en | Drama, Mystery, Thriller | |
| 44214 | Black Swan | 2010 | en | Drama, Horror, Thriller | |
| 146233 | Prisoners | 2013 | en | Crime, Drama, Thriller | |
| 210577 | Gone Girl | 2014 | en | Drama, Mystery, Thriller | |
| 27205 | Inception | 2010 | en | Action, Adventure, Science Fiction | |
| 157336 | Interstellar | 2014 | en | Adventure, Drama, Science Fiction | |
| 1124 | The Prestige | 2006 | en | Drama, Mystery, Science Fiction | |
| 77 | Memento | 2000 | en | Mystery, Thriller | |
| 329865 | Arrival | 2016 | en | Drama, Mystery, Science Fiction | |
| 278 | The Shawshank Redemption | 1994 | en | Crime, Drama | |
| 13 | Forrest Gump | 1994 | en | Comedy, Drama, Romance | |
| 597 | Titanic | 1997 | en | Drama, Romance | |
| 155 | The Dark Knight | 2008 | en | Action, Crime, Thriller | |
| 98 | Gladiator | 2000 | en | Action, Adventure, Drama | |
| 245891 | John Wick | 2014 | en | Action, Thriller | |
| 299534 | Avengers: Endgame | 2019 | en | Action, Adventure, Science Fiction | |
| 438631 | Dune | 2021 | en | Adventure, Science Fiction | |
| 106646 | The Wolf of Wall Street | 2013 | en | Comedy, Crime, Drama | |
| 293660 | Deadpool | 2016 | en | Action, Adventure, Comedy | |
| 8467 | Dumb and Dumber | 1994 | en | Comedy | |
| 313369 | La La Land | 2016 | en | Comedy, Drama, Romance | |
| 38 | Eternal Sunshine of the Spotless Mind | 2004 | en | Drama, Romance, Science Fiction | |
| 11036 | The Notebook | 2004 | en | Drama, Romance | |
| 129 | Spirited Away | 2001 | ja | Animation, Family, Fantasy | |
| 354912 | Coco | 2017 | en | Adventure, Animation, Family, Music | |
| 150540 | Inside Out | 2015 | en | Adventure, Animation, Comedy, Drama, Family | |
| 324857 | Spider-Man: Into the Spider-Verse | 2018 | en | Action, Adventure, Animation, Science Fiction | |
| 10681 | WALL·E | 2008 | en | Animation, Family, Science Fiction | |
| 372058 | Your Name. | 2016 | ja | Animation, Drama, Romance | |
| 105 | Back to the Future | 1985 | en | Adventure, Comedy, Science Fiction | |
| 280 | Terminator 2: Judgment Day | 1991 | en | Action, Science Fiction, Thriller | |
| 329 | Jurassic Park | 1993 | en | Adventure, Science Fiction | |
| 8587 | The Lion King | 1994 | en | Animation, Drama, Family | |
| 872585 | Oppenheimer | 2023 | en | Drama, History | |
| 530915 | 1917 | 2019 | en | Drama, History, War | |
| 414906 | The Batman | 2022 | en | Crime, Mystery, Thriller | |
| 640 | Catch Me If You Can | 2002 | en | Crime, Drama | |
| 37165 | The Truman Show | 1998 | en | Comedy, Drama | |
| 75656 | Now You See Me | 2013 | en | Crime, Thriller | |
| 671 | Harry Potter and the Philosopher's Stone | 2001 | en | Adventure, Fantasy | |
| 634649 | Spider-Man: No Way Home | 2021 | en | Action, Adventure, Science Fiction | |
| 808 | Shrek | 2001 | en | Adventure, Animation, Comedy, Family, Fantasy | |
| 862 | Toy Story | 1995 | en | Adventure, Animation, Comedy, Family | |
| 14160 | Up | 2009 | en | Adventure, Animation, Comedy, Family | |
| 2062 | Ratatouille | 2007 | en | Animation, Comedy, Family, Fantasy | |
| 9502 | Kung Fu Panda | 2008 | en | Action, Animation, Comedy, Family | |
| 109445 | Frozen | 2013 | en | Adventure, Animation, Family, Fantasy | |

Verdict ustuni: ko'rik paytida `ok` yoki `wrong: <qaysi trait, va nega>` yoziladi.
