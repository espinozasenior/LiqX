# LiqX Agent Dockerfile
# Multi-stage build for Python agents

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv pip
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY agents/ ./agents/
COPY data/ ./data/
COPY metta/ ./metta/
COPY config/ ./config/
COPY fusion_plus_bridge.py ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash agent
RUN chown -R agent:agent /app
USER agent

# Default command (will be overridden in docker-compose)
CMD ["python", "-m", "agents.position_monitor"]
