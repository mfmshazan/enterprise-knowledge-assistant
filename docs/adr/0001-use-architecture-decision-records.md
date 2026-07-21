# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

This is an open-source product intended to be forked and extended. Contributors
need to understand *why* the system is built the way it is, not just *how*.
Decisions made implicitly in code (which vector DB, which auth model, sync vs.
async) are expensive to reverse once undocumented rationale is lost.

## Decision

We keep lightweight **Architecture Decision Records** (ADRs) in `docs/adr/`.
Each significant, hard-to-reverse decision gets one short, immutable file:
Context → Decision → Consequences. Superseded ADRs are marked, not deleted.

## Consequences

- New contributors can read the ADR log to onboard on the "why".
- Reversing a decision is an explicit act (a new ADR that supersedes an old one).
- Slight overhead per major decision — acceptable for the clarity gained.
