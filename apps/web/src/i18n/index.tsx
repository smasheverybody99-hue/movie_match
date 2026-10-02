import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import type { Lang } from "../lib/types";
import { en, type Message, type MessageKey } from "./en";
import { ru } from "./ru";
import { uz } from "./uz";

export type { Message, MessageKey };

export const DICTIONARIES: Record<Lang, Record<MessageKey, Message>> = { en, uz, ru };
/** Menu order (TZ 1.8). English is the default; the others are chosen by the user. */
export const LANGS: readonly Lang[] = ["en", "uz", "ru"];
export const DEFAULT_LANG: Lang = "en";

const STORAGE_KEY = "mm.lang";

type Vars = Record<string, string | number>;
export type Translate = (key: MessageKey, vars?: Vars) => string;

/** Fill `{name}` placeholders. An unknown placeholder is left as written. */
export function format(template: string, vars: Vars = {}): string {
  return template.replace(/\{(\w+)\}/g, (whole, name: string) =>
    name in vars ? String(vars[name]) : whole,
  );
}

/** The form of `message` for the count `vars.n` in `lang`; `other` without a count. */
export function pickForm(lang: Lang, message: Message, vars: Vars = {}): string {
  if (typeof message === "string") return message;
  const n = vars.n;
  if (typeof n !== "number") return message.other;
  const category = new Intl.PluralRules(lang).select(n);
  return message[category] ?? message.other;
}

export function translate(lang: Lang, key: MessageKey, vars?: Vars): string {
  return format(pickForm(lang, DICTIONARIES[lang][key], vars), vars);
}

function isLang(value: unknown): value is Lang {
  return (LANGS as readonly unknown[]).includes(value);
}

function storedLang(): Lang {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (isLang(value)) return value;
  } catch {
    // Storage can be unavailable (private mode); the default is fine.
  }
  return DEFAULT_LANG; // never the browser's language: the user chooses (TZ 1.8)
}

interface I18n {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: Translate;
}

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children, lang: fixed }: { children: ReactNode; lang?: Lang }) {
  const [lang, setLangState] = useState<Lang>(() => fixed ?? storedLang());

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Not remembered across reloads; the switch still works for this visit.
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18n>(
    () => ({ lang, setLang, t: (key, vars) => translate(lang, key, vars) }),
    [lang, setLang],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n needs <I18nProvider>");
  return value;
}

export function useT(): Translate {
  return useI18n().t;
}
