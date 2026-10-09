import { useEffect, useId } from "react";

import { useI18n } from "../i18n";
import { score as formatScore } from "../lib/format";
import { TRAIT_KEYS, type TraitKey } from "../lib/traits";
import { traitLabelKey } from "./Traits";

/** FR-3: "what did you like?" appears for scores above 8.0. */
export const LIKED_ASPECTS_ABOVE = 8.0;

export function showsLikedAspects(value: number): boolean {
  return value > LIKED_ASPECTS_ABOVE;
}

function isTextField(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable || target.tagName === "TEXTAREA") return true;
  return target instanceof HTMLInputElement && !["range", "checkbox", "radio", "button"].includes(target.type);
}

/**
 * The 0.5-step, 10-point scale (design system, onboarding 2/3). Keyboard: the slider's
 * own arrows, plus 1-9 anywhere outside a text field for a whole score, 0 for 10.
 */
export function RatingInput({
  value,
  onChange,
  aspects,
  onAspectsChange,
}: {
  value: number;
  onChange: (value: number) => void;
  aspects: TraitKey[];
  onAspectsChange: (aspects: TraitKey[]) => void;
}) {
  const { t, lang } = useI18n();
  const id = useId();

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.altKey || event.ctrlKey || event.metaKey || isTextField(event.target)) return;
      if (!/^[0-9]$/.test(event.key)) return;
      event.preventDefault();
      onChange(event.key === "0" ? 10 : Number(event.key));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onChange]);

  function toggle(key: TraitKey) {
    onAspectsChange(aspects.includes(key) ? aspects.filter((a) => a !== key) : [...aspects, key]);
  }

  return (
    <div>
      <div className="score-big" aria-hidden="true">
        {formatScore(value, lang)}
      </div>
      <div className="meta" aria-hidden="true">
        {t("onboarding.rate.outOf")}
      </div>
      <label htmlFor={id} className="visually-hidden">
        {t("onboarding.rate.scoreLabel")}
      </label>
      <input
        id={id}
        className="slider"
        type="range"
        min={0.5}
        max={10}
        step={0.5}
        value={value}
        aria-valuetext={formatScore(value, lang)}
        aria-describedby={`${id}-hint`}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <div className="scale-marks" aria-hidden="true">
        <span>0.5</span>
        <span>5.0</span>
        <span>10</span>
      </div>
      <p id={`${id}-hint`} className="meta">
        {t("onboarding.rate.keysHint")}
      </p>

      {showsLikedAspects(value) && (
        <fieldset className="aspects">
          <legend className="field-label">{t("onboarding.rate.liked")}</legend>
          <div className="chip-row" data-testid="liked-aspects">
            {TRAIT_KEYS.map((key) => (
              <button
                key={key}
                type="button"
                className="chip"
                aria-pressed={aspects.includes(key)}
                onClick={() => toggle(key)}
              >
                {t(traitLabelKey(key))}
              </button>
            ))}
          </div>
        </fieldset>
      )}
    </div>
  );
}
