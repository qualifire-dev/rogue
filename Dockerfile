FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# curl is used for the container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

# Rogue uses uv + uv.lock for reproducible installs
RUN pip install --no-cache-dir uv

# Copy dependency manifests first for better caching
COPY pyproject.toml uv.lock ./
COPY .python-version* ./

# Copy the repo
COPY . .

# Install deps from lockfile
RUN uv sync --locked --no-dev

# AgentCore HTTP runtime expects the service to listen on 8080
EXPOSE 8080

# Optional but recommended: container-level healthcheck uses AgentCore /ping
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8080/ping || exit 1

# Start the existing server on the required host/port
CMD ["uv", "run", "python", "-m", "rogue.run_server", "--host", "0.0.0.0", "--port", "8080"]