"""Ingestion dispatch — how a pending document gets processed.

The upload endpoint returns immediately after creating a `pending` row; the
dispatcher is what actually kicks off the pipeline. Two strategies behind one
interface:

* **InlineDispatcher (default)** runs the pipeline in a background task inside
  the API process. Zero extra services to run — ideal for local dev and demos.
  Trade-off: work is lost if the process restarts mid-job, and it shares the API
  process's resources (doesn't scale horizontally).
* **Arq worker (production)** would enqueue a Redis job for a separate worker
  pool. Wired via `INGEST_MODE=arq` in a later step; the inline path keeps the
  product fully runnable today.

Because the dispatcher builds a *fresh* DB session per job (ingestion is not tied
to the request that triggered it), it uses the app's session factory and
provider factories directly.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.embeddings.factory import get_embedding_provider
from app.services.ingestion_service import IngestionService
from app.storage.factory import get_object_storage
from app.vectorstore.factory import get_vector_store

logger = get_logger(__name__)


class IngestionDispatcher(ABC):
    @abstractmethod
    async def enqueue(self, document_id: uuid.UUID) -> None:
        """Schedule ingestion of a document. Must return quickly."""


class InlineDispatcher(IngestionDispatcher):
    async def enqueue(self, document_id: uuid.UUID) -> None:
        # Fire-and-forget on the running loop; keep a reference so it isn't GC'd.
        task = asyncio.create_task(self._run(document_id))
        _BACKGROUND_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_TASKS.discard)

    async def _run(self, document_id: uuid.UUID) -> None:
        try:
            async with get_sessionmaker()() as session:
                service = IngestionService(
                    session=session,
                    storage=get_object_storage(),
                    embedder=get_embedding_provider(),
                    vector_store=get_vector_store(),
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP,
                )
                await service.ingest(document_id)
        except Exception:  # noqa: BLE001 - background task must never crash silently
            logger.exception("inline_ingestion_error", document_id=str(document_id))


# Keep strong references to in-flight tasks (asyncio only holds weak ones).
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


@lru_cache
def get_ingestion_dispatcher() -> IngestionDispatcher:
    if settings.INGEST_MODE == "arq":
        # The Arq worker path is a planned enhancement; fall back to inline so the
        # app stays functional rather than failing at startup.
        logger.warning("arq_ingest_mode_not_implemented_falling_back_to_inline")
    return InlineDispatcher()
