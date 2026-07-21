# =============================================================================
# Multi-stage build for the FastAPI backend.
#
# Stage 1 (builder): use the official `uv` image to resolve and install deps
#   into a self-contained virtualenv. Keeping this separate means the heavy
#   toolchain never ships in the final image.
# Stage 2 (runtime): a slim Python image with only the venv + app code, run as
#   a non-root user. Smaller attack surface, faster pulls.
# =============================================================================

# ---------- Stage 1: builder ----------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install dependencies first (cached layer) using only the lockfiles.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project --no-dev || uv sync --no-install-project

# Now copy source and install the project itself.
COPY app ./app
RUN uv sync --no-dev || uv sync

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create an unprivileged user to run the app.
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app ./app

USER app

EXPOSE 8000

# Liveness check baked into the image so orchestrators can use it directly.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/health').status_code==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
