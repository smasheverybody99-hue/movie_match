import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import sharedSpec from "../../../../packages/shared/traits.json";
import { TRAIT_KEYS } from "../lib/traits";
import type { Lang } from "../lib/types";
import { en, type Message } from "./en";
import {
  DEFAULT_LANG,
  DICTIONARIES,
  format,
  I18nProvider,
  LANGS,
  pickForm,
  translate,
  useI18n,
} from "./index";

/** en is the source (TZ 1.8); every other language is checked against it. */
const SOURCE_KEYS = Object.keys(en).sort();
const OTHERS = LANGS.filter((lang) => lang !== "en");

function forms(message: Message): string[] {
  return typeof message === "string" ? [message] : Object.values(message);
}

function placeholders(text: string): string[] {
  return [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1] ?? "").sort();
}

function categories(lang: Lang): string[] {
  return new Intl.PluralRules(lang).resolvedOptions().pluralCategories;
}

describe("dictionaries", () => {
  it("are en, uz and ru, in the menu order", () => {
    expect(LANGS).toEqual(["en", "uz", "ru"]);
    expect(Object.keys(DICTIONARIES).sort()).toEqual([...LANGS].sort());
  });

  it.each(OTHERS)("%s has exactly the keys of en, no more, no fewer", (lang) => {
    const keys = Object.keys(DICTIONARIES[lang]).sort();
    expect(keys.filter((key) => !SOURCE_KEYS.includes(key)), "extra keys").toEqual([]);
    expect(SOURCE_KEYS.filter((key) => !keys.includes(key)), "missing keys").toEqual([]);
    expect(keys.length).toBe(SOURCE_KEYS.length);
  });

  it.each(LANGS)("%s has no empty string", (lang) => {
    for (const [key, message] of Object.entries(DICTIONARIES[lang])) {
      for (const text of forms(message)) expect(text.trim(), key).not.toBe("");
    }
  });

  it.each(OTHERS)("%s uses the placeholders of en in every string and form", (lang) => {
    for (const [key, source] of Object.entries(DICTIONARIES.en)) {
      const expected = placeholders(forms(source)[0] ?? "");
      for (const text of [...forms(source), ...forms(DICTIONARIES[lang][key as keyof typeof en])]) {
        expect(placeholders(text), `${lang} ${key}`).toEqual(expected);
      }
    }
  });

  it.each(LANGS)("%s gives every plural message all of its plural forms", (lang) => {
    for (const [key, message] of Object.entries(DICTIONARIES[lang])) {
      if (typeof message === "string") continue;
      expect(Object.keys(message).sort(), `${lang} ${key}`).toEqual(categories(lang).sort());
    }
  });

  it("Russian inflects every message that English inflects", () => {
    for (const [key, message] of Object.entries(DICTIONARIES.en)) {
      if (typeof message === "string") continue;
      expect(typeof DICTIONARIES.ru[key as keyof typeof en], key).toBe("object");
    }
  });

  it("names each language in itself, the same in every dictionary", () => {
    const names = { "lang.en": "English", "lang.uz": "O'zbek", "lang.ru": "Русский" };
    for (const lang of LANGS) {
      for (const [key, name] of Object.entries(names)) {
        expect(DICTIONARIES[lang][key as keyof typeof en], `${lang} ${key}`).toBe(name);
      }
    }
  });

  it("has a label for every trait, equal to packages/shared/traits.json", () => {
    for (const dimension of sharedSpec.dimensions) {
      const key = `trait.${dimension.key}` as keyof typeof en;
      expect(DICTIONARIES.en[key], dimension.key).toBe(dimension.label_en);
      expect(DICTIONARIES.uz[key], dimension.key).toBe(dimension.label_uz);
      expect(DICTIONARIES.ru[key], dimension.key).toBe(dimension.label_ru);
    }
    expect(sharedSpec.dimensions.map((d) => d.key)).toEqual([...TRAIT_KEYS]);
  });

  it("never shows a person the setup's variable names", () => {
    for (const lang of LANGS) {
      expect(DICTIONARIES[lang]["welcome.notConfigured"], lang).not.toMatch(/VITE_|SUPABASE/);
    }
  });

  it("Russian: the match badge and the panel heading are two different words", () => {
    expect(DICTIONARIES.ru["band.strong"]).toBe("Сильное совпадение");
    expect(DICTIONARIES.ru["band.strongHeading"]).toBe("Больше всего подходит");
  });

  it("Russian names the section Movie DNA and never declines it", () => {
    const texts = Object.values(DICTIONARIES.ru).flatMap(forms);
    // "DNA" only inside the name; a film's own profile is ДНК
    for (const text of texts) expect(text.replace(/Movie DNA/g, ""), text).not.toMatch(/DNA/);
    expect(texts.filter((text) => /свою Movie DNA|Моя Movie DNA/.test(text))).toEqual([]);
  });
});

describe("format and translate", () => {
  it("fills placeholders and leaves unknown ones", () => {
    expect(format("{a} and {b}", { a: 1 })).toBe("1 and {b}");
  });

  it("translates in the requested language", () => {
    const vars = { title: "Heat" };
    expect(translate("en", "feed.section.because_you_loved", vars)).toBe("Because you loved Heat");
    expect(translate("uz", "feed.section.because_you_loved", vars)).toBe("Heat yoqqani uchun");
    expect(translate("ru", "feed.section.because_you_loved", vars)).toBe(
      "Потому что вам понравился фильм «Heat»",
    );
  });

  it("picks the English form by count", () => {
    expect(translate("en", "feed.notEnough", { n: 1 })).toBe(
      "Rate 1 more film to get recommendations.",
    );
    expect(translate("en", "feed.notEnough", { n: 2 })).toBe(
      "Rate 2 more films to get recommendations.",
    );
  });

  it.each([
    [1, "фильм"],
    [3, "фильма"],
    [5, "фильмов"],
    [11, "фильмов"],
    [21, "фильм"],
    [24, "фильма"],
  ])("picks the Russian form for %i: %s", (n, word) => {
    expect(translate("ru", "dna.rateMore", { n })).toBe(
      `Оцените ещё ${n} ${word}, чтобы открыть раздел Movie DNA.`,
    );
  });

  it("uses the same Uzbek string for any count", () => {
    expect(translate("uz", "feed.notEnough", { n: 1 })).toBe(
      "Tavsiya uchun yana 1 ta film baholang.",
    );
  });

  it("falls back to `other` without a count", () => {
    expect(pickForm("en", { one: "a film", other: "films" })).toBe("films");
  });
});

describe("I18nProvider", () => {
  const STORAGE_KEY = "mm.lang";

  function wrapper({ children }: { children: ReactNode }) {
    return <I18nProvider>{children}</I18nProvider>;
  }

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("starts in English when nothing was chosen", () => {
    localStorage.clear();
    const { result } = renderHook(() => useI18n(), { wrapper });
    expect(DEFAULT_LANG).toBe("en");
    expect(result.current.lang).toBe("en");
    expect(document.documentElement.lang).toBe("en");
  });

  it("ignores the browser's language", () => {
    localStorage.clear();
    vi.spyOn(navigator, "language", "get").mockReturnValue("ru-RU");
    vi.spyOn(navigator, "languages", "get").mockReturnValue(["ru-RU", "uz-UZ"]);
    const { result } = renderHook(() => useI18n(), { wrapper });
    expect(result.current.lang).toBe("en");
  });

  it.each(["uz", "ru"] as const)("opens in the saved choice: %s", (lang) => {
    localStorage.setItem(STORAGE_KEY, lang);
    const { result } = renderHook(() => useI18n(), { wrapper });
    expect(result.current.lang).toBe(lang);
  });

  it("ignores a saved value that is not a language", () => {
    localStorage.setItem(STORAGE_KEY, "fr");
    const { result } = renderHook(() => useI18n(), { wrapper });
    expect(result.current.lang).toBe("en");
  });

  it("saves the choice, so the next visit opens in it", () => {
    localStorage.clear();
    const first = renderHook(() => useI18n(), { wrapper });
    act(() => first.result.current.setLang("ru"));
    expect(first.result.current.lang).toBe("ru");
    expect(first.result.current.t("profile.language")).toBe("Язык");
    expect(localStorage.getItem(STORAGE_KEY)).toBe("ru");
    first.unmount();

    const next = renderHook(() => useI18n(), { wrapper });
    expect(next.result.current.lang).toBe("ru");
  });
});
