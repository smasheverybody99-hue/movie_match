/**
 * The assistant conversation (FR-8). The stream goes through a TanStack Query mutation
 * (CLAUDE.md: no fetch in components); the conversation itself is screen state, because
 * nothing about it is cached or refetched: the API keeps the last five turns as the
 * model's context, and a page that opens fresh starts a new conversation there too.
 */
import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { useI18n } from "../i18n";
import { AssistantLimitError, api } from "./api";
import type {
  AssistantCard,
  AssistantErrorReason,
  AssistantEvent,
  AssistantRefusalReason,
} from "./types";

/** What an answer shows, in the order the stream sent it: text runs and rows of cards. */
export type AnswerPart = { kind: "text"; text: string } | { kind: "cards"; cards: AssistantCard[] };

export type ExchangeStatus = "waiting" | "streaming" | "done" | "refused" | "failed" | "limit";

export interface Exchange {
  id: number;
  question: string;
  parts: AnswerPart[];
  followups: string[];
  status: ExchangeStatus;
  refusal: AssistantRefusalReason | null;
  error: AssistantErrorReason | "offline" | null;
  /** The limit reached, and when it resets (ISO), on a "limit" exchange. */
  limit: { count: number; resetsAt: string } | null;
}

export function newExchange(id: number, question: string): Exchange {
  return { id, question, parts: [], followups: [], status: "waiting", refusal: null, error: null, limit: null };
}

/** One event applied to the answer it belongs to. Pure: the hook and the tests share it. */
export function applyEvent(exchange: Exchange, event: AssistantEvent): Exchange {
  switch (event.type) {
    case "text": {
      const last = exchange.parts.at(-1);
      const parts: AnswerPart[] =
        last?.kind === "text"
          ? [...exchange.parts.slice(0, -1), { kind: "text", text: last.text + event.text }]
          : [...exchange.parts, { kind: "text", text: event.text }];
      return { ...exchange, parts, status: "streaming" };
    }
    case "card": {
      const last = exchange.parts.at(-1);
      // Cards that follow each other share a row; text in between starts a new one.
      const parts: AnswerPart[] =
        last?.kind === "cards"
          ? [...exchange.parts.slice(0, -1), { kind: "cards", cards: [...last.cards, event.card] }]
          : [...exchange.parts, { kind: "cards", cards: [event.card] }];
      return { ...exchange, parts, status: "streaming" };
    }
    case "followups":
      return { ...exchange, followups: event.items.slice(0, 3) };
    case "refusal":
      // The interface's own fixed text replaces whatever came before the refusal.
      return { ...exchange, parts: [], followups: [], status: "refused", refusal: event.reason };
    case "error":
      return { ...exchange, status: "failed", error: event.reason };
    case "reset":
      // The server tries the call again; what came before that call is sent again.
      return { ...exchange, parts: [], followups: [], status: "waiting" };
    case "done":
      return exchange.status === "refused" ? exchange : { ...exchange, status: "done" };
  }
}

interface Ask {
  id: number;
  message: string;
  newConversation: boolean;
}

/**
 * How often the screen may open the connection to the API ahead of a message. A new
 * connection to the API cost ~1.0 s more than a reused one (2026-11-13, /health from the
 * dev machine: 1.43 s vs 0.42 s, medians of 5), and FR-8 gives the first words 2 s from
 * the moment the message is sent. A page loaded a while ago may hold no open connection.
 */
export const WARM_EVERY_MS = 30_000;

export function useAssistantChat() {
  const { lang } = useI18n();
  const warmedAt = useRef(-Infinity);
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const nextId = useRef(1);
  // The first message from this screen starts a new conversation on the API as well.
  const fresh = useRef(true);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => () => abort.current?.abort(), []);

  const update = useCallback((id: number, change: (exchange: Exchange) => Exchange) => {
    setExchanges((list) => list.map((e) => (e.id === id ? change(e) : e)));
  }, []);

  const mutation = useMutation({
    mutationFn: async ({ id, message, newConversation }: Ask) => {
      const controller = new AbortController();
      abort.current = controller;
      await api.assistantChat(
        { message, lang, new_conversation: newConversation },
        (event) => update(id, (e) => applyEvent(e, event)),
        controller.signal,
      );
    },
    onSuccess: (_data, { id }) =>
      // A stream that ended without `done` or `error` broke off: say so.
      update(id, (e) => (e.status === "waiting" || e.status === "streaming" ? { ...e, status: "failed", error: "failed" } : e)),
    onError: (error, { id }) => {
      if (error instanceof AssistantLimitError) {
        update(id, (e) => ({
          ...e,
          status: "limit",
          limit: { count: error.limit.limit, resetsAt: error.limit.resets_at },
        }));
      } else {
        update(id, (e) => ({ ...e, status: "failed", error: "failed" }));
      }
    },
  });

  const ask = useCallback(
    (text: string) => {
      const message = text.trim();
      if (!message || mutation.isPending) return;
      const id = nextId.current++;
      setExchanges((list) => [...list, newExchange(id, message)]);
      mutation.mutate({ id, message, newConversation: fresh.current });
      fresh.current = false;
    },
    [mutation],
  );

  const restart = useCallback(() => {
    abort.current?.abort();
    setExchanges([]);
    fresh.current = true;
  }, []);

  const last = exchanges.at(-1);
  const limit = [...exchanges].reverse().find((e) => e.status === "limit")?.limit ?? null;
  /** While the viewer types: a cheap request, so the message finds the connection open. */
  const warm = useCallback(() => {
    const now = Date.now();
    if (now - warmedAt.current < WARM_EVERY_MS) return;
    warmedAt.current = now;
    void Promise.resolve()
      .then(() => api.health())
      .catch(() => undefined); // only the open connection matters, not the answer
  }, []);

  return {
    exchanges,
    ask,
    restart,
    warm,
    busy: mutation.isPending,
    /** Set once today's cap is hit: the screen stops offering to send. */
    limit: limit && new Date(limit.resetsAt).getTime() > Date.now() ? limit : null,
    retryable: last?.status === "failed" ? last.question : null,
  };
}
