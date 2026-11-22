import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type * as ApiModule from "../lib/api";
import { api, ApiError } from "../lib/api";
import type { Me } from "../lib/types";
import { fakeAuthClient, pending, renderWithProviders, TEST_SESSION } from "../test/utils";
import { AssistantDataReminder, DataNoticeGate } from "./DataNotice";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const me = vi.mocked(api.me);
const accept = vi.mocked(api.acceptDataNotice);

const ME: Me = {
  id: TEST_SESSION.userId,
  created_at: "2026-11-23T10:00:00Z",
  rating_count: 0,
  ratings_needed: 10,
  has_taste_profile: false,
  taste_updated_at: null,
  data_notice_required: true,
  data_notice_accepted_at: null,
};

function gate(auth = fakeAuthClient()) {
  return renderWithProviders(
    <DataNoticeGate loading={<p data-testid="loading">loading</p>}>
      <p>the app</p>
    </DataNoticeGate>,
    { auth },
  );
}

describe("the data notice", () => {
  beforeEach(() => {
    me.mockReset();
    accept.mockReset();
    localStorage.clear();
  });

  it("waits for the account before anything could send data", async () => {
    me.mockReturnValue(pending());
    gate();
    expect(await screen.findByTestId("loading")).toBeInTheDocument();
    expect(screen.queryByText("the app")).not.toBeInTheDocument();
  });

  it("comes before the app until it is accepted, and says what is sent where", async () => {
    me.mockResolvedValue(ME);
    gate();
    expect(await screen.findByRole("heading", { name: "Before you start" })).toBeInTheDocument();
    expect(screen.getByText(/run on Google Gemini's free tier/)).toBeInTheDocument();
    expect(screen.getByText(/Don't write anything personal or confidential/)).toBeInTheDocument();
    expect(screen.queryByText("the app")).not.toBeInTheDocument();
  });

  it("lets the viewer in once accepted, and remembers it in this browser", async () => {
    me.mockResolvedValueOnce(ME).mockResolvedValue({ ...ME, data_notice_accepted_at: "2026-11-23T10:01:00Z" });
    accept.mockResolvedValue(undefined);
    gate();
    await userEvent.click(await screen.findByRole("button", { name: "I agree, continue" }));
    expect(accept).toHaveBeenCalledTimes(1);
    expect(await screen.findByText("the app")).toBeInTheDocument();
    expect(localStorage.getItem(`mm.dataNotice.v1.${TEST_SESSION.userId}`)).toBe("accepted");
  });

  it("signs the viewer out when they do not agree", async () => {
    me.mockResolvedValue(ME);
    const auth = fakeAuthClient();
    gate(auth);
    await userEvent.click(await screen.findByRole("button", { name: "I don't agree — sign out" }));
    expect(auth.signOut).toHaveBeenCalledTimes(1);
    expect(accept).not.toHaveBeenCalled();
  });

  it("says so when the answer is not saved, and stays", async () => {
    me.mockResolvedValue(ME);
    accept.mockRejectedValue(new ApiError(0, "offline"));
    gate();
    await userEvent.click(await screen.findByRole("button", { name: "I agree, continue" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't save your answer");
    expect(screen.queryByText("the app")).not.toBeInTheDocument();
  });

  it("is not shown once accepted, nor where it is not needed", async () => {
    me.mockResolvedValue({ ...ME, data_notice_accepted_at: "2026-11-23T10:01:00Z" });
    const first = gate();
    expect(await screen.findByText("the app")).toBeInTheDocument();
    first.unmount();
    me.mockResolvedValue({ ...ME, data_notice_required: false });
    gate();
    expect(await screen.findByText("the app")).toBeInTheDocument();
  });

  it("goes straight in, while the account loads, for a viewer this browser saw accept", async () => {
    localStorage.setItem(`mm.dataNotice.v1.${TEST_SESSION.userId}`, "accepted");
    me.mockReturnValue(pending());
    gate();
    expect(await screen.findByText("the app")).toBeInTheDocument();
  });

  it("asks to try again when the account cannot be loaded", async () => {
    me.mockRejectedValue(new ApiError(0, "offline"));
    gate();
    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't load your account");
    me.mockResolvedValue({ ...ME, data_notice_required: false });
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.getByText("the app")).toBeInTheDocument());
  });

  it("leaves a one-line reminder on the assistant while it applies", async () => {
    me.mockResolvedValue({ ...ME, data_notice_accepted_at: "2026-11-23T10:01:00Z" });
    renderWithProviders(<AssistantDataReminder />);
    expect(await screen.findByText(/Test mode: your messages go to Google's free tier/)).toBeInTheDocument();
  });
});
