"""Authentication abstraction.

Business logic depends on the `AuthProvider` interface and the provider-agnostic
`AuthIdentity` it returns — never on Clerk (or any vendor) directly. Concrete
providers (`dev`, `clerk`) are selected at runtime by `get_auth_provider()`.
This is the same swap-a-vendor-without-touching-core discipline used for the
LLM/embedding layer.
"""

from app.auth.base import AuthIdentity, AuthProvider
from app.auth.factory import get_auth_provider

__all__ = ["AuthIdentity", "AuthProvider", "get_auth_provider"]
