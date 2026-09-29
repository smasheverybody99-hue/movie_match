import { useEffect, useId, useRef, type KeyboardEvent, type ReactNode } from "react";

/**
 * A modal sheet (bottom sheet on phones, centred on wider screens). Escape and the
 * backdrop close it; Tab stays inside; focus returns to whatever opened it.
 */
export function Dialog({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const first = ref.current?.querySelector<HTMLElement>(
      "input, button, [href], select, [tabindex]:not([tabindex='-1'])",
    );
    first?.focus();
    return () => opener?.focus();
  }, []);

  function onKeyDown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== "Tab" || !ref.current) return;
    const focusable = [
      ...ref.current.querySelectorAll<HTMLElement>(
        "input, button:not(:disabled), [href], select, [tabindex]:not([tabindex='-1'])",
      ),
    ];
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (!first || !last) return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div
      className="dialog-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
        onKeyDown={onKeyDown}
      >
        <h2 id={id}>{title}</h2>
        {children}
      </div>
    </div>
  );
}
