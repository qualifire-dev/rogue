# Docker Usage Guide

Complete guide for running Rogue with Docker and Docker Compose.

## Table of Contents

- [Building the Image](#building-the-image)
- [Running with Docker](#running-with-docker)
- [Running with Docker Compose](#running-with-docker-compose)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Building the Image

### Standard Build

```bash
docker build -t rogue-app .
```

### Build Options

```bash
# No cache (fresh build)
docker build --no-cache -t rogue-app .

# Specific platform
docker build --platform linux/amd64 -t rogue-app .

# With version tag
docker build -t rogue-app:1.0.0 -t rogue-app:latest .
```

---

## Running with Docker

### Default Mode (Server + TUI)

Starts the server and launches the interactive TUI:

```bash
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  rogue-app
```

**Flags explained:**
- `-it`: Interactive terminal (required for TUI)
- `--rm`: Auto-remove container when stopped
- `-e`: Environment variable (API key)
- `-p 8000:8000`: Expose server port

### With Persistent Storage

```bash
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  -v ~/.config/rogue:/root/.config/rogue \
  -v $(pwd)/.rogue:/app/.rogue \
  rogue-app
```

**Volumes:**
- `~/.config/rogue`: TUI configuration (API keys, preferences)
- `.rogue/`: Scenarios, reports, business context

---

### Running Individual Components

#### Server Only (Background)

```bash
docker run -d --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  --name rogue-server \
  rogue-app \
  rogue-ai server --host 0.0.0.0 --port 8000
```

**Important:** Always use `--host 0.0.0.0` in Docker containers. The default `127.0.0.1` only accepts connections from within the same container and won't allow external access.

**Access API:** http://localhost:8000/docs

**View logs:**
```bash
docker logs -f rogue-server
```

**Stop server:**
```bash
docker stop rogue-server
```

#### Server with Debug Mode

```bash
docker run -d --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  --name rogue-server \
  rogue-app \
  rogue-ai server --host 0.0.0.0 --debug
```

---

#### TUI Client Only

```bash
# First, start the server
docker run -d --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  --name rogue-server \
  rogue-app \
  rogue-ai server --host 0.0.0.0

# Then connect TUI
docker run -it --rm \
  --network container:rogue-server \
  rogue-app \
  rogue-ai tui
```

---

#### Web UI (Gradio)

```bash
docker run -d --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  -p 7860:7860 \
  --name rogue-ui \
  rogue-app \
  rogue-ai ui --port 7860
```

**Access Web UI:** http://localhost:7860

**With custom server URL:**
```bash
docker run -d --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 7860:7860 \
  --name rogue-ui \
  rogue-app \
  rogue-ai ui --port 7860 --rogue-server-url http://rogue-server:8000
```

---

#### CLI Mode (CI/CD)

```bash
docker run --rm \
  -e OPENAI_API_KEY="sk-..." \
  -v $(pwd)/.rogue:/app/.rogue \
  rogue-app \
  rogue-ai cli \
    --evaluated-agent-url http://host.docker.internal:10001 \
    --judge-llm openai/gpt-4o-mini \
    --business-context-file /app/.rogue/business_context.md \
    --output-report-file /app/.rogue/report.md
```

**Note:** Use `host.docker.internal` to access services running on your host machine.

**Example with all options:**
```bash
docker run --rm \
  -e OPENAI_API_KEY="sk-..." \
  -v $(pwd)/.rogue:/app/.rogue \
  rogue-app \
  rogue-ai cli \
    --evaluated-agent-url http://host.docker.internal:10001 \
    --evaluated-agent-auth-type no_auth \
    --judge-llm openai/gpt-4o-mini \
    --business-context-file /app/.rogue/business_context.md \
    --input-scenarios-file /app/.rogue/scenarios.json \
    --output-report-file /app/.rogue/report.md \
    --deep-test-mode \
    --debug
```

---

#### Running with Example Agent

```bash
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  -p 10001:10001 \
  rogue-app \
  rogue-ai --example=tshirt_store --example-host 0.0.0.0 --example-port 10001
```

---

## Running with Docker Compose

The repository includes a production-ready `docker-compose.yml` that starts the server and web UI together.

### Quick Start

1. **Set environment variables:**

```bash
# Option 1: Export variables
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
export ANTHROPIC_API_KEY="sk-..."

# Option 2: Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=sk-...
EOF
```

2. **Start services:**

```bash
docker-compose up -d
```

3. **Access applications:**
   - **Server API:** http://localhost:8000/docs
   - **Web UI:** http://localhost:7860

### Managing Services

```bash
# View running services
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f rogue-server
docker-compose logs -f rogue-ui

# Restart a service
docker-compose restart rogue-server

# Stop services (containers remain)
docker-compose stop

# Start stopped services
docker-compose start

# Stop and remove containers
docker-compose down

# Stop, remove containers, and delete volumes
docker-compose down -v
```

### Running Individual Services

```bash
# Start only the server
docker-compose up -d rogue-server

# Start only the UI (server must be running)
docker-compose up -d rogue-ui
```

### Scaling Services

```bash
# Run multiple UI instances
docker-compose up -d --scale rogue-ui=3
```

### Rebuilding After Changes

```bash
# Rebuild images
docker-compose build

# Rebuild and restart
docker-compose up -d --build

# Force rebuild (no cache)
docker-compose build --no-cache
```

---

## Configuration

### Environment Variables

All LLM provider API keys can be set via environment variables:

```bash
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -e GOOGLE_API_KEY="..." \
  -e ANTHROPIC_API_KEY="sk-..." \
  -e GROQ_API_KEY="..." \
  -p 8000:8000 \
  rogue-app
```

**For docker-compose**, add them to `.env`:

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=sk-...
```

### Persistent Storage

#### Using Named Volumes

```bash
# Create volumes
docker volume create rogue-config
docker volume create rogue-data

# Run with volumes
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  -v rogue-config:/root/.config/rogue \
  -v rogue-data:/app/.rogue \
  rogue-app
```

#### Using Host Directories

```bash
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8000:8000 \
  -v ~/.config/rogue:/root/.config/rogue \
  -v $(pwd)/data:/app/.rogue \
  rogue-app
```

**Windows (PowerShell):**
```powershell
docker run -it --rm `
  -e OPENAI_API_KEY="sk-..." `
  -p 8000:8000 `
  -v ${HOME}\.config\rogue:/root/.config/rogue `
  -v ${PWD}\data:/app/.rogue `
  rogue-app
```

### Port Configuration

Change host ports if defaults are already in use:

```bash
# Server on port 9000 instead of 8000
docker run -it --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 9000:8000 \
  rogue-app

# Web UI on port 8080 instead of 7860
docker run -d --rm \
  -e OPENAI_API_KEY="sk-..." \
  -p 8080:7860 \
  rogue-app \
  rogue-ai ui --port 7860
```

**For docker-compose**, edit `docker-compose.yml`:

```yaml
services:
  rogue-server:
    ports:
      - "9000:8000"  # Change 9000 to your desired port
```

### Network Configuration

#### Connect to External Agent

```bash
# Agent on host machine
docker run --rm \
  -e OPENAI_API_KEY="sk-..." \
  rogue-app \
  rogue-ai cli \
    --evaluated-agent-url http://host.docker.internal:10001
```

#### Agent in Docker Network

```bash
# Create network
docker network create rogue-net

# Run agent
docker run -d --rm \
  --network rogue-net \
  --name my-agent \
  my-agent-image

# Run Rogue CLI
docker run --rm \
  --network rogue-net \
  -e OPENAI_API_KEY="sk-..." \
  rogue-app \
  rogue-ai cli \
    --evaluated-agent-url http://my-agent:8080
```

---

## Troubleshooting

### TUI Not Rendering Properly

**Problem:** Colors, formatting, or layout broken in TUI

**Solution:** Ensure you use `-it` flags:
```bash
docker run -it --rm rogue-app  # ✅ Correct
docker run --rm rogue-app      # ❌ Missing -it
```

---

### Cannot Connect to Host Services

**Problem:** Docker container can't reach services on host machine

**Solution:** Use `host.docker.internal`:
```bash
# ✅ Correct
--evaluated-agent-url http://host.docker.internal:10001

# ❌ Won't work
--evaluated-agent-url http://localhost:10001
```

**Alternative:** Use host networking (Linux only):
```bash
docker run -it --rm --network host rogue-app
```

---

### Port Already in Use

**Problem:** `bind: address already in use`

**Solution:** Change the host port:
```bash
# Use port 9000 instead of 8000
docker run -it --rm -p 9000:8000 rogue-app
```

Or stop the conflicting service:
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Stop the process
kill <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

---

### Permission Denied on Volumes

**Problem:** Cannot write to mounted directories

**Solution 1 - Use named volumes (recommended):**
```bash
docker volume create rogue-data
docker run -v rogue-data:/app/.rogue rogue-app
```

**Solution 2 - Fix host directory permissions:**
```bash
# Linux/Mac
chmod -R 777 ./data
docker run -v $(pwd)/data:/app/.rogue rogue-app

# Or match user ID
docker run --user $(id -u):$(id -g) -v $(pwd)/data:/app/.rogue rogue-app
```

---

### Health Check Failing

**Problem:** `docker-compose` reports container unhealthy

**Check logs:**
```bash
docker-compose logs rogue-server
```

**Verify health endpoint:**
```bash
docker exec rogue-server curl http://localhost:8000/api/v1/health
```

**Common causes:**
- Server not starting (check API key is set)
- Port conflict
- Insufficient resources

---

### Container Exits Immediately

**Problem:** Container stops right after starting

**View logs:**
```bash
docker logs rogue-container
# or
docker-compose logs rogue-server
```

**Common causes:**
- Missing required environment variables (API keys)
- Command syntax error
- TUI started without `-it` flags

---

### Out of Memory

**Problem:** Container killed due to memory limits

**Solution:** Increase Docker memory limit (Docker Desktop → Settings → Resources)

Or set limits in docker-compose.yml:
```yaml
services:
  rogue-server:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

### Build Fails

**Problem:** `docker build` errors

**Try fresh build:**
```bash
docker build --no-cache -t rogue-app .
```

**Check disk space:**
```bash
docker system df
```

**Clean up:**
```bash
# Remove old images
docker image prune -a

# Remove build cache
docker builder prune -a
```

---

### Slow Performance

**Problem:** Container runs slowly

**Solutions:**
1. **Allocate more resources** (Docker Desktop → Settings → Resources)
2. **Use local SDK cache:**
   ```bash
   docker run -v ~/.cache:/root/.cache rogue-app
   ```
3. **Check Docker disk usage:**
   ```bash
   docker system df
   docker system prune
   ```

---

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Build image | `docker build -t rogue-app .` |
| Run default | `docker run -it --rm -p 8000:8000 rogue-app` |
| Run server | `docker run -d -p 8000:8000 rogue-app rogue-ai server --host 0.0.0.0` |
| Run Web UI | `docker run -d -p 7860:7860 -p 8000:8000 rogue-app rogue-ai ui` |
| Start compose | `docker-compose up -d` |
| View logs | `docker-compose logs -f` |
| Stop compose | `docker-compose down` |
| Rebuild | `docker-compose up -d --build` |

### Port Reference

| Service | Port | URL |
|---------|------|-----|
| Server | 8000 | http://localhost:8000/docs |
| Web UI | 7860 | http://localhost:7860 |
| Example Agent | 10001 | http://localhost:10001 |
