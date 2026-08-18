# -----------------------------------------------------------------------------
# Base Image: Python 3.11 Slim Footprint
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# 1. Environment Variables:
# - PYTHONUNBUFFERED=1: Flushes stdout/stderr immediately (critical for GCP Cloud Logging)
# - PYTHONDONTWRITEBYTECODE=1: Prevents creation of .pyc files inside container
# - PORT=8000: Default port fallback (overridden dynamically by GCP Cloud Run)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# 2. System Dependencies: Minimal packages for C-extensions and health monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Layer Caching Optimization:
# Copy requirements FIRST so Docker caches dependency layers unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy Application Source & Embedded Vector Database
COPY src/ ./src/
COPY qdrant_db/ ./qdrant_db/

# 5. Security Hardening (Least-Privilege Non-Root Execution):
# Create a dedicated non-root application user and transfer file permissions.
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose container network port
EXPOSE 8000

# 6. Entrypoint Execution:
# Binds Uvicorn to 0.0.0.0 and dynamically listens on ${PORT} provided by Cloud Run.
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT}