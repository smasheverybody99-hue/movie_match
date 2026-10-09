import { describe, expect, it } from "vitest";

import { DICTIONARIES, LANGS, translate } from "../i18n";
import { score } from "./format";
import { genreLabel, KNOWN_GENRES } from "./genres";

const t = (lang: (typeof LANGS)[number]) => (key: Parameters<typeof translate>[1]) => translate(lang, key);

describe("genreLabel", () => {
  it("covers TMDB's movie genres, as the catalogue stores them (checked 2026-10-09)", () => {
    expect([...KNOWN_GENRES].sort()).toEqual(
      ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family",
        "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction",
        "TV Movie", "Thriller", "War", "Western"].sort(),
    );
  });

  it("translates a genre, and in English shows it as sent", () => {
    expect(genreLabel("Adventure", t("ru"))).toBe("Приключения");
    expect(genreLabel("Science Fiction", t("ru"))).toBe("Фантастика");
    expect(genreLabel("Adventure", t("uz"))).toBe("Sarguzasht");
    for (const genre of KNOWN_GENRES) expect(genreLabel(genre, t("en"))).toBe(genre);
  });

  it("shows a genre TMDB adds later as sent", () => {
    expect(genreLabel("Noir", t("ru"))).toBe("Noir");
  });

  it("has a name in every language for every genre", () => {
    for (const lang of LANGS) {
      for (const genre of KNOWN_GENRES) expect(genreLabel(genre, t(lang)).trim(), `${lang} ${genre}`).not.toBe("");
    }
    expect(Object.keys(DICTIONARIES.ru).filter((key) => key.startsWith("genre."))).toHaveLength(KNOWN_GENRES.length);
  });
});

describe("score", () => {
  it("writes one decimal with the language's separator", () => {
    expect(score(7, "en")).toBe("7.0");
    expect(score(6.6, "en")).toBe("6.6");
    expect(score(7, "ru")).toBe("7,0");
    expect(score(6.6, "ru")).toBe("6,6");
    expect(score(7.25, "uz")).toBe("7,3");
  });
});
