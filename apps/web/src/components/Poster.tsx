import { useState } from "react";

import { useT } from "../i18n";
import { imageUrl, initials } from "../lib/format";
import type { MatchBand as Band } from "../lib/types";
import { MatchBand } from "./MatchBand";

interface PosterProps {
  title: string;
  path: string | null;
  size?: "w185" | "w342";
  /** The match band; only "strong" is shown on a poster (top-left, red), so it stays rare. */
  band?: Band | null;
  /** Decorative when the title is printed next to it (the default), so it isn't read twice. */
  describe?: boolean;
  eager?: boolean;
}

/** 2:3 poster. Without an image (or when it fails): a gradient with the initials. */
export function Poster({ title, path, size = "w342", band, describe = false, eager }: PosterProps) {
  const t = useT();
  const [failed, setFailed] = useState(false);
  const src = failed ? null : imageUrl(path, size);
  return (
    <div className="poster">
      {src ? (
        <img
          src={src}
          alt={describe ? t("common.poster", { title }) : ""}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="poster-fallback" aria-hidden="true">
          {initials(title)}
        </span>
      )}
      {band === "strong" && <MatchBand band={band} className="badge" />}
    </div>
  );
}
