import { useState } from "react";

import { useT } from "../i18n";
import type { TraitKey } from "../lib/traits";
import { Dialog, DialogCancel, useDialogClose } from "./Dialog";
import { RatingInput } from "./RatingInput";

/** The one rating dialog: the film page's Rate button and the Home cards' quick Rate. */
export function RateDialog({
  title,
  current,
  onSave,
  onClose,
}: {
  title: string;
  current: number | null;
  onSave: (value: number, aspects: TraitKey[]) => void;
  onClose: () => void;
}) {
  const t = useT();
  const [value, setValue] = useState(current ?? 7);
  const [aspects, setAspects] = useState<TraitKey[]>([]);
  return (
    <Dialog title={t("movie.rateDialog", { title })} onClose={onClose}>
      <RatingInput value={value} onChange={setValue} aspects={aspects} onAspectsChange={setAspects} />
      <RateActions onSave={() => onSave(value, aspects)} />
    </Dialog>
  );
}

/** Cancel and Save leave the way Escape does: the sheet's exit first, then the action. */
function RateActions({ onSave }: { onSave: () => void }) {
  const t = useT();
  const close = useDialogClose();
  return (
    <div className="foot-actions" style={{ marginTop: 16 }}>
      <DialogCancel>{t("common.cancel")}</DialogCancel>
      <button type="button" className="btn btn-primary" onClick={() => close(onSave)}>
        {t("movie.rateSave")}
      </button>
    </div>
  );
}
