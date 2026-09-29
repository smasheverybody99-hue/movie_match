import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import type { Lang } from "../lib/types";
import { en } from "./en";
import { uz, type MessageKey } from "./uz";

export type { MessageKey };

export const DICTIONARIES: Record<Lang, Record<MessageKey, string>> = { uz, en };
export const LANGS: readonly Lang[] = ["uz", "en"];

const STORAGE_KEY = "mm.lang";

type Vars = Record<string, string | number>;
export type Translate = (key: MessageKey, vars?: Vars) => string;

/** Fill `{name}` placeholders. An unknown placeholder is left as written. */
export function format(template: string, vars: Vars = {}): string {
  return template.replace(/\{(\w+)\}/g, (whole, name: string) =>
    name in vars ? String(vars[name]) : whole,
  );
}

export function translate(lang: Lang, key: MessageKey, vars?: Vars): string {
  return format(DICTIONARIES[lang][key], vars);
}

function storedLang(): Lang {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "uz" || value === "en") return value;
  } catch {
    // Storage can be unavailable (private mode); the default is fine.
  }
  return "uz";
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
