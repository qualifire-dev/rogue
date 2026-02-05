# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Rogue TUI — a Go terminal UI for the Rogue Agent Evaluator. Built with Bubble Tea (v2), Lipgloss, and Cobra. Module path: `github.com/rogue/tui`.

## Commands

```bash
make build          # Build binary (CGO_ENABLED=0), output in bin/
make run            # Build and run
make dev            # Run in development mode
make test           # Run all tests
make test-coverage  # Tests with coverage report
make fmt            # Format code
make lint           # Run golangci-lint
make vet            # Run go vet
make security       # Run gosec
make check          # Run all checks (fmt, vet, lint, test)
make setup          # Install dev dependencies (golangci-lint, gosec)
```

Run a single test: `go test ./internal/screens/redteam/... -run TestName`

Version is injected via ldflags: `-X github.com/rogue/tui/internal/shared.Version=v$(VERSION)`

## Architecture

**Entry flow**: `cmd/rogue/main.go` (Cobra CLI) → `internal/commands/commands.go` (`RunTUI()`) → `internal/tui/app.go` (`NewApp()` → `app.Run()`)

**`internal/tui/`** — Core application:
- `types.go` — Main `Model` struct holding all application state (current screen, evaluations, scenarios, config, UI state)
- `keyboard_controller.go` — Global keyboard routing with screen-specific delegation
- `common_controller.go` — Shared evaluation logic, WebSocket event streaming, summary generation
- `form_controller.go` / `detail_controller.go` — Evaluation form and detail view logic
- `eval_types.go` — Evaluation modes (Policy, Red Team), protocols (A2A, MCP, Python), transports (HTTP, SSE, Streamable HTTP)

**`internal/screens/`** — Each screen is a Bubble Tea component with its own view/controller:
- `dashboard/` — Home screen with command input
- `evaluations/` — Create (form) and view (detail) evaluations
- `report/` — Evaluation summary with markdown rendering (Glamour)
- `config/` — App settings and API keys
- `scenarios/` — Test scenario management
- `interview/` — Interactive agent testing
- `redteam/` — Red team config (vulnerability/attack catalog, scan presets, auto-persists to `.rogue/redteam.yaml`)
- `redteam_report/` — Red team results display

**`internal/components/`** — Reusable UI widgets: spinner, command_line (with autocomplete), dialog, textarea, viewport, chat_view, logo.

**`internal/theme/`** — Theme system with 22 built-in themes (JSON files in `themes/`). Uses Radix color scale. `manager.go` handles registration/switching, `loader.go` reads JSON themes. Themes define 70+ color methods.

**`internal/styles/`** — Lipgloss style utilities, custom Style wrapper with "none" color support.

## State and Communication

- Bubble Tea message-driven architecture: screens communicate via typed messages (`AutoRefreshMsg`, `StartEvaluationMsg`, `SummaryGeneratedMsg`, etc.)
- WebSocket connection to Rogue server (default `http://localhost:8000`) for streaming evaluation events
- Configuration persisted in `.rogue/` directory (searched upward from CWD): `user_config.json`, `scenarios.json`, `redteam.yaml`, `rogue.log`

## Key Patterns

- All screens follow view/controller separation within their package
- Keyboard input flows: global shortcuts → active dialog/overlay → current screen handler
- Red team config auto-saves selections to `.rogue/redteam.yaml` on every change
- Evaluation events consumed via goroutine into state, triggering UI refresh
