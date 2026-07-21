"""Cross-cutting concerns: configuration, logging, security, exceptions.

Everything in `core` may be imported by any layer, but `core` must not import
from `api`, `services`, or `repositories`. It sits at the center of the
dependency graph — dependencies point *inward* toward it.
"""
