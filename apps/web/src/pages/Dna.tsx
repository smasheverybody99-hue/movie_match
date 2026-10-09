import { Share2 } from "lucide-react";
import { useState } from "react";

import { DnaFlower } from "../components/DnaFlower";
import { Icon } from "../components/Icon";
import { EmptyState, QueryView, Skeleton } from "../components/States";
import { TraitBar, traitInSentence, traitLabelKey } from "../components/Traits";
import { useI18n, useT, type Translate } from "../i18n";
import { score } from "../lib/format";
import { genreLabel } from "../lib/genres";
import { useDna } from "../lib/queries";
import { isTraitKey, type TraitKey } from "../lib/traits";
import type { Lang, MovieDna } from "../lib/types";

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
export function summarize(dna: MovieDna, t: Translate, lang: Lang): string {
  if (dna.summary) return dna.summary;
  const [a, b, c] = sortedTraits(dna.scores).map(([key]) => traitInSentence(key, t, lang));
  return t("dna.summary", { a: a ?? "", b: b ?? "", c: c ?? "" });
}

/** The page's shape while it loads: the sentence, the chart's square, the stats row. */
function DnaSkeleton() {
  return (
    <div className="dna-page">
      <Skeleton className="skeleton-line dna-summary" style={{ height: 22 }} />
      <Skeleton className="dna-flower" style={{ borderRadius: "50%" }} />
      <Skeleton className="dna-stats dna-stats-skel" />
    </div>
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
  const { t, lang } = useI18n();
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
        const summary = summarize(dna, t, lang);
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
            {/* Below 1100px one column: the sentence, the chart (at most 480px), the stats in
                one row, Numbers. From 1100 two: the chart (~560px) on the left, centred
                vertically; the sentence, the stats as a list and Numbers on the right. */}
            <div className="dna-page">
              <p className="dna-summary">“{summary}”</p>
              <DnaFlower
                scores={dna.scores}
                label={t("dna.chartLabel", {
                  traits: traits
                    .slice(0, 3)
                    .map(([key, value]) => `${t(traitLabelKey(key))} ${Math.round(value)}`)
                    .join(", "),
                })}
              />
              <section className="dna-stats" aria-labelledby="stats-title">
                <h2 className="visually-hidden" id="stats-title">
                  {t("dna.stats")}
                </h2>
                <dl className="stats">
                  <div>
                    <dt>{t("dna.statFilms")}</dt>
                    <dd>{dna.rating_count}</dd>
                  </div>
                  <div>
                    <dt>{t("dna.statAverage")}</dt>
                    <dd>{dna.average_rating !== null ? score(dna.average_rating, lang) : "—"}</dd>
                  </div>
                  <div>
                    <dt>{t("dna.statGenre")}</dt>
                    <dd>{dna.top_genre ? genreLabel(dna.top_genre, t) : "—"}</dd>
                  </div>
                </dl>
              </section>
              {/* A plain disclosure, not a modal: the chart's text alternative too. */}
              <details className="dna-numbers">
                <summary className="btn btn-ghost">{t("dna.numbers")}</summary>
                <div data-testid="dna-bars">
                  {traits.map(([key, value]) => (
                    <TraitBar key={key} trait={key} value={value} />
                  ))}
                </div>
              </details>
            </div>
          </>
        );
      }}
    </QueryView>
  );
}
