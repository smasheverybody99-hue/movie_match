# Legal notes

Not legal advice. These are the open items a lawyer needs to review before public launch.

## 1. TMDB — free tier now, commercial licence before monetization

See ADR 0002 for the reasoning. In short:

TMDB's API is free for **non-commercial** use. A commercial product needs a separate
licence, arranged through `sales@themoviedb.org`.

**We build on the free tier.** Development, the closed alpha and a free public launch
earn no revenue, so the non-commercial terms cover them. The licence becomes required
**before the product charges for anything** — subscriptions, ads, paid tiers. That makes
it a phase-9 launch-gate item, not a phase-0 blocker.

Treat this as a hard line, not a grey area: the day a revenue mechanism ships is the day
the licence must already be signed. Start the conversation weeks ahead of that day, since
replies can take time.

### Attribution — required on the free tier too

From the moment the app is public:

- Display the TMDB logo (unmodified in colour, aspect ratio and orientation).
- Display: *"This product uses the TMDB API but is not endorsed or certified by TMDB."*
- Place it in the app's About or Credits screen.

### Sources that cannot be used

- **MovieLens** — the licence forbids commercial or revenue-bearing use.
- **IMDb datasets** — personal and non-commercial use only.

Do not import either, even during development: data imported under a non-commercial
licence does not become usable later by changing the product's business model.

### Keep the source swappable

`app/pipelines/tmdb.py` is the only module that knows TMDB's field names. Everything
downstream works with our own model shapes. If TMDB licensing later proves unworkable,
the fallback is **Wikidata** (CC0, commercial use unrestricted) for metadata — but note
that no open source provides posters or streaming availability, so that path requires a
UI that does not depend on poster recognition.

## 2. Character Match — third-party IP

Batman, Tony Stark, Spider-Man and similar characters are protected by copyright and
trademark. The feature must:

- Use **text names only**. No images, artwork, logos, silhouettes or stylised icons.
- Carry a visible disclaimer: entertainment only, unofficial, not a psychological test.
- Lean on public-domain characters (Sherlock Holmes and similar) in the first version.
- Be reviewed by a lawyer before it ships publicly.

Do not generate or commission character illustrations. Do not put character names in the
app's store listing, icon or marketing imagery.

## 3. User data

- Privacy policy and terms before launch.
- Account deletion and data export must actually work, not just be promised.
- Ratings and watch history are personal data. Any "Taste Twin" style feature operates on
  anonymised, aggregated behaviour and never exposes another user's identity or list.
