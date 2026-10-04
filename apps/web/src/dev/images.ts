/**
 * DEV ONLY: real TMDB image paths for the fixture titles, so the mock API shows the
 * screens with real posters and backdrops. Read from the main database (`movies`
 * table, read-only query) on 2026-10-04. The Machinist, Enemy and Coherence are not in
 * the catalogue: they stay without images, which keeps the no-backdrop state in view.
 * Component tests do not use this file: their fixtures have no images.
 */
export const TMDB_PATHS: Record<string, { poster: string; backdrop: string }> = {
  "The Prestige": { poster: "/Ag2B2KHKQPukjH7WutmgnnSNurZ.jpg", backdrop: "/yaExZh6qE2cfyK3o4kAMEq0mkgy.jpg" },
  Memento: { poster: "/nzlv62aC0octS5AklAiWpXLX9Z0.jpg", backdrop: "/7Wev9JMo6R5XAfz2KDvXb7oPMmy.jpg" },
  Zodiac: { poster: "/6YmeO4pB7XTh8P8F960O1uA14JO.jpg", backdrop: "/3zCPI4JFc54xvLaJ71oI2KoP3az.jpg" },
  Prisoners: { poster: "/uhviyknTT5cEQXbn6vWIqfM4vGm.jpg", backdrop: "/3RFmTz5h2UuFWEV4oH00XICBR9y.jpg" },
  "Wind River": { poster: "/pySivdR845Hom4u4T2WNkJxe6Ad.jpg", backdrop: "/kQGxGXzYiCumY8kmXXpgbZyZQK8.jpg" },
  "The Guilty": { poster: "/42QPG6p7oLcLd4LQOPeSTLhqfMx.jpg", backdrop: "/wXZ2JmuQq58E9A4OcP9e8yeKFGR.jpg" },
  "Shutter Island": { poster: "/nrmXQ0zcZUL8jFLrakWc90IR8z9.jpg", backdrop: "/rbZvGN1A1QyZuoKzhCw8QPmf2q0.jpg" },
  Arrival: { poster: "/pEzNVQfdzYDzVK0XqxERIw2x2se.jpg", backdrop: "/8MUZz7oPXQftFTslZpRP3CVMOoq.jpg" },
  Heat: { poster: "/umSVjVdbVwtx5ryCA2QXL44Durm.jpg", backdrop: "/uI22JkEMediWyiRqhllNqeeGtW0.jpg" },
  "Amélie": { poster: "/nSxDa3M9aMvGVLoItzWTepQ5h5d.jpg", backdrop: "/6n53UI4mX9QMfe2S0Pgt8mGebY1.jpg" },
  "Spirited Away": { poster: "/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg", backdrop: "/6oaL4DP75yABrd5EbC4H2zq5ghc.jpg" },
  Oldboy: { poster: "/pWDtjs568ZfOTMbURQBYuT4Qxka.jpg", backdrop: "/rwf5SUTiEsmfkXAgy15R0UtJUtv.jpg" },
  Parasite: { poster: "/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg", backdrop: "/hiKmpZMGZsrkA3cdce8a7Dpos1j.jpg" },
  "Before Sunrise": { poster: "/kf1Jb1c2JAOqjuzA3H4oDM263uB.jpg", backdrop: "/qA2TyqPldTtoTVY3LKrNIG5g6bH.jpg" },
  "Mad Max: Fury Road": { poster: "/ulcAi4dKpAjHwYGS08vNyx9H6I9.jpg", backdrop: "/gqrnQA6Xppdl8vIb2eJc58VC1tW.jpg" },
  "Paddington 2": { poster: "/1OJ9vkD5xPt3skC6KguyXAgagRZ.jpg", backdrop: "/kRVUMsXFzhuXjr20JcCGc6TapxA.jpg" },
  "The Grand Budapest Hotel": { poster: "/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg", backdrop: "/jK65srQczOKTpW62wPxwwKztGgE.jpg" },
  Nightcrawler: { poster: "/j9HrX8f7GbZQm1BrBiR40uFQZSb.jpg", backdrop: "/bdI6U1mT0kCdTJ6TWtiFxQ42GSn.jpg" },
  "Gone Girl": { poster: "/ts996lKsxvjkO2yiYG0ht4qAicO.jpg", backdrop: "/iWak7wT0j6ycCc8lKr4NBz9c7n5.jpg" },
  Whiplash: { poster: "/7fn624j5lj3xTme2SgiLCeuedmO.jpg", backdrop: "/fRGxZuo7jJUWQsVg9PREb98Aclp.jpg" },
  Her: { poster: "/eCOtqtfvn7mxGl6nfmq4b1exJRc.jpg", backdrop: "/1YnZchmaGc8dchgRPDpR1KGrixA.jpg" },
};
