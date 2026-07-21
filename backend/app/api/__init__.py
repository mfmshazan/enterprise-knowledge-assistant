"""HTTP transport layer.

Routers here handle *only* HTTP concerns: parsing, validation, authorization,
serialization. They delegate all business logic to `app.services`. Keeping
routers thin is what makes the business logic independently testable.
"""
