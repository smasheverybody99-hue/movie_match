import { TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { Icon } from "./Icon";

/**
 * An error under a field or an action: a warning icon (gold, the colour for warnings)
 * and the text. `alert` makes screen readers announce it when it appears; a message tied
 * to an input through aria-describedby passes `alert={false}` and an `id`.
 */
export function FieldError({
  children,
  id,
  alert = true,
}: {
  children: ReactNode;
  id?: string;
  alert?: boolean;
}) {
  return (
    <p className="field-error" id={id} role={alert ? "alert" : undefined}>
      <Icon as={TriangleAlert} size={14} />
      <span>{children}</span>
    </p>
  );
}
