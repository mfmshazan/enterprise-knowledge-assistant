"""Repository layer: the *only* place that talks to the database via the ORM.

Why a repository layer at all? It concentrates data-access logic behind small,
intention-revealing methods (`get_by_external_id`, `list_for_user`) so that:

* Services/routers express *what* they want, not raw SQL.
* Query patterns are reused instead of re-derived (and mis-scoped) per call site.
* From Phase 3, tenant-owned repositories can *enforce* `org_id` scoping in one
  place — a query that isn't org-scoped simply won't exist.
"""
