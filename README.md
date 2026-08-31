<div align="center">

# 🧠 Enterprise Knowledge Assistant

**An open-source, production-grade RAG + Agentic AI platform.**
Upload documents and websites, then let your organization ask questions and get
**cited, verified answers** — powered by a multi-agent LangGraph pipeline.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Backend: FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend: Next.js 15](https://img.shields.io/badge/frontend-Next.js_15-black.svg)](https://nextjs.org/)

</div>

---

## ✨ What it does

- **Ingest** PDF / DOCX / Markdown files and crawled websites.
- **Retrieve** relevant context with a Qdrant-backed vector search + reranking.
- **Reason** over that context with a multi-agent pipeline (Planner → Retrieval →
  Verification → Generation) orchestrated by **LangGraph**.
- **Answer** with inline **source citations** that link back to the exact chunk.
- **Remember** conversation history per user and workspace.
- **Govern** it all with organizations, roles, and an admin dashboard.

## 🏗️ Architecture at a glance

```
Next.js 15 ──REST/SSE──▶ FastAPI ──▶ Services / Agents (LangGraph)
                              │
        ┌─────────────┬───────┼────────────┬──────────────┐
        ▼             ▼       ▼            ▼              ▼
    PostgreSQL     Redis    Qdrant     MinIO/S3     Ingestion workers
   (source of     (cache/  (vector    (raw files)   (extract→chunk→
    truth, RBAC)   queue)   index)                    embed→upsert)
```

Two decoupled loops:

- **Ingestion (write path)** — asynchronous workers turn raw files into embedded,
  searchable chunks. Qdrant is a *derived index*: it can always be rebuilt from
  PostgreSQL + object storage.
- **Query (read path)** — synchronous, latency-sensitive; retrieves context and
  runs the agent pipeline to produce a grounded, cited answer.

See [`docs/`](./docs) for the full architecture and Architecture Decision Records.

## 🧰 Tech stack

| Layer         | Choice                                                        |
|---------------|---------------------------------------------------------------|
| Frontend      | Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui, React Query |
| Backend       | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2 (async)       |
| AI            | LangChain, LangGraph, OpenAI (pluggable provider interface)   |
| Data          | PostgreSQL, Qdrant (vectors), Redis (cache/queue)             |
| Storage       | MinIO / S3-compatible                                         |
| Auth          | Clerk (pluggable `AuthProvider` interface)                    |
| Infra         | Docker Compose, GitHub Actions, uv                            |

## 🚀 Quick start

**Prerequisites:** Docker + Docker Compose. (For local, non-container dev:
[uv](https://docs.astral.sh/uv/) and Node.js 20+.)

```bash
# 1. Clone and configure
git clone https://github.com/your-org/enterprise-knowledge-assistant.git
cd enterprise-knowledge-assistant
cp .env.example .env          # then edit secrets

# 2. Bring up the whole stack
make up                       # docker compose up -d --build

# 3. Verify
curl http://localhost:8000/health      # backend
open http://localhost:3000             # frontend
```

Useful targets (`make help` for all):

| Command        | What it does                                   |
|----------------|------------------------------------------------|
| `make up`      | Start the full stack in Docker                 |
| `make down`    | Stop the stack                                 |
| `make be-dev`  | Run the API locally with hot reload            |
| `make fe-dev`  | Run the Next.js dev server                     |
| `make check`   | Run the full lint + type + test quality gate   |

## 🗺️ Roadmap

The project is built in phases, each ending in a runnable, tested state:

- [x] **Phase 1** — Project scaffold, Docker stack, health checks, CI
- [x] **Phase 2** — Authentication, organizations & users (RBAC)
- [x] **Phase 3** — Document ingestion pipeline (extract → chunk → embed → index)
- [x] **Phase 4** — RAG retrieval (org-scoped semantic search)
- [x] **Phase 5** — AI chat with citations
- [x] **Phase 6** — Agentic AI (LangGraph: plan → retrieve → generate → verify)
- [ ] **Phase 7** — Enterprise features
- [ ] **Phase 8** — Deployment & monitoring

## 🤝 Contributing

This is designed to be forked, self-hosted, and extended. Auth and AI providers
are behind interfaces so you can swap Clerk → Auth.js or OpenAI → local models
without touching business logic. See [`docs/adr`](./docs/adr) for the reasoning
behind key decisions.

## 📄 License

[Apache 2.0](./LICENSE).
