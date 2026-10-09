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
  render(
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
      open(onClose);
      leave();
      expect(document.querySelector(".dialog-backdrop")).toHaveClass("is-closing");
      act(() => vi.advanceTimersByTime(DIALOG_CLOSE_MS - 1));
      expect(onClose).not.toHaveBeenCalled();
      act(() => vi.advanceTimersByTime(1));
      expect(onClose).toHaveBeenCalledTimes(1);
      document.body.innerHTML = "";
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

  it("with reduced motion closes at once", () => {
    motion(true);
    const onClose = vi.fn();
    open(onClose);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
