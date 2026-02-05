# Makefile for Rogue TUI

.PHONY: build clean run test install deps dev dev-tmux stop-tmux

# Variables
BINARY_NAME=rogue-tui
TUI_DIR=packages/tui
BUILD_DIR?=$(TUI_DIR)/dist
CMD_DIR=$(TUI_DIR)/cmd/rogue
VERSION?=$(shell cat VERSION 2>/dev/null || echo "dev")
COMMIT?=$(shell git rev-parse --short HEAD)
DATE?=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build flags
LDFLAGS=-ldflags "-X github.com/rogue/tui/internal/shared.Version=v$(VERSION) -X main.commit=$(COMMIT) -X main.date=$(DATE)"

# Default target
all: build

# Install dependencies
deps:
	cd $(TUI_DIR) && go mod download && go mod tidy

# Build the binary
build: deps
	mkdir -p $(BUILD_DIR)
	cd $(TUI_DIR) && CGO_ENABLED=0 go build $(LDFLAGS) -o $(CURDIR)/$(BUILD_DIR)/$(BINARY_NAME) ./cmd/rogue

# Build for multiple platforms
build-all: deps
	mkdir -p $(BUILD_DIR)
	# Linux
	cd $(TUI_DIR) && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o $(CURDIR)/$(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 ./cmd/rogue
	cd $(TUI_DIR) && CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o $(CURDIR)/$(BUILD_DIR)/$(BINARY_NAME)-linux-arm64 ./cmd/rogue
	# macOS
	cd $(TUI_DIR) && CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o $(CURDIR)/$(BUILD_DIR)/$(BINARY_NAME)-darwin-amd64 ./cmd/rogue
	cd $(TUI_DIR) && CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o $(CURDIR)/$(BUILD_DIR)/$(BINARY_NAME)-darwin-arm64 ./cmd/rogue
	# Windows
	cd $(TUI_DIR) && CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o $(CURDIR)/$(BUILD_DIR)/$(BINARY_NAME)-windows-amd64.exe ./cmd/rogue

# Run the application
run: build
	./$(BUILD_DIR)/$(BINARY_NAME)

# Run in development mode
dev: deps
	cd $(TUI_DIR) && CGO_ENABLED=0 go run $(LDFLAGS) ./cmd/rogue

# Run tests
test:
	cd $(TUI_DIR) && go test -v ./...

# Run tests with coverage
test-coverage:
	cd $(TUI_DIR) && go test -v -coverprofile=coverage.out ./... && go tool cover -html=coverage.out -o coverage.html

# Install the binary to GOPATH/bin
install: deps
	cd $(TUI_DIR) && go install $(LDFLAGS) ./cmd/rogue

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)
	rm -f $(TUI_DIR)/coverage.out $(TUI_DIR)/coverage.html

# Format code
fmt:
	cd $(TUI_DIR) && go fmt ./...

# Lint code
lint:
	cd $(TUI_DIR) && golangci-lint run

# Vet code
vet:
	cd $(TUI_DIR) && go vet ./...

# Check for security issues
security:
	cd $(TUI_DIR) && gosec ./...

# Run all checks
check: fmt vet lint test

# Development setup
setup:
	cd $(TUI_DIR) && go mod download
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest

# Start dev environment in tmux with server, TUI, and example agents
dev-tmux:
	@./scripts/dev-tmux.sh

# Stop dev tmux session
stop-tmux:
	@tmux kill-session -t rogue 2>/dev/null && echo "Stopped rogue tmux session" || echo "No rogue tmux session found"

# Help
help:
	@echo "Available targets:"
	@echo "  build        - Build the binary"
	@echo "  build-all    - Build for multiple platforms"
	@echo "  run          - Build and run the application"
	@echo "  dev          - Run in development mode"
	@echo "  test         - Run tests"
	@echo "  test-coverage- Run tests with coverage"
	@echo "  install      - Install binary to GOPATH/bin"
	@echo "  clean        - Clean build artifacts"
	@echo "  fmt          - Format code"
	@echo "  lint         - Lint code"
	@echo "  vet          - Vet code"
	@echo "  security     - Check for security issues"
	@echo "  check        - Run all checks"
	@echo "  setup        - Setup development environment"
	@echo "  dev-tmux     - Start tmux session with server, TUI, and example agents"
	@echo "  stop-tmux    - Kill the rogue tmux session"
	@echo "  deps         - Download dependencies"
	@echo "  help         - Show this help"
