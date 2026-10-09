import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { usePrefersReducedMotion } from "../lib/motion";

/** How long the sheet takes to leave (docs/ui.md 7): ease-in, shorter than the 160 ms in. */
export const DIALOG_CLOSE_MS = 120;

/**
 * Close the dialog it is called in, then run `then` once the sheet has left: so a button
 * inside (Cancel, Save) gets the same exit as Escape and the backdrop.
 */
const CloseContext = createContext<(then?: () => void) => void>((then) => then?.());
export const useDialogClose = () => useContext(CloseContext);

/** The dialog's Cancel: leaves like Escape. */
export function DialogCancel({ children }: { children: ReactNode }) {
  const close = useDialogClose();
  return (
    <button type="button" className="btn btn-ghost" onClick={() => close()}>
      {children}
    </button>
  );
}

/**
 * A modal sheet (bottom sheet on phones, centred on wider screens). Escape and the
 * backdrop close it; Tab stays inside; focus returns to whatever opened it.
 * In: the backdrop fades and the sheet grows from 96% (160 ms, ease-out). Out: the reverse
 * in 120 ms, ease-in, and only then `onClose`. With reduced motion it closes at once.
 * Drawn into document.body (a portal): wherever it is opened from, no ancestor's stacking
 * context or containment can hold it under the top bar, the bottom nav or the search row
 * (the film page's head is `z-index: 1`; `.main` is a size container). React events and
 * context still follow the component tree, so the keyboard handling below is unchanged.
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
  const reduce = usePrefersReducedMotion();
  const [closing, setClosing] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const close = useCallback(
    (then: () => void = onClose) => {
      if (timer.current) return; // already leaving
      if (reduce) {
        then();
        return;
      }
      setClosing(true);
      timer.current = setTimeout(then, DIALOG_CLOSE_MS);
    },
    [onClose, reduce],
  );
  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

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
      close();
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

  return createPortal(
    <div
      className={closing ? "dialog-backdrop is-closing" : "dialog-backdrop"}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
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
        <CloseContext.Provider value={close}>{children}</CloseContext.Provider>
      </div>
    </div>,
    document.body,
  );
}
