# Rogue TUI Implementation Plan - Simple & Pragmatic Approach

## Overview

This document provides a **simple, maintainable** implementation plan for the Rogue Agent Evaluator TUI using Go and Bubble Tea. The focus is on building a working TUI that's easy to understand, debug, and maintain.

## Executive Summary

**Objective**: Build a simple Go TUI that provides an interactive interface for Rogue Agent Evaluator.

**Key Features**:

- Simple Bubble Tea implementation with direct screen switching
- Real-time evaluation monitoring via WebSocket
- Basic configuration with TOML
- Keyboard navigation (mouse optional)
- Clean styling with Lipgloss
- Direct HTTP client for server communication

**Timeline**: 4 weeks

**Philosophy**: Start simple, add complexity only when needed (YAGNI principle)

## Simplified Architecture

### Why Simple?

**Problems with Complex Architecture:**

- ❌ Event bus adds debugging complexity
- ❌ Version migration is premature for v1.0
- ❌ Plugin system is unnecessary
- ❌ Complex state management hides bugs

**Benefits of Simple Architecture:**

- ✅ Easy to understand and debug
- ✅ Fast to implement
- ✅ Low maintenance burden
- ✅ Clear execution flow

### Simple Architecture

```
packages/tui/
├── cmd/rogue/
│   └── main.go                         # Simple CLI entry point
├── internal/
│   ├── tui/
│   │   ├── model.go                    # Main TUI model (300 lines max)
│   │   ├── screens.go                  # All screens in one file
│   │   └── styles.go                   # Basic styling
│   ├── client/
│   │   ├── client.go                   # HTTP client wrapper
│   │   └── websocket.go                # Simple WebSocket handling
│   └── config/
│       └── config.go                   # Simple TOML config
├── go.mod                              # Go module
└── README.md                           # Documentation
```

**Total Files**: ~6 files instead of 30+
**Total Lines**: ~1000 lines instead of 5000+
**Complexity**: Simple, direct, debuggable

## Implementation Plan

### Week 1: Basic Structure & Navigation

#### Setup & Dependencies

```bash
cd packages/tui
go mod init github.com/qualifire-dev/rogue-private/packages/tui
go get github.com/charmbracelet/bubbletea@latest
go get github.com/charmbracelet/lipgloss@latest
go get github.com/pelletier/go-toml/v2@latest
go get github.com/gorilla/websocket@latest
```

#### `cmd/rogue/main.go` - Simple Entry Point

```go
package main

import (
	"fmt"
	"os"

	"github.com/charmbracelet/bubbletea"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/config"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/tui"
)

func main() {
	// Load config
	cfg, err := config.Load()
	if err != nil {
		fmt.Printf("Config error: %v\n", err)
		os.Exit(1)
	}

	// Create TUI
	model := tui.New(cfg)

	// Run TUI
	program := tea.NewProgram(model, tea.WithAltScreen())
	if _, err := program.Run(); err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}
}
```

#### `internal/config/config.go` - Simple Config

```go
package config

import (
	"os"
	"path/filepath"

	"github.com/pelletier/go-toml/v2"
)

type Config struct {
	ServerURL string `toml:"server_url"`
	Theme     string `toml:"theme"`
	Debug     bool   `toml:"debug"`
}

func Load() (*Config, error) {
	cfg := &Config{
		ServerURL: "http://localhost:8000",
		Theme:     "dark",
		Debug:     false,
	}

	// Try to load existing config
	home, _ := os.UserHomeDir()
	configPath := filepath.Join(home, ".rogue", "config.toml")

	if data, err := os.ReadFile(configPath); err == nil {
		toml.Unmarshal(data, cfg) // Ignore errors, use defaults
	}

	return cfg, nil
}

func (c *Config) Save() error {
	home, _ := os.UserHomeDir()
	configDir := filepath.Join(home, ".rogue")
	os.MkdirAll(configDir, 0755)

	configPath := filepath.Join(configDir, "config.toml")
	data, _ := toml.Marshal(c)
	return os.WriteFile(configPath, data, 0644)
}
```

#### `internal/tui/model.go` - Simple Main Model

```go
package tui

import (
	"github.com/charmbracelet/bubbletea"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/client"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/config"
)

type Screen int

const (
	ScreenDashboard Screen = iota
	ScreenEvaluations
	ScreenConfig
)

type Model struct {
	config        *config.Config
	client        *client.Client
	currentScreen Screen
	width         int
	height        int

	// Simple state
	selectedEvaluation string
	error             error
}

func New(cfg *config.Config) *Model {
	return &Model{
		config:        cfg,
		client:        client.New(cfg.ServerURL),
		currentScreen: ScreenDashboard,
	}
}

func (m *Model) Init() tea.Cmd {
	return m.client.Connect()
}

func (m *Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "1":
			m.currentScreen = ScreenDashboard
		case "2":
			m.currentScreen = ScreenEvaluations
		case "3":
			m.currentScreen = ScreenConfig
		}
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
	case error:
		m.error = msg
	}

	return m, nil
}

func (m *Model) View() string {
	if m.error != nil {
		return "Error: " + m.error.Error()
	}

	switch m.currentScreen {
	case ScreenDashboard:
		return m.dashboardView()
	case ScreenEvaluations:
		return m.evaluationsView()
	case ScreenConfig:
		return m.configView()
	default:
		return "Unknown screen"
	}
}
```

#### `internal/tui/screens.go` - All Screens in One File

```go
package tui

import (
	"fmt"
	"strings"
)

func (m *Model) dashboardView() string {
	title := "🏠 Rogue Agent Evaluator"
	menu := []string{
		"",
		"[1] 📊 Dashboard",
		"[2] 📋 Evaluations",
		"[3] ⚙️  Configuration",
		"",
		"[q] Quit",
		"",
	}

	content := []string{title}
	content = append(content, menu...)

	return strings.Join(content, "\n")
}

func (m *Model) evaluationsView() string {
	title := "📋 Evaluations"

	// Get evaluations from server
	evaluations, err := m.client.GetEvaluations()
	if err != nil {
		return fmt.Sprintf("%s\n\nError: %v\n\n[1] Back to Dashboard", title, err)
	}

	content := []string{title, ""}

	for i, eval := range evaluations {
		status := "⏳"
		if eval.Status == "completed" {
			status = "✅"
		} else if eval.Status == "failed" {
			status = "❌"
		}

		line := fmt.Sprintf("%s #%s %s", status, eval.ID, eval.Title)
		content = append(content, line)
	}

	content = append(content, "", "[1] Back to Dashboard")
	return strings.Join(content, "\n")
}

func (m *Model) configView() string {
	title := "⚙️ Configuration"

	content := []string{
		title,
		"",
		fmt.Sprintf("Server URL: %s", m.config.ServerURL),
		fmt.Sprintf("Theme: %s", m.config.Theme),
		fmt.Sprintf("Debug: %v", m.config.Debug),
		"",
		"[1] Back to Dashboard",
	}

	return strings.Join(content, "\n")
}
```

### Week 2: HTTP Client & Basic Styling

#### `internal/client/client.go` - Simple HTTP Client

```go
package client

import (
	"encoding/json"
	"fmt"
	"net/http"
)

type Client struct {
	baseURL string
	http    *http.Client
}

type Evaluation struct {
	ID     string `json:"id"`
	Title  string `json:"title"`
	Status string `json:"status"`
}

func New(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		http:    &http.Client{},
	}
}

func (c *Client) Connect() error {
	// Simple ping to check connection
	resp, err := c.http.Get(c.baseURL + "/api/v1/health")
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}

func (c *Client) GetEvaluations() ([]Evaluation, error) {
	resp, err := c.http.Get(c.baseURL + "/api/v1/evaluations")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var evaluations []Evaluation
	if err := json.NewDecoder(resp.Body).Decode(&evaluations); err != nil {
		return nil, err
	}

	return evaluations, nil
}
```

#### `internal/tui/styles.go` - Simple Styling

```go
package tui

import (
	"github.com/charmbracelet/lipgloss"
)

func (m *Model) applyStyles(content string) string {
	if m.config.Theme == "light" {
		return lipgloss.NewStyle().
			Foreground(lipgloss.Color("#000000")).
			Background(lipgloss.Color("#FFFFFF")).
			Render(content)
	}

	return lipgloss.NewStyle().
		Foreground(lipgloss.Color("#FFFFFF")).
		Background(lipgloss.Color("#000000")).
		Render(content)
}
```

### Week 3: WebSocket & Real-time Updates

#### `internal/client/websocket.go` - Simple WebSocket

```go
package client

import (
	"encoding/json"
	"log"

	"github.com/charmbracelet/bubbletea"
	"github.com/gorilla/websocket"
)

type WSMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

func (c *Client) ConnectWebSocket() tea.Cmd {
	return func() tea.Msg {
		conn, _, err := websocket.DefaultDialer.Dial(
			"ws://localhost:8000/ws", nil)
		if err != nil {
			return err
		}

		go c.listenWebSocket(conn)
		return WSConnectedMsg{}
	}
}

func (c *Client) listenWebSocket(conn *websocket.Conn) {
	for {
		var msg WSMessage
		if err := conn.ReadJSON(&msg); err != nil {
			log.Printf("WebSocket error: %v", err)
			return
		}

		// Send message to TUI
		tea.Send(msg)
	}
}

type WSConnectedMsg struct{}
```

### Week 4: Polish & Testing

#### Simple Testing

```go
// internal/tui/model_test.go
package tui

import (
	"testing"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/config"
)

func TestBasicNavigation(t *testing.T) {
	cfg := &config.Config{ServerURL: "http://localhost:8000"}
	model := New(cfg)

	// Test initial state
	if model.currentScreen != ScreenDashboard {
		t.Error("Expected dashboard screen")
	}
}
```

#### Simple Makefile

```makefile
.PHONY: build test run

build:
	go build -o bin/rogue ./cmd/rogue

test:
	go test ./...

run: build
	./bin/rogue

dev:
	go run ./cmd/rogue
```

## Key Benefits of This Simple Approach

### ✅ **Maintainability**

- Only 6 files to understand
- Clear, direct code flow
- Easy to debug with standard Go debugging tools
- No hidden abstractions or magic

### ✅ **Development Speed**

- Fast to implement (1 week per major feature)
- Easy to add new screens (just add to screens.go)
- Simple testing (standard Go unit tests)
- No complex build setup required

### ✅ **User Experience**

- Fast startup (no initialization overhead)
- Responsive UI (direct state updates)
- Clear navigation (numbered options)
- Error messages are visible and actionable

## Implementation Timeline

| Week | Focus                  | Deliverable                          | Complexity |
| ---- | ---------------------- | ------------------------------------ | ---------- |
| 1    | Structure & Navigation | Working TUI with 3 screens           | Low        |
| 2    | HTTP Client & Styling  | Data from server, basic themes       | Low        |
| 3    | WebSocket & Real-time  | Live updates, progress monitoring    | Medium     |
| 4    | Polish & Testing       | Error handling, tests, documentation | Low        |

## What We're NOT Building (And Why)

### ❌ **Complex Architecture**

- **Event bus**: Direct function calls are easier to debug
- **Plugin system**: YAGNI - add when needed
- **Complex state management**: Simple struct fields work fine
- **Version migration**: Let users recreate config if needed

### ❌ **Advanced Features**

- **Slash commands**: Numbered navigation is simpler
- **Auto-completion**: Add later if users request it
- **Complex layouts**: Single-column layout works
- **Advanced styling**: Basic themes are sufficient

## Success Criteria

### ✅ **Week 1 Goals**

- [ ] TUI starts and shows dashboard
- [ ] Can navigate between screens with numbers
- [ ] Configuration loads from file
- [ ] Basic styling works

### ✅ **Week 2 Goals**

- [ ] Connects to Rogue server
- [ ] Shows list of evaluations
- [ ] Basic error handling
- [ ] Theme switching works

### ✅ **Week 3 Goals**

- [ ] Real-time updates via WebSocket
- [ ] Progress monitoring for running evaluations
- [ ] Handle connection failures gracefully

### ✅ **Week 4 Goals**

- [ ] Unit tests for core functions
- [ ] Error recovery and user feedback
- [ ] Documentation and examples
- [ ] Cross-platform builds

## After V1: What to Add Next

### **Only Add If Users Request:**

1. **More screens** (interview mode, detailed views)
2. **Better navigation** (slash commands, vim keys)
3. **Advanced features** (search, filtering, export)
4. **Performance optimizations** (caching, pagination)

### **Keep It Simple:**

- Add one feature at a time
- Get user feedback before adding complexity
- Maintain the 6-file limit as long as possible
- Refactor only when the simple approach breaks

## Bottom Line

**This approach prioritizes:**

- ✅ Working software over comprehensive documentation
- ✅ Simple solutions over complex architectures
- ✅ Direct code over abstract patterns
- ✅ Fast iteration over perfect design

**The result:** A maintainable, debuggable TUI that actually gets built and shipped.
