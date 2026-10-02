# Phase 1 — status

Last updated: 2026-10-02 · Phase: **1 (data foundation). Data part closed for the
500-film list:** traits 500/500, embeddings 500/500, missing count 0, nearest-neighbour
check passed (user, 2026-10-02). One known issue, below

Phase prompt: `docs/prompts/phase-01-data.md`. Adjustments for this run (from the user):
catalogue of 5,000 not 20,000 (TZ v1.2 now says the same); TMDB ingestion run for real;
trait extraction and embeddings on Gemini, one vendor for both (2026-09-26, ADR 0004). **No paid API call — not even one film — until the user has
seen the estimate below and said go.**

## Is Phase 1 finished?

**No.** The code is finished and the gate is green; the data is not there yet. The phase
prompt makes the manual checklist part of the phase:

| Checklist item | State |
|---|---|
| Every film has a trait vector and an embedding (missing count must be 0) | **Done for the 500-film list** (2026-10-02, read-only query below): 0 missing traits, 0 missing embeddings. The other 4,500 ingested films have neither, as TZ 1.5 plans |
| Run the pipeline on real films; report cost and time | **Stage 1 done** (2026-10-01): 50 films, 50 stored, 0 failed. Below |
| 50-film hand review; no more than 5 clearly wrong | **Passed** (2026-10-01): 3 of 50 disputed, limit 5. Below |
| Nearest neighbours of 5 films, checked by eye | **Passed** (user, 2026-10-02). Known issue: studio clustering on Spirited Away, below |
| Measured cost per 1,000 films | **Measured**: traits 380 in / 195 out tokens per film; embeddings 182 tokens per film. Below |

The phase report's items 2–4 (review table and verdict, measured cost, trait definitions
that did not work in practice) cannot be written until those are done.

The phase prompt says "run the pipeline on 200 films"; that step is **dropped** (user,
2026-09-27): the 500-film stage covers it. The 200 predates the agreed 50 → 500 → 5,000
staging (CLAUDE.md).

## Stage 1 — 50 films, run and hand review (2026-10-01)

**Run.** `traits submit --ids ../../docs/review-films.md --yes` with `TRAIT_MODE=sync`
(one film per request; the account's batch submits are refused, ADR 0006 amendment),
`gemini-3.5-flash-lite`, 10 requests per minute. Result: **50 stored, 0 failed**, no 429,
no quota stop. The `app.cost` line:

```
run=traits-sync provider=gemini model=gemini-3.5-flash-lite requests=50 input_tokens=18976
output_tokens=9746 usd=0.0301 tokens=reported
```

- Cost: **$0.0301 at the paid standard rate; $0 on the free tier**, which this key
  appears to be on (batch refused, sync accepted; not provable from the key).
- Tokens per film: **380 in, 195 out** (thinking included), against the 410 / 250
  estimate: input 14% lower, output 22% lower. `docs/costs.md` now uses the measured
  numbers.
- Per 1,000 films, measured: ~$0.60 sync at the standard rate, ~$0.30 batch.
- Time: at least ~4.9 minutes by the pacing (49 pauses of 6 s); the wall-clock time was
  not recorded.

**Review.** The user, who has seen all 50 films, judged every row of `report.py`
(verdicts in `docs/review-films.md`): **47 ok, 3 disputed** — under the limit of 5, so
the prompt stands and stage 2 may go ahead once approved.

| Film | Verdict |
|---|---|
| Titanic (597) | action 70 too high: a sinking disaster, not an action film |
| The Shawshank Redemption (278) | plot_twist 35 too low: the escape reveal is a major twist |
| Frozen (109445) | romance 30 too low |

Pattern worth watching at 500: two of the three are a dimension read too literally
(*action* for spectacle and peril, *plot_twist* for a reveal that is not a mystery
twist). No change to the prompt now — 3 of 50 is within the rule — but the trait
definitions are where to look if stage 2 shows more of the same.

## Stage 2 — 500 films, first attempt (2026-10-01): stopped at 247 of 500

The 500 are `docs/catalogue-500.md` (decade and language quotas over our catalogue,
`scripts/select_catalogue.py`; the 50 reviewed films pinned). The user approved 450 new
films in sync mode. The run stopped at 12:19 after **197 stored and 1 failed**, on a
dropped database connection (`ConnectionDoesNotExistError` while saving *Beauty and the
Beast*), not on a quota: no 429, no FAILED_PRECONDITION. The failed film is *Exploits of a
Young Don Juan* (1986): Google blocked the prompt (`PROHIBITED_CONTENT`).

Its cost line was never written (it came at the end), so the run's real tokens are
lost; estimated from stage 1, ~199 requests ≈ 75,600 in / 38,800 out ≈ $0.12 at the
standard rate, $0 on the free tier. Both gaps are fixed: the sync run now reconnects
(`ingest.with_reconnect`) and writes its cost line in `finally` with a `status`.
**253 films are still pending**; the same command continues with them.

## Stage 2 — continuation (2026-10-01, 12:42–13:29): complete

Same command, the 253 pending films. **241 stored, 19 failed attempts**; the connection
dropped twice (`ReadError`, then a DNS `gaierror`) and the run reconnected by itself both
times. No 429, no quota, no FAILED_PRECONDITION. The cost line, written this time:

```
run=traits-sync provider=gemini model=gemini-3.5-flash-lite requests=260 input_tokens=94800
output_tokens=47199 usd=0.1464 tokens=reported status=complete
```

- **$0.1464 at the standard rate; $0 on the free tier.** Per request 365 in / 182 out,
  against stage 1's 380 / 195 per film (blocked prompts use input tokens and return none,
  which pulls the average down).
- **Stage 2 in total ≈ $0.27 at the standard rate** ($0.1464 measured + ≈ $0.12
  estimated for the first attempt, whose cost line was lost), $0 on the free tier.
- The 19 failed attempts are **12 films**, every one blocked by Google's safety filter
  (`PROHIBITED_CONTENT`: the prompt itself was refused, no answer). Seven of them were
  asked twice because a reconnect re-read them as pending — wasted requests, now fixed:
  a blocked prompt is final at once.

### 12 films excluded from the trait list (Google safety filter)

All twelve stay in the 5,000-film catalogue; they are only out of the 500 to score.
Their slots went to the next films by the same quota rules (`scripts/select_catalogue.py`
skips given-up films; `docs/catalogue-500.md` lists both). Reason for each:
`no candidates (prompt blocked: BlockedReason.PROHIBITED_CONTENT)` — Gemini refused the
prompt, most likely for sexual themes in the TMDB keywords or overview.

| TMDB id | Film | Year | Lang |
|---:|---|---:|---|
| 27098 | All Things Fair | 1995 | sv |
| 19173 | Diary of a Nymphomaniac | 2008 | es |
| 1440098 | Drawn Together | 2026 | es |
| 118451 | Eungyo | 2012 | ko |
| 81774 | Exploits of a Young Don Juan | 1986 | fr |
| 53064 | Midori | 1992 | ja |
| 1010581 | My Fault | 2023 | es |
| 670 | Oldboy | 2003 | ko |
| 519465 | Queen of Hearts | 2019 | da |
| 10995 | The Lover | 1992 | fr |
| 1791 | The Piano Teacher | 2001 | fr |
| 1232449 | Young Hearts | 2024 | nl |

(This table is in a status page, not an `--ids` list; do not pass this file to `--ids`.)

**Bringing them back later** is possible: delete a film's row from `trait_failures` and
it is pending again, and `select_catalogue` will consider it again. It only makes sense
with something that changes the outcome — a different provider (ADR 0006), or a prompt
that leaves out the keywords that trip the filter. Four of the twelve had one attempt
recorded before the rule changed; they were set to given-up by hand (4 rows,
`attempts` 1 -> 2, guarded by id and error text) so all twelve are treated alike.

### Replacements scored, and a 13th exclusion (2026-10-01, evening)

- The 12 replacements: **11 stored, 1 blocked**, cost line `requests=12 input_tokens=4372
  output_tokens=2157 usd=0.0067 tokens=reported status=complete` ($0 on the free tier).
  The blocked one, *Hope* (2013, ko, TMDB 255709), was given up at once by the new rule
  (one request, `PROHIBITED_CONTENT`).
- *Hope* was excluded the same way as the twelve (user's limit: replace once more, and
  stop at 499 if that one is blocked too). Its replacement, *The Third One* (2014, es,
  TMDB 261776), stored: `requests=1 input_tokens=358 output_tokens=188 usd=0.0006
  status=complete`. **Traits: 500 of 500.** Excluded films: 13 (the twelve above and
  *Hope*, all `PROHIBITED_CONTENT`), listed in `docs/catalogue-500.md`.

## Embeddings — first run (2026-10-01, 22:27–22:57): stopped at 258 of 500

`embeddings --ids ../../docs/catalogue-500.md --yes`, Gemini Embedding 2 at 1,536-d, one
film per request. **258 stored**, then interrupted: Google's server dropped the
connection on an `embed_content` call (`httpx.RemoteProtocolError: Server disconnected
without sending a response`) after the SDK's own short retry. Not a quota, not the
database. The cost line, written in `finally`:

```
run=embeddings provider=gemini model=gemini-embedding-2 requests=258 input_tokens=47554
output_tokens=0 usd=0.0095 tokens=reported status=interrupted
```

$0.0095 at the standard rate, $0 on the free tier; 184 tokens per film, counted by
`count_tokens` (the one-film test measured 187). Throughput was ~8.6 films a minute, not
the 20 the pacing allows: each film is an embedding call, a count call and a commit to
the database in Singapore.

**Gap found and fixed (2026-10-02):** network-level errors from the provider
(`httpx.TransportError`) were not translated to `TransientError`, so neither the retry nor
the reconnect caught this one; the same gap was on the sync trait path and in
`count_tokens`. They are now transient (ADR 0006, item 8), with tests. The remaining
**242** films continue with the same command.

## Embeddings — second run (2026-10-02, 10:38–11:06): complete

The same command, after the network fix. **242 stored**, no interruption:

```
run=embeddings provider=gemini model=gemini-embedding-2 requests=242 input_tokens=43522
output_tokens=0 usd=0.0087 tokens=reported status=complete
```

**Both runs together:** 500 films, 91,076 tokens (182 per film, counted by
`count_tokens`), **$0.0182** at the standard rate, $0 on the free tier.

### Missing count (2026-10-02, read-only transaction on the main database)

| | |
|---|---|
| 500-film list: without traits / without embeddings | **0 / 0** (500 have both) |
| `movie_traits` / `movie_embeddings` rows in total | 500 / 500, none outside the list |
| Embedding size, min / max | 1,536 / 1,536 |
| Films ingested / without traits | 5,000 / 4,500 (not part of this stage, TZ 1.5) |

### Nearest neighbours of 5 films (2026-10-02)

`find_similar` (`app/services/similarity.py`, cosine distance on the embeddings, no
filters), first 8 of the 500. Films from the review list, one per genre:

| Film | Neighbours (cosine distance) |
|---|---|
| Fight Club (1999) | Joker 0.188, Pulp Fiction 0.189, Eyes Wide Shut 0.201, Se7en 0.205, Battle Royale 0.206, The Matrix 0.207, Good Will Hunting 0.207, Parasite 0.208 |
| Spirited Away (2001) | Howl's Moving Castle 0.153, Kiki's Delivery Service 0.155, My Neighbor Totoro 0.160, Arrietty 0.163, The Boy and the Heron 0.166, Whisper of the Heart 0.169, Ponyo 0.170, Castle in the Sky 0.171 |
| The Notebook (2004) | Titanic 0.191, Eternal Sunshine of the Spotless Mind 0.191, You've Got Mail 0.209, Forrest Gump 0.214, The Shawshank Redemption 0.216, Gone with the Wind 0.226, Cinema Paradiso 0.226, In the Mood for Love 0.227 |
| John Wick (2014) | The Raid 2 0.181, Pulp Fiction 0.183, Léon: The Professional 0.184, Kill Bill: Vol. 1 0.185, Game of Death 0.196, Vengeance (2026) 0.201, Hard Boiled 0.203, Mutiny (2026) 0.204 |
| Arrival (2016) | Project Hail Mary 0.185, Inception 0.186, 2001: A Space Odyssey 0.188, Interstellar 0.192, Stalker 0.194, Alien 0.195, Blade Runner 2049 0.198, Dune 0.198 |

**Verdict (user, 2026-10-02): passed.**

- John Wick, Arrival, Fight Club: right.
- The Notebook: one wrong neighbour of 8, *The Shawshank Redemption* (not a romance).
  Borderline, passes.
- Spirited Away: all 8 are Studio Ghibli. Passes, but is a **known issue** (next).

### Known issue: studio clustering (Spirited Away) — look at it again in the F2 manual check

The user expected films like *Pan's Labyrinth* or *Coraline* among Spirited Away's
neighbours. Both are in the 500. Exact ranks (all 499 distances, computed in SQL without
the index, 2026-10-02):

| | Rank of 499 | Distance |
|---|---|---|
| Ghibli films | 1–9 (the 8 shown, then *The Cat Returns*) | 0.153–0.174 |
| First non-Ghibli: *Harry Potter and the Philosopher's Stone* | 10 | 0.178 |
| *Coraline* | 15 | 0.186 |
| *Pan's Labyrinth* | 56 | 0.222 |

What the embedding text holds (`build_embedding_text`): title and year, genres, keywords,
overview, the trait summary. **No studio or director field**, and no keyword among the
500 contains "ghibli" or "miyazaki". So the studio is not named; what the Ghibli films
share is the genre line (*Animation, Family, Fantasy*), the keyword *anime*, similar
keywords (*witch*, *magic*, *flying*), and whatever the model knows about the titles.
*Pan's Labyrinth* is not *Animation* at all, which fits its rank. Hypothesis, not tested:
animation and anime markers outweigh the content.

To look at in the F2 manual check (recommendations rank by traits after the embedding
proposes candidates, so the effect there may be smaller). Possible directions, none
chosen: put the trait summary first, drop the genre line, or rank by traits more
heavily. Any change to the text means embedding all films again.

### Distances are compressed: use the order, not a threshold

All 124,750 pairs of the 500 films: min 0.075, 1st percentile 0.198, **median 0.275**,
99th percentile 0.334, max 0.370. One film's neighbours (Spirited Away): 0.153 to 0.331.
So an absolute cut-off does not work: "similar below 0.2" would keep about 1% of pairs.
Only the relative order is meaningful, and these numbers change with the model, the text
and the catalogue. The same note is in `app/services/similarity.py`, where a "similar
films" feature would add one.

## Where things stand

| Step | State |
|---|---|
| `.env` + Supabase connection | Done. Main and test projects reachable, Postgres 17.6, pgvector 0.8.2 |
| Migrations | Main DB at `0002 (head)`. Round-trip test passes on the test DB |
| TMDB ingestion (5,000 films) | **Done**, run 1 finished, 0 missing |
| Trait pipeline | Gemini `gemini-3.5-flash-lite`, `TRAIT_MODE=sync` (ADR 0006). **Run: 500/500** on the list |
| Embeddings | Gemini `gemini-embedding-2` at 1,536-d behind the `Embedder` protocol. **Run: 500/500** on the list |
| Similarity service | Built and tested; tried by eye on 5 films (2026-10-02, above) |
| Review report | Built. Review list in `docs/review-films.md` (draft) |
| Gate | Passes: ruff, format, 199 tests (0 skipped, real test DB). Coverage: `app/pipelines/` 83.1%, `app/services/` 100% |

## What was built

All in `services/api`:

- `app/pipelines/tmdb.py` — the only module that knows TMDB field names. Rate limiter
  (20 req/s), backoff that honours `Retry-After`, no retry on 404, text clipped to column
  sizes at this boundary.
- `app/pipelines/catalogue.py` — picks the catalogue: decade quotas, no language over 55%
  of a decade while others have candidates, most popular first inside that.
- `app/pipelines/ingest.py` — resumable ingestion. Plan and cursor live in `sync_runs`;
  25-film chunks written with one statement per table; reconnects and resumes after a
  dropped connection.
- `app/pipelines/traits.py` — Gemini through the Batch API (ADR 0004). `--dry-run` prints the
  prompt and cost without an API call; a paid run needs `--yes`; `--limit N` or `--ids`.
  A malformed answer gets one retry, then the film is recorded in `trait_failures` —
  never stored with default scores.
- `app/pipelines/embeddings.py` — embedding text builder and storage behind an
  `Embedder` protocol, with a `GeminiEmbedder` (one request per film, retries on 429/5xx).
  `--dry-run` prints tokens and cost; a paid run needs `--yes`.
- `app/pipelines/gemini.py` — the one place the Gemini client is built.
- `app/services/similarity.py` — `find_similar()` over pgvector cosine distance, filters
  for year, runtime, language and max violence; returns trait vectors for Phase 2.
- `app/pipelines/report.py` — trait table for the 50-film hand review.
- Migration `0002`: `keywords`, `movie_keywords`, `sync_runs`, `trait_batches`,
  `trait_failures`.
- Tests: `tests/unit/` (no DB, no network) and `tests/integration/` (real test DB). The
  TMDB fixture is a real recorded response; Gemini results and requests are validated
  against the google-genai SDK's own types.

## The catalogue (measured in the database)

| | |
|---|---|
| Films | **5,000** (planned 5,000, missing 0, skipped 0) |
| Credits / people / keywords | 87,558 / 45,167 / 13,954 |
| Gaps | 83 films without keywords, 1 without overview, 1 without director |
| By decade | 1920s 63 · 1930s 125 · 1940s 188 · 1950s 250 · 1960s 312 · 1970s 375 · 1980s 500 · 1990s 687 · 2000s 875 · 2010s 1,000 · 2020s 625 |
| By language | 42 languages. en 2,877 (57.5%) · fr 569 · ja 442 · it 225 · es 170 · de 128 · cn 124 · ko 85 · zh 71 · sv 43 |
| Run time | 41 min wall clock, including three restarts |

English is above the 55% per-decade cap overall because the 1920s–40s pools had too few
non-English candidates; the fill-up rule then takes English films rather than leave the
quota short.

## Cost estimates (not yet measured)

Trait extraction, `gemini-3.5-flash-lite`, Batch API, paid tier ($0.15 in / $1.25 out
per million tokens; ADR 0004 has the alternatives):

| Stage | Films | Estimated cost |
|---|---|---|
| 1 — review list (`docs/review-films.md`) | 50 | **~$0.02** |
| 2 | 500 | **~$0.19** |
| 3 — full catalogue | 5,000 | **~$1.87** |

These are **estimates**: input tokens from real prompt length (~3.5 characters per
token), output assumed at 250 tokens per film. If answers, thinking tokens included,
run twice as long, the full catalogue is ~$3.43. Stage 1 replaces the estimate with
measured token counts (`collect` now prints them and the measured cost).

Embeddings: ~1.04M tokens for all 5,000 films at $0.20 per million = **~$0.21**
(standard API; the batch API would be ~$0.10 and is not used). Whole catalogue,
traits + embeddings: ~$2.08.

The trait numbers come from the real `submit --dry-run` command (re-run 2026-09-26 after
the switch). The embeddings number is a **projection**, not a dry-run: no film has traits
yet, so `embeddings --dry-run` finds 0 films. It was measured on the embedding text of all
5,000 films with a typical two-sentence summary added (mean 729 characters, longest 1,496;
none near the 8,192-token input limit).

## Bugs found during the real run, and the fixes

| # | What happened | Fix | Commit |
|---|---|---|---|
| 1 | Writing film by film would have spent ~2.4 h on network waits (~170 ms per round trip to Supabase) | One statement per table per 25-film chunk | `dedce7c` |
| 2 | Stopped at film 2,125: TMDB film 9473 has a 348-character character name (column holds 300). The failure could not even be recorded — the transaction was aborted | Text clipped to its column at the TMDB boundary; roll back before recording a failure | `421277f` |
| 3 | Network dropped at film 2,575 (`WinError 121`, then `ConnectionDoesNotExistError`) | Reconnect and resume from the saved cursor, up to 5 times; data errors still stop the run | `7a41a89` |
| 4 | The dropped connection left an orphaned session "idle in transaction" holding row locks; the next run timed out on them. The orphan was terminated by hand (`pg_terminate_backend`, nothing had been committed in it) | Job connections set `idle_in_transaction_session_timeout=60s` and `lock_timeout=20s`; lock waits are retried | `618cdcf` |
| 5 | A lock timeout exited instead of retrying: SQLAlchemy wraps asyncpg's error, so the class check missed it | Classify by SQLSTATE and the cause chain; tests build errors the way the driver raises them | `4f4e085` |

Found afterwards, while building the review list: the pipeline commands crashed printing
titles such as "Amélie" on a Windows console using code page 1251. Fixed — the commands
switch their output to UTF-8.

Also: `alembic.exe` is blocked on the dev machine (Smart App Control, most likely), so
migrations run as `python -m alembic upgrade head`. `tasks.ps1` / `tasks.sh` already do.

## Outstanding — needs a decision or a key

1. **Stage 1 not run.** Needs a working `GEMINI_API_KEY` (paid-tier project) and a go for
   ~$0.02.
   - **The key is configured.** `GEMINI_API_KEY` is in `services/api/.env`, read by
     `Settings.gemini_api_key` (`app/config.py`) and passed to the SDK in
     `app/pipelines/gemini.py`. Checked 2026-09-26 without printing it: loaded from `.env`
     (not the OS environment), 53 characters, no stray quotes or whitespace. It does not
     start with `AIza`, the older Google key format; whether it is valid is unverified.
   - **One unapproved live call was made.** While checking the no-key path, the agent
     ran `traits submit --limit 5 --yes`, not knowing the key had been added. Google
     rejected it: `400 FAILED_PRECONDITION: Precondition check failed`. No batch was
     created, nothing was recorded, and nothing should have been charged; the payload was 5
     films of public TMDB metadata. Cause not investigated. First suspect: billing not
     enabled on the key's project (enabling it is the user's action).
   - **Offered, awaiting a yes:** one free `models.list` call to check the key. Not made.

   Before stage 1, edit `docs/review-films.md` so every film is one the reviewer
   knows well. Then, from `services/api`:
   ```
   python -m app.pipelines.traits submit --ids ../../docs/review-films.md --dry-run
   python -m app.pipelines.traits submit --ids ../../docs/review-films.md --yes
   python -m app.pipelines.traits collect <batch name>    # batches/..., when the job has ended
   python -m app.pipelines.report ../../docs/review-films.md
   ```
   Pass rule: no more than 5 of the 50 clearly wrong. Then stage 2 (500), then stage 3
   — asking before each step up (CLAUDE.md).
2. **Embedding step: done** (2026-10-02), 500/500 on the list, two runs, above.
3. **Phase 1 manual checklist:** the 50-film review passed, cost per film is measured,
   missing count is 0. Open: the user's verdict on the 5 films' neighbours.
4. **Not built in this phase:** the daily TMDB re-sync that TZ FR-2 asks for (ingestion
   is resumable and idempotent, but nothing schedules it yet). Streaming providers were
   dropped from FR-2 in TZ v1.2.

## Housekeeping

- TZ v1.2 (`4fa0c07`), the Gemini switch (`f791ecd`) and its docs (`022801b`) are pushed
  to GitHub (`origin/main`).
- The README env table lists `GEMINI_API_KEY`. CLAUDE.md, `docs/architecture.md` and the
  phase prompts match ADR 0004 since 2026-09-27; two budget rows in `docs/roadmap.html`
  still need new numbers.
- `google-genai` 2.25 is installed in `services/api/.venv` and replaces `anthropic` in
  `pyproject.toml`. Re-add `anthropic` when the Phase 4 assistant is built.
- `.env.txt` at the repo root is an old copy of the local config and holds a real
  `TMDB_API_KEY`. It is gitignored (`.env.*`), was never tracked, and is not in git history.
  The key was printed once into an agent session's output on 2026-09-26; rotate it if
  that matters, and delete the file if it is no longer needed. It was left untouched.
