import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

/**
 * F0 placeholder: proves the web app reaches the API.
 * Replaced by the real feed in F3.
 */
export default function Home() {
  const { data, isPending, error } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
  });

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "64px 16px" }}>
      <p
        style={{
          color: "var(--gold)",
          letterSpacing: ".16em",
          textTransform: "uppercase",
          fontSize: 12,
          fontWeight: 700,
          margin: "0 0 12px",
        }}
      >
        Movie Match
      </p>
      <h1 style={{ fontSize: 44, marginBottom: 16 }}>Skelet ishlayapti.</h1>
      <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
        Bu F0 fazasining tekshiruv sahifasi. F3 da haqiqiy feed bilan almashtiriladi.
      </p>

      <div
        style={{
          marginTop: 32,
          background: "var(--surface)",
          border: "1px solid var(--line)",
          borderRadius: "var(--radius)",
          padding: 20,
        }}
      >
        <strong style={{ fontSize: 13, letterSpacing: ".08em", textTransform: "uppercase" }}>
          API holati
        </strong>
        <p style={{ color: "var(--muted)", margin: "8px 0 0" }}>
          {isPending && "Tekshirilmoqda…"}
          {error && (
            <span style={{ color: "var(--red)" }}>
              Ulanmadi. API ishga tushganmi? ({String(error)})
            </span>
          )}
          {data && (
            <span style={{ color: "var(--green)" }}>
              Ulandi · {data.trait_dimensions} ta trait o'lchovi yuklangan
            </span>
          )}
        </p>
      </div>
    </main>
  );
}
