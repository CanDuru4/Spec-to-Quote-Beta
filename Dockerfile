# Spec-to-Quote Copilot — safe containerized environment
# Python 3.11+ (FastAPI), non-root user, minimal surface
FROM python:3.11-slim-bookworm

# Avoid encoding and buffer issues
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system deps only if needed (e.g. for PDF/image libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application (backend + frontend + docs)
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY docs/ ./docs/
COPY README.md .env.example ./

# Create uploads dir and optional data dirs
RUN mkdir -p backend/uploads backend/data/sample_inquiries

# Generate sample inquiry PDFs if not already present
RUN python backend/data/generate_sample_inquiries.py 2>/dev/null || true

# Run as non-root for safer environment (use volume with correct permissions for persistence)
RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8000

# Run from repo root so "backend" package is found
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
