import { useState } from "react";

import { useT } from "../i18n";
import { imageUrl, initials } from "../lib/format";

interface PosterProps {
  title: string;
  path: string | null;
  size?: "w185" | "w342";
  /** Match percentage shown top-left; hidden below 60 (FR-5) or when null. */
  match?: number | null;
  /** Decorative when the title is printed next to it (the default), so it isn't read twice. */
  describe?: boolean;
  eager?: boolean;
}

/** 2:3 poster. Without an image (or when it fails): a gradient with the initials. */
export function Poster({ title, path, size = "w342", match, describe = false, eager }: PosterProps) {
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
      {match != null && match >= 60 && (
        <span className="badge" aria-label={t("common.matchLabel", { n: match })}>
          {t("common.matchBadge", { n: match })}
        </span>
      )}
    </div>
  );
}
