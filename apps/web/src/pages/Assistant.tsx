import { RotateCcw, Send } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { Icon } from "../components/Icon";
import { MovieCard } from "../components/MovieCard";
import { useI18n, useT, type MessageKey } from "../i18n";
import { useAssistantChat, type Exchange } from "../lib/assistant";

/**
 * /assistant (FR-8). Three starter prompts on an empty conversation; the answer streams
 * in as text and rows of film cards from the engine; two or three follow-up chips after
 * the last answer. Today's cap is a state of the screen with its reset time, not a dialog.
 *
 * The four states: empty (starters), loading (waiting for the first words), error (the
 * answer failed, with a retry), content (the conversation).
 */
export const STARTERS: MessageKey[] = [
  "assistant.starter.mind",
  "assistant.starter.light",
  "assistant.starter.dark",
];

const MAX_CHARS = 500; // app.schemas.AssistantChatIn

/** The reset time in the viewer's own clock and language, e.g. "05:00". */
export function resetTime(iso: string, lang: string): string {
  return new Intl.DateTimeFormat(lang, { hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
}

function Answer({ exchange, onRetry }: { exchange: Exchange; onRetry?: () => void }) {
  const t = useT();
  const { lang } = useI18n();
  const { status } = exchange;

  if (status === "waiting") {
    return (
      <p className="assistant-thinking" role="status">
        <span className="assistant-dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        {t("assistant.thinking")}
      </p>
    );
  }
  if (status === "refused") {
    return <p>{t(exchange.refusal === "leak" ? "assistant.leak" : "assistant.offTopic")}</p>;
  }
  if (status === "limit" && exchange.limit) {
    return (
      <p className="assistant-limit" role="status">
        {t("assistant.limit", { n: exchange.limit.count, time: resetTime(exchange.limit.resetsAt, lang) })}
      </p>
    );
  }

  return (
    <>
      {exchange.parts.map((part, i) =>
        part.kind === "text" ? (
          <p key={i} className="assistant-text">
            {part.text.trim()}
          </p>
        ) : (
          <ul key={i} className="row-scroll assistant-cards">
            {part.cards.map((card) => (
              <li key={card.movie.id}>
                <MovieCard movie={card.movie} band={card.band} />
              </li>
            ))}
          </ul>
        ),
      )}
      {status === "failed" && (
        <div className="assistant-error" role="alert">
          <p>{t(exchange.error === "blocked" ? "assistant.blocked" : "assistant.failed")}</p>
          {onRetry && exchange.error !== "blocked" && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
              {t("common.retry")}
            </button>
          )}
        </div>
      )}
    </>
  );
}

export default function Assistant() {
  const t = useT();
  const chat = useAssistantChat();
  const [draft, setDraft] = useState("");
  const end = useRef<HTMLDivElement>(null);
  const { exchanges } = chat;
  const last = exchanges.at(-1);
  const blocked = chat.busy || chat.limit !== null;

  // Keep the newest words in view while they arrive.
  const tail = last ? `${last.id}:${last.parts.length}:${last.status}` : "";
  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end" });
  }, [tail]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (blocked || !draft.trim()) return;
    chat.ask(draft);
    setDraft("");
  }

  return (
    <div className="assistant">
      <header className="assistant-head">
        <div>
          <h1 className="screen-title">{t("assistant.title")}</h1>
          <p className="meta">{t("assistant.lead")}</p>
        </div>
        {exchanges.length > 0 && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={chat.restart}>
            <Icon as={RotateCcw} size={16} />
            {t("assistant.newConversation")}
          </button>
        )}
      </header>

      {exchanges.length === 0 ? (
        <section className="assistant-starters" aria-labelledby="assistant-starters">
          <h2 id="assistant-starters" className="eyebrow">
            {t("assistant.startersLabel")}
          </h2>
          <ul className="assistant-starter-list">
            {STARTERS.map((key) => (
              <li key={key}>
                <button type="button" className="assistant-starter" onClick={() => chat.ask(t(key))}>
                  {t(key)}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <ol className="assistant-log" role="log" aria-live="polite">
          {exchanges.map((exchange) => (
            <li key={exchange.id} className="assistant-exchange">
              <div className="assistant-question">
                <span className="visually-hidden">{t("assistant.you")}: </span>
                {exchange.question}
              </div>
              <article
                className="assistant-answer"
                aria-label={t("assistant.answer")}
                aria-busy={exchange.status === "waiting" || exchange.status === "streaming"}
              >
                <Answer
                  exchange={exchange}
                  onRetry={exchange === last && chat.retryable ? () => chat.ask(exchange.question) : undefined}
                />
              </article>
            </li>
          ))}
        </ol>
      )}

      {last?.status === "done" && last.followups.length > 0 && !chat.limit && (
        <section aria-label={t("assistant.followupsLabel")} className="chip-row assistant-followups">
          {last.followups.map((question) => (
            <button key={question} type="button" className="chip" onClick={() => chat.ask(question)}>
              {question}
            </button>
          ))}
        </section>
      )}
      <div ref={end} />

      <form className="assistant-form" onSubmit={submit}>
        <label htmlFor="assistant-input" className="visually-hidden">
          {t("assistant.inputLabel")}
        </label>
        <input
          id="assistant-input"
          className="field"
          value={draft}
          maxLength={MAX_CHARS}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={t("assistant.placeholder")}
          disabled={chat.limit !== null}
          autoComplete="off"
        />
        <button
          type="submit"
          className="btn btn-primary assistant-send"
          aria-label={t("assistant.send")}
          disabled={blocked || !draft.trim()}
        >
          <Icon as={Send} size={18} />
        </button>
      </form>
    </div>
  );
}
