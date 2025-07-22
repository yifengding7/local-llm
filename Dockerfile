# syntax=docker/dockerfile:1

############################
# Build stage
############################
FROM python:3.12-slim AS builder

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl libffi-dev && \
    pip install --no-cache-dir poetry==1.8.2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* requirements.txt ./

# Install prod deps only, no dev, into virtualenv
RUN poetry export --without-hashes --only main -f requirements.txt | pip install --no-cache-dir -r -

# Copy source
COPY . .

############################
# Runtime stage
############################
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=on

# Create non-root user
RUN useradd -m appuser
WORKDIR /app

# Copy installed site-packages and source code from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "ai_monitor.core.main:app", "--host", "0.0.0.0", "--port", "8000"] 