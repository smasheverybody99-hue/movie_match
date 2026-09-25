# ADR 0001 — Stack

Date: 2026-09-24 · Status: accepted

## Context

Solo developer, ~27 hours/week, AI-assisted. Two clients required: web and mobile. The
product's core is a data + AI pipeline, not the UI.

## Decision

- **API: Python 3.12 + FastAPI.** The trait pipeline, embeddings and recommendation
  scoring are data work; Python's ecosystem carries that with less custom code. Async
  FastAPI keeps request throughput adequate for the expected load.
- **Web: React 19 + Vite + TypeScript.** Vite for now; if movie pages need SEO, migrate to
  Next.js — decide before F3 ends, not after.
- **Mobile: Flutter 3.47.** One codebase for iOS and Android, one developer.
- **DB: Supabase Postgres + pgvector.** Managed Postgres, auth included, vector search in
  the same database as the relational data — no second datastore to operate.

## Consequence

Two languages in the repo (Python, TypeScript) plus Dart. Type contracts between API and
web are maintained by hand and must change in the same commit.

## Alternatives rejected

- **Node/Fastify API**: one less language, but the data pipeline work would fight the
  ecosystem.
- **Separate vector DB (Pinecone, Qdrant)**: more capability than needed at this scale,
  and another service to pay for and operate.
