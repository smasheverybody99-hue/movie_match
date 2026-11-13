import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { movie } from "../dev/fixtures";
import type * as ApiModule from "../lib/api";
import { api, ApiError, AssistantLimitError, readSse } from "../lib/api";
import { applyEvent, newExchange } from "../lib/assistant";
import type { AssistantChatIn, AssistantEvent } from "../lib/types";
import { renderWithProviders } from "../test/utils";
import Assistant, { resetTime } from "./Assistant";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof ApiModule>("../lib/api");
  const { mockedApi } = await import("../test/utils");
  return { ...actual, api: mockedApi(actual.api) };
});

const chat = vi.mocked(api.assistantChat);
const ROUTE = { route: "/assistant", path: "/assistant" };

/**
 * A stream the test plays by hand: `send` delivers events one at a time, `end` finishes
 * the request, `fail` breaks it.
 */
function controlledStream() {
  let emit: (event: AssistantEvent) => void = () => {};
  let finish: () => void = () => {};
  let breakOff: (error: unknown) => void = () => {};
  const bodies: AssistantChatIn[] = [];
  chat.mockImplementation((body, onEvent) => {
    bodies.push(body);
    emit = onEvent;
    return new Promise<void>((resolve, reject) => {
      finish = resolve;
      breakOff = reject;
    });
  });
  return {
    bodies,
    send: (...events: AssistantEvent[]) => act(() => events.forEach((e) => emit(e))),
    end: () => act(async () => finish()),
    fail: (error: unknown) => act(async () => breakOff(error)),
  };
}

const card = (i: number) => ({ movie: movie(i), match: 80, band: null });

describe("Assistant", () => {
  beforeEach(() => {
    chat.mockReset();
  });

  it("opens the connection while the viewer types, at most once in 30 s", async () => {
    // FR-8's 2 s start when the message is sent; a new connection to the API cost ~1 s.
    const health = vi.mocked(api.health);
    health.mockReset();
    health.mockResolvedValue({ status: "ok", trait_dimensions: 14, commit: null });
    const now = vi.spyOn(Date, "now").mockReturnValue(1_000_000);
    renderWithProviders(<Assistant />, ROUTE);
    expect(health).not.toHaveBeenCalled();

    const input = screen.getByLabelText("Your question");
    await userEvent.click(input);
    await userEvent.type(input, "Something");
    expect(health).toHaveBeenCalledTimes(1);

    now.mockReturnValue(1_000_000 + 30_000);
    await userEvent.type(input, "!");
    expect(health).toHaveBeenCalledTimes(2);
    now.mockRestore();
  });

  it("renders three starter prompts on an empty conversation, and asking one sends it", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    const starters = within(screen.getByRole("region", { name: "Try asking" })).getAllByRole("button");
    expect(starters.map((b) => b.textContent)).toEqual([
      "I have 90 minutes — blow my mind",
      "Something light for a tired evening",
      "A dark thriller from the 90s",
    ]);

    await userEvent.click(starters[0] as HTMLElement);
    expect(stream.bodies).toEqual([
      { message: "I have 90 minutes — blow my mind", lang: "en", new_conversation: true },
    ]);
    expect(screen.queryByRole("region", { name: "Try asking" })).toBeNull();
  });

  it("shows a loading state until the first words arrive", async () => {
    controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Something funny{Enter}");
    expect(screen.getByRole("status")).toHaveTextContent("Looking through your films…");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  it("renders streaming text incrementally, then cards inside the answer and follow-up chips", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Blow my mind{Enter}");
    const answer = screen.getByRole("article", { name: "Assistant" });

    stream.send({ type: "text", text: "Two short ones " });
    expect(answer).toHaveTextContent("Two short ones");
    expect(answer).not.toHaveTextContent("keep you guessing");
    expect(screen.queryByText("Looking through your films…")).toBeNull();

    stream.send({ type: "text", text: "that keep you guessing." });
    expect(answer).toHaveTextContent("Two short ones that keep you guessing.");
    expect(answer).toHaveAttribute("aria-busy", "true");

    stream.send({ type: "card", card: card(1) }, { type: "card", card: card(2) });
    const links = within(answer).getAllByRole("link");
    expect(links.map((a) => a.getAttribute("href"))).toEqual([`/movie/${movie(1).id}`, `/movie/${movie(2).id}`]);

    stream.send({ type: "followups", items: ["Something shorter", "Older films"] }, { type: "done" });
    await stream.end();
    expect(answer).toHaveAttribute("aria-busy", "false");
    const chips = within(screen.getByRole("region", { name: "Ask next" })).getAllByRole("button");
    expect(chips.map((c) => c.textContent)).toEqual(["Something shorter", "Older films"]);

    await userEvent.click(chips[0] as HTMLElement);
    expect(stream.bodies[1]).toEqual({ message: "Something shorter", lang: "en", new_conversation: false });
  });

  it("shows the reset time when today's limit is reached, not an error", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "One more{Enter}");
    const resetsAt = new Date(Date.now() + 3 * 3600_000).toISOString();
    await stream.fail(
      new AssistantLimitError({ detail: "Daily assistant limit reached", limit: 30, resets_at: resetsAt }),
    );

    const time = resetTime(resetsAt, "en");
    expect(screen.getByRole("status")).toHaveTextContent(
      `You've asked all 30 of today's questions. You can ask again at ${time}.`,
    );
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("textbox", { name: "Your question" })).toBeDisabled();
  });

  it("shows an error with a retry when the answer fails", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Something calm{Enter}");
    await stream.fail(new ApiError(0, "offline"));

    expect(screen.getByRole("alert")).toHaveTextContent("The assistant couldn't answer. Try again.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(stream.bodies.map((b) => b.message)).toEqual(["Something calm", "Something calm"]);
  });

  it("says the assistant is busy, with a retry, when the answer did not come in time", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Something calm{Enter}");
    stream.send({ type: "error", reason: "timeout" });
    await stream.end();

    expect(screen.getByRole("alert")).toHaveTextContent("The assistant is busy right now. Try again in a minute.");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(stream.bodies.map((b) => b.message)).toEqual(["Something calm", "Something calm"]);
  });

  it("drops a broken-off start when the server tries again, and shows the new answer", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Blow my mind{Enter}");
    const answer = screen.getByRole("article", { name: "Assistant" });
    stream.send({ type: "text", text: "Two short ones. " }, { type: "card", card: card(1) }, { type: "text", text: "This" });
    expect(answer).toHaveTextContent("This");

    stream.send({ type: "reset" });
    expect(answer).not.toHaveTextContent("Two short ones");
    expect(within(answer).queryAllByRole("link")).toHaveLength(0);
    expect(screen.getByRole("status")).toHaveTextContent("Looking through your films…");

    stream.send({ type: "text", text: "Two short ones. " }, { type: "card", card: card(1) }, { type: "done" });
    await stream.end();
    expect(within(answer).getAllByRole("link")).toHaveLength(1);
    expect(answer.textContent?.match(/Two short ones/g)).toHaveLength(1);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("replaces an off-topic answer with its own fixed refusal", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Capital of Peru?{Enter}");
    stream.send({ type: "text", text: "Lima" }, { type: "refusal", reason: "off_topic" }, { type: "done" });
    await stream.end();

    const answer = screen.getByRole("article", { name: "Assistant" });
    expect(answer).toHaveTextContent("I can only help with films.");
    expect(answer).not.toHaveTextContent("Lima");
  });

  it("starts a new conversation on request", async () => {
    const stream = controlledStream();
    renderWithProviders(<Assistant />, ROUTE);
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "First{Enter}");
    stream.send({ type: "text", text: "Ok." }, { type: "done" });
    await stream.end();

    await userEvent.click(screen.getByRole("button", { name: "New conversation" }));
    expect(screen.getByRole("region", { name: "Try asking" })).toBeInTheDocument();
    await userEvent.type(screen.getByRole("textbox", { name: "Your question" }), "Second{Enter}");
    expect(stream.bodies[1]?.new_conversation).toBe(true);
  });
});

describe("the assistant stream", () => {
  it("reads complete SSE blocks and keeps a block that is still arriving", () => {
    const { events, rest } = readSse(
      'event: text\ndata: {"text": "Hi"}\n\nevent: card\ndata: {"movie": {"id": 1}, "match": 80, "band": null}\n\nevent: do',
    );
    expect(events.map((e) => e.type)).toEqual(["text", "card"]);
    expect(rest).toBe("event: do");
    expect(readSse('event: future\ndata: {}\n\nevent: done\ndata: {}\n\n').events).toEqual([{ type: "done" }]);
    expect(readSse("event: reset\ndata: {}\n\n").events).toEqual([{ type: "reset" }]);
    expect(readSse('event: error\ndata: {"reason": "timeout"}\n\n').events).toEqual([
      { type: "error", reason: "timeout" },
    ]);
    expect(readSse('event: error\ndata: {"reason": "new"}\n\n').events).toEqual([{ type: "error", reason: "failed" }]);
  });

  it("joins text into one run and cards into one row until the other interrupts", () => {
    let exchange = newExchange(1, "q");
    const events: AssistantEvent[] = [
      { type: "text", text: "A " },
      { type: "text", text: "B" },
      { type: "card", card: card(1) },
      { type: "card", card: card(2) },
      { type: "text", text: "C" },
      { type: "card", card: card(3) },
      { type: "done" },
    ];
    for (const event of events) exchange = applyEvent(exchange, event);
    expect(exchange.parts.map((p) => (p.kind === "text" ? p.text : p.cards.length))).toEqual(["A B", 2, "C", 1]);
    expect(exchange.status).toBe("done");
  });
});
