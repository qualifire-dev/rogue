# Stage 1: Build the TUI binary from source
FROM golang:1.23-alpine AS tui-builder

# Install make and git for the build process
RUN apk add --no-cache make git

# Set working directory
WORKDIR /app

# Copy the TUI source code
COPY packages/tui/ ./packages/tui/

# Copy version file for build metadata
COPY VERSION ./

# Build the TUI binary for Linux amd64
WORKDIR /app/packages/tui
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags "-X github.com/rogue/tui/internal/tui.Version=v$(cat ../../VERSION)" \
    -o dist/rogue-tui ./cmd/rogue

# Stage 2: Install Python dependencies using uv
FROM python:3.11-slim AS builder

# Install uv
RUN pip install uv

# Set environment variables for uv
ENV UV_NO_INTERACTION=1 \
    UV_VIRTUALENVS_CREATE=false

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy the VERSION file (required for dynamic version)
COPY VERSION ./

# Copy the README.md file (required for package metadata)
COPY README.md ./

# Copy the SDK directory (required for the local dependency)
COPY sdks/python/ ./sdks/python/

# Copy the main source code (needed for editable install)
COPY rogue/ ./rogue/

# Install dependencies (excluding dev dependencies)
RUN uv sync --frozen --no-dev

# Install the local packages in editable mode
RUN uv pip install -e ./sdks/python
RUN uv pip install -e .

# Stage 3: Create the final runtime image
FROM python:3.11-slim AS final

# Set environment variables for proper terminal rendering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TERM=xterm-256color \
    COLORTERM=truecolor

# Set working directory
WORKDIR /app

# Copy pre-installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the TUI binary from tui-builder stage
COPY --from=tui-builder /app/packages/tui/dist/rogue-tui /usr/local/bin/rogue-tui

# Make the TUI binary executable
RUN chmod +x /usr/local/bin/rogue-tui

# Copy the application source code
COPY . .

# Install the local packages in editable mode (same as builder stage)
RUN pip install -e ./sdks/python
RUN pip install -e .

# Expose port 8000 (default server port)
EXPOSE 8000

# Set the default command to run rogue-ai (starts server + TUI)
CMD ["rogue-ai"]

