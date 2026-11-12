# ==============================================================================
# Datheon Python + FastAPI Backend Development Internship
# Production-Conscious Dockerfile
# ==============================================================================

# Base image: Official slim Python 3.11 Debian image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable immediate stdout flushing
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATABASE_URL="sqlite+aiosqlite:////app/data/datheon_bookstore.db"

# Set working directory
WORKDIR /app

# Install security updates and lightweight system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user for least privilege security
RUN useradd -m -u 1000 appuser

# Install Python dependencies first for optimal Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and bootstrap scripts
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create persistent storage volume mount directory for SQLite database
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI Uvicorn service port
EXPOSE 8000

# Docker healthcheck pinging the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 else 1)" || exit 1

# Launch application via Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
