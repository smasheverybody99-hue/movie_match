# Trait review list — 50 films

The films used for the Phase 1 hand review: stage 1 of the trait run scores these, then
`report.py` prints their scores for a person to judge. Phase 1 rule: if more than 5 of
the 50 are clearly wrong, the trait prompt needs work before stage 2.

**Status: draft (2026-09-25).** Picked mechanically, not by a person: the most-voted
films on TMDB in our catalogue (votes are the best available proxy for "widely known"),
spread by decade, English capped at ~60% per decade, released before 2025 so the model
is likely to know them. It leans towards sci-fi and action blockbusters and has no
documentary. **Replace any film you don't know well** — the review only works on films
the reviewer can judge.

## How to edit

- Keep the table shape. Only the first column is read; the rest is for the reviewer.
- A replacement must be in the catalogue. Check with
  `python -m app.pipelines.report <id>` — it says "not in the catalogue" otherwise.
- TMDB ids are in the film's URL: themoviedb.org/movie/**550**-fight-club.

## How it is used (from `services/api`)

```
python -m app.pipelines.traits submit --ids ../../docs/review-films.md --dry-run
python -m app.pipelines.traits submit --ids ../../docs/review-films.md --yes   # paid
python -m app.pipelines.report ../../docs/review-films.md
```

## Films

| TMDB id | Title | Year | Lang | Genres | Verdict |
|---:|---|---:|---|---|---|
| 19 | Metropolis | 1927 | de | Drama, Science Fiction | |
| 408 | Snow White and the Seven Dwarfs | 1937 | en | Animation, Family, Fantasy | |
| 832 | M | 1931 | de | Crime, Drama, Thriller | |
| 10895 | Pinocchio | 1940 | en | Animation, Family, Fantasy | |
| 15 | Citizen Kane | 1941 | en | Drama, Mystery | |
| 5156 | Bicycle Thieves | 1948 | it | Drama | |
| 389 | 12 Angry Men | 1957 | en | Drama | |
| 567 | Rear Window | 1954 | en | Drama, Mystery, Thriller | |
| 346 | Seven Samurai | 1954 | ja | Action, Drama | |
| 62 | 2001: A Space Odyssey | 1968 | en | Adventure, Mystery, Science Fiction | |
| 539 | Psycho | 1960 | en | Horror, Mystery, Thriller | |
| 429 | The Good, the Bad and the Ugly | 1966 | it | Western | |
| 335 | Once Upon a Time in the West | 1968 | it | Drama, Western | |
| 238 | The Godfather | 1972 | en | Crime, Drama | |
| 11 | Star Wars | 1977 | en | Action, Adventure, Science Fiction | |
| 348 | Alien | 1979 | en | Horror, Science Fiction | |
| 11906 | Suspiria | 1977 | it | Horror | |
| 1398 | Stalker | 1979 | ru | Drama, Science Fiction | |
| 105 | Back to the Future | 1985 | en | Adventure, Comedy, Science Fiction | |
| 694 | The Shining | 1980 | en | Horror, Thriller | |
| 1891 | The Empire Strikes Back | 1980 | en | Action, Adventure, Science Fiction | |
| 1892 | Return of the Jedi | 1983 | en | Action, Adventure, Science Fiction | |
| 8392 | My Neighbor Totoro | 1988 | ja | Animation, Family, Fantasy | |
| 149 | Akira | 1988 | ja | Action, Animation, Science Fiction | |
| 550 | Fight Club | 1999 | en | Drama, Thriller | |
| 278 | The Shawshank Redemption | 1994 | en | Crime, Drama | |
| 680 | Pulp Fiction | 1994 | en | Comedy, Crime, Thriller | |
| 13 | Forrest Gump | 1994 | en | Comedy, Drama, Romance | |
| 101 | Léon: The Professional | 1994 | fr | Action, Crime, Drama | |
| 637 | Life Is Beautiful | 1997 | it | Comedy, Drama | |
| 18 | The Fifth Element | 1997 | fr | Action, Adventure, Science Fiction | |
| 155 | The Dark Knight | 2008 | en | Action, Crime, Thriller | |
| 19995 | Avatar | 2009 | en | Action, Adventure, Science Fiction | |
| 671 | Harry Potter and the Philosopher's Stone | 2001 | en | Adventure, Fantasy | |
| 1726 | Iron Man | 2008 | en | Action, Adventure, Science Fiction | |
| 120 | The Lord of the Rings: The Fellowship of the Ring | 2001 | en | Action, Adventure, Fantasy | |
| 129 | Spirited Away | 2001 | ja | Animation, Family, Fantasy | |
| 194 | Amélie | 2001 | fr | Comedy, Romance | |
| 1417 | Pan's Labyrinth | 2006 | es | Drama, Fantasy, War | |
| 157336 | Interstellar | 2014 | en | Adventure, Drama, Science Fiction | |
| 27205 | Inception | 2010 | en | Action, Adventure, Science Fiction | |
| 24428 | The Avengers | 2012 | en | Action, Adventure, Science Fiction | |
| 293660 | Deadpool | 2016 | en | Action, Adventure, Comedy | |
| 299536 | Avengers: Infinity War | 2018 | en | Action, Adventure, Science Fiction | |
| 496243 | Parasite | 2019 | ko | Comedy, Drama, Thriller | |
| 77338 | The Intouchables | 2011 | fr | Comedy, Drama | |
| 372058 | Your Name. | 2016 | ja | Animation, Drama, Romance | |
| 634649 | Spider-Man: No Way Home | 2021 | en | Action, Adventure, Science Fiction | |
| 438631 | Dune | 2021 | en | Adventure, Science Fiction | |
| 664413 | 365 Days | 2020 | pl | Crime, Drama, Romance | |

Verdict column: fill in `ok` or `wrong: <which trait, and why>` during the review.
