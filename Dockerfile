# =======================================================
# MJ Assistant - Containerized Bridge & Core Server
# =======================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend ./backend
COPY data ./data
COPY main.py .

# Create required directories
RUN mkdir -p /app/data/skills /app/data/autonomous_tasks

# Expose HTTP API & Cockpit port
EXPOSE 8000
EXPOSE 8001

# Healthcheck to ensure Bridge server is active
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/status || exit 1

# Start the Fast API / WebSocket Bridge Server
CMD ["uvicorn", "backend.bridge.server:app", "--host", "0.0.0.0", "--port", "8000"]
