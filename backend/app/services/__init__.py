"""Service layer: business logic and use-cases.

Services orchestrate repositories and enforce rules (uniqueness, provisioning,
role assignment). Routers call services; services call repositories. Services are
transport-agnostic — no FastAPI, no HTTP — so they are unit-testable in isolation
and reusable from workers, a CLI, or an MCP server.
"""
