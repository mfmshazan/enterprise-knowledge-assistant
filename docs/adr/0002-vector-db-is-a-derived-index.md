# ADR-0002: PostgreSQL is the source of truth; Qdrant is a derived index

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

RAG systems store two representations of a document chunk: its **canonical
record** (text, metadata, ownership) and its **embedding vector** (for
similarity search). It is tempting to treat the vector database as primary,
but vector DBs optimize for approximate nearest-neighbor search, not for
transactional integrity, relational joins, or point-in-time recovery.

## Decision

PostgreSQL holds the canonical record for every entity, including a
`document_chunks` row per chunk with enough information (source document,
position, text, model id) to **regenerate its embedding**. Qdrant stores only
vectors plus a minimal payload (`org_id`, `chunk_id`, filters). Qdrant is
treated as a rebuildable index: if it is lost or the embedding model changes,
we re-embed from PostgreSQL + object storage.

## Consequences

- **Recoverability:** the vector store can be dropped and rebuilt at any time.
- **Model migration:** switching embedding models is a re-index job, not data loss.
- **Multi-tenant isolation:** enforced by `org_id` payload filters in Qdrant and
  row scoping in PostgreSQL — the same tenant boundary in both stores.
- **Cost:** we store chunk text twice (Postgres + object storage of the raw file).
  Accepted for the durability and flexibility it buys.
