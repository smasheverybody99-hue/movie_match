import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Dialog, DIALOG_CLOSE_MS, DialogCancel } from "./Dialog";

function motion(reduce: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({ matches: reduce, addEventListener: vi.fn(), removeEventListener: vi.fn() })),
  );
}

function open(onClose: () => void) {
  return render(
    <Dialog title="Rate it" onClose={onClose}>
      <DialogCancel>Cancel</DialogCancel>
    </Dialog>,
  );
}

describe("Dialog", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("leaves in 120 ms before it closes: Escape, the backdrop and Cancel alike", () => {
    vi.useFakeTimers();
    motion(false);
    for (const leave of [
      () => fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" }),
      () => fireEvent.mouseDown(document.querySelector(".dialog-backdrop")!),
      () => fireEvent.click(screen.getByRole("button", { name: "Cancel" })),
    ]) {
      const onClose = vi.fn();
      const { unmount } = open(onClose);
      leave();
      expect(document.querySelector(".dialog-backdrop")).toHaveClass("is-closing");
      act(() => vi.advanceTimersByTime(DIALOG_CLOSE_MS - 1));
      expect(onClose).not.toHaveBeenCalled();
      act(() => vi.advanceTimersByTime(1));
      expect(onClose).toHaveBeenCalledTimes(1);
      unmount();
    }
    expect(DIALOG_CLOSE_MS).toBe(120);
  });

  it("closes once, however often it is asked while leaving", () => {
    vi.useFakeTimers();
    motion(false);
    const onClose = vi.fn();
    open(onClose);
    const dialog = screen.getByRole("dialog");
    fireEvent.keyDown(dialog, { key: "Escape" });
    fireEvent.keyDown(dialog, { key: "Escape" });
    act(() => vi.advanceTimersByTime(DIALOG_CLOSE_MS));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("is drawn straight into document.body, outside whatever opened it", () => {
    const { container } = render(
      <div className="film-head" style={{ position: "relative", zIndex: 1 }}>
        <Dialog title="Rate it" onClose={() => {}}>
          <button type="button">Save</button>
        </Dialog>
      </div>,
    );
    const backdrop = document.querySelector(".dialog-backdrop")!;
    expect(backdrop.parentElement).toBe(document.body);
    expect(container.querySelector(".dialog-backdrop")).toBeNull();
    expect(container.querySelector(".film-head")).not.toContainElement(screen.getByRole("dialog"));
  });

  it("keeps its keyboard handling through the portal: focus inside, Tab wraps, focus goes back", () => {
    function Page({ open: isOpen, onClose }: { open: boolean; onClose: () => void }) {
      return (
        <div>
          <button type="button">Rate</button>
          {isOpen && (
            <Dialog title="Rate it" onClose={onClose}>
              <button type="button">First</button>
              <button type="button">Last</button>
            </Dialog>
          )}
        </div>
      );
    }
    const onClose = vi.fn();
    const { rerender } = render(<Page open={false} onClose={onClose} />);
    const opener = screen.getByRole("button", { name: "Rate" });
    opener.focus();
    rerender(<Page open onClose={onClose} />);

    const first = screen.getByRole("button", { name: "First" });
    const last = screen.getByRole("button", { name: "Last" });
    expect(first).toHaveFocus();
    last.focus();
    fireEvent.keyDown(last, { key: "Tab" });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "Tab", shiftKey: true });
    expect(last).toHaveFocus();

    fireEvent.keyDown(last, { key: "Escape" }); // no matchMedia in tests: reduced motion, at once
    expect(onClose).toHaveBeenCalledTimes(1);
    rerender(<Page open={false} onClose={onClose} />);
    expect(opener).toHaveFocus();
  });

  it("with reduced motion closes at once", () => {
    motion(true);
    const onClose = vi.fn();
    open(onClose);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
