import { Share2 } from "lucide-react";
import { useState } from "react";

import { Icon } from "../components/Icon";
import { EmptyState, QueryView, Skeleton } from "../components/States";
import { TraitBar, traitLabelKey } from "../components/Traits";
import { useT, type Translate } from "../i18n";
import { score } from "../lib/format";
import { useDna } from "../lib/queries";
import { isTraitKey, type TraitKey } from "../lib/traits";
import type { MovieDna } from "../lib/types";

/** The taste vector as [trait, score], strongest first; ties keep the vector order. */
export function sortedTraits(scores: Record<string, number>): [TraitKey, number][] {
  return Object.entries(scores)
    .filter((entry): entry is [TraitKey, number] => isTraitKey(entry[0]))
    .sort((a, b) => b[1] - a[1]);
}

/**
 * The one-sentence summary. FR-7 asks for an AI one; until that is generated and cached
 * server-side (backlog), the sentence names the three strongest dimensions — the same
 * numbers the bars show, so it can never say something the profile doesn't.
 */
export function summarize(dna: MovieDna, t: Translate): string {
  if (dna.summary) return dna.summary;
  const [a, b, c] = sortedTraits(dna.scores).map(([key]) => t(traitLabelKey(key)));
  return t("dna.summary", { a: a ?? "", b: b ?? "", c: c ?? "" });
}

function DnaSkeleton() {
  return (
    <>
      <Skeleton style={{ height: 80, marginBottom: 16 }} />
      {Array.from({ length: 8 }, (_, i) => (
        <Skeleton key={i} className="skeleton-line" style={{ height: 18 }} />
      ))}
    </>
  );
}

function Share({ text }: { text: string }) {
  const t = useT();
  const [note, setNote] = useState<"copied" | "failed" | null>(null);

  async function share() {
    try {
      if (typeof navigator.share === "function") {
        await navigator.share({ text });
        return;
      }
      await navigator.clipboard.writeText(text);
      setNote("copied");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return; // closed the sheet
      setNote("failed");
    }
  }

  return (
    <>
      <button type="button" className="btn btn-secondary btn-sm" onClick={() => void share()}>
        <Icon as={Share2} size={16} /> {t("dna.share")}
      </button>
      <span role="status" className="visually-hidden">
        {note === "copied" ? t("dna.copied") : ""}
      </span>
      {note && (
        <p className="toast" aria-hidden="true">
          {note === "copied" ? t("dna.copied") : t("dna.shareError")}
        </p>
      )}
    </>
  );
}

/** /dna — the taste profile (FR-7). Below 10 ratings: "rate N more", never empty bars. */
export default function Dna() {
  const t = useT();
  const query = useDna();

  return (
    <QueryView query={query} skeleton={<DnaSkeleton />} error={t("dna.error")}>
      {(dna) => {
        if (dna.ratings_needed > 0) {
          return (
            <>
              <h1 className="screen-title">{t("dna.title")}</h1>
              <EmptyState
                message={t("dna.rateMore", { n: dna.ratings_needed })}
                action={{ label: t("dna.rateMoreCta"), to: "/onboarding" }}
              />
            </>
          );
        }
        const traits = sortedTraits(dna.scores);
        if (traits.length === 0) {
          return (
            <>
              <h1 className="screen-title">{t("dna.title")}</h1>
              <EmptyState message={t("dna.noTaste")} action={{ label: t("dna.rateMoreCta"), to: "/search" }} />
            </>
          );
        }
        const summary = summarize(dna, t);
        const shareText = t("dna.shareText", {
          traits: traits
            .slice(0, 5)
            .map(([key, value]) => `${t(traitLabelKey(key))} ${Math.round(value)}`)
            .join(", "),
        });
        return (
          <>
            <div className="title-row">
              <h1 className="screen-title">{t("dna.title")}</h1>
              <Share text={`${summary} ${shareText}`} />
            </div>
            <div className="dna-layout">
              <div>
                <div className="panel panel-elev" style={{ marginBottom: 16 }}>
                  <p className="dna-summary">“{summary}”</p>
                </div>
                <div data-testid="dna-bars">
                  {traits.map(([key, value]) => (
                    <TraitBar key={key} trait={key} value={value} />
                  ))}
                </div>
              </div>
              <section aria-labelledby="stats-title">
                <h2 className="eyebrow" id="stats-title">
                  {t("dna.stats")}
                </h2>
                <dl className="stats">
                  <div>
                    <dt>{t("dna.statFilms")}</dt>
                    <dd>{dna.rating_count}</dd>
                  </div>
                  <div>
                    <dt>{t("dna.statAverage")}</dt>
                    <dd>{dna.average_rating !== null ? score(dna.average_rating) : "—"}</dd>
                  </div>
                  <div>
                    <dt>{t("dna.statGenre")}</dt>
                    <dd>{dna.top_genre ?? "—"}</dd>
                  </div>
                </dl>
              </section>
            </div>
          </>
        );
      }}
    </QueryView>
  );
}
