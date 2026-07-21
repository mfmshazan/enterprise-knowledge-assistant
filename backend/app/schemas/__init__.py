"""Pydantic schemas (DTOs) — the shapes that cross the API boundary.

These are deliberately separate from SQLAlchemy ORM models (`app.models`).
ORM models describe how data is *stored*; schemas describe how it is
*transferred*. Decoupling them prevents leaking internal columns to clients and
lets the API contract evolve independently of the database schema.
"""
