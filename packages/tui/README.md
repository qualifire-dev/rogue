# Rogue TUI

A modern terminal user interface for the Rogue Agent Evaluator, built with Go and Bubble Tea.

## Features

- **Interactive Dashboard**: Clean, centered interface with slash commands
- **Real-time Evaluation Monitoring**: Live progress updates via WebSocket
- **Interview Mode**: Direct chat interface with agents
- **Scenario Management**: Create and edit test scenarios
- **Configuration Management**: Persistent settings with TOML configuration
- **Keyboard Navigation**: Arrow keys, shortcuts, and slash commands
- **Mouse Support**: Click to navigate and interact
- **Themes**: Dark, light, and auto themes
- **Responsive Design**: Adapts to different terminal sizes

## Installation

```bash
cd packages/tui
go build -o bin/rogue ./cmd/rogue
```

## Usage

### Launch TUI (Default)

```bash
# Start interactive TUI
rogue

# Explicit TUI launch (same as above)
rogue tui
```

### CLI Commands

```bash
# CI/CD Commands
rogue ci --agent-url http://localhost:3000 --scenarios scenarios.json

# Evaluation Management
rogue eval list                         # List all evaluations
rogue eval show <eval-id>               # Show evaluation details
rogue eval cancel <eval-id>             # Cancel running evaluation

# Scenario Management
rogue scenarios list                    # List all scenarios
rogue scenarios generate                # Generate scenarios wizard
rogue scenarios edit <scenario-id>      # Edit scenario

# Interview Mode
rogue interview --agent-url http://localhost:3000

# Configuration
rogue config server                     # Set server URL
rogue config auth                       # Authentication setup

# Utility
rogue version                           # Show version
rogue help                              # Show help
```

### Global Flags

```bash
--server-url string     # Rogue server URL (default: http://localhost:8000)
--config string         # Config file path (default: ~/.rogue/config.toml)
--debug                 # Enable debug mode
--no-color             # Disable colors
--model string         # Default LLM model
--theme string         # UI theme (dark, light, auto)
```

## Configuration

Configuration is stored in `~/.rogue/config.toml`:

```toml
[server]
url = "http://localhost:8000"
timeout = "30s"

[auth]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
google_api_key = "..."

[defaults]
judge_llm = "openai/gpt-4o-mini"
deep_test_mode = false
theme = "auto"

[agent]
default_url = "http://localhost:3000"
default_auth_type = "no_auth"

[ui]
theme = "dark"
mouse_enabled = true
animations = true
```

## Slash Commands (In-TUI)

When in the TUI, type `/` followed by a command:

```bash
/new                    # Start new evaluation wizard
/eval                   # List evaluations
/interview              # Start interview mode
/configure              # Open configuration settings
/themes                 # Switch between themes
/models                 # List and select LLM models
/server                 # Configure server connection
/auth                   # Manage API keys and authentication
/help                   # Show help and commands
/quit                   # Exit application
/clear                  # Clear current screen
/refresh                # Refresh current view
/export                 # Export current data
/import                 # Import configuration or scenarios
```

## Keyboard Shortcuts

### Global Shortcuts

- `Ctrl+N` - New evaluation
- `Ctrl+E` - Evaluations list
- `Ctrl+I` - Interview mode
- `Ctrl+C` - Configuration
- `Ctrl+H` - Help
- `Ctrl+Q` - Quit application
- `Ctrl+R` - Refresh
- `Ctrl+L` - Clear screen

### Navigation

- `↑↓` - Navigate lists
- `←→` - Navigate forms
- `Tab` - Next field
- `Shift+Tab` - Previous field
- `Enter` - Select/Confirm
- `Esc` - Back/Cancel

### Function Keys

- `F1` - Help
- `F5` - Refresh

## Screens

### 1. Dashboard

- Central command hub
- Quick access to all features
- Command input with suggestions

### 2. Evaluations List

- View all evaluations with status
- Real-time progress updates
- Filter and search capabilities

### 3. Evaluation Detail

- Live chat transcript
- Progress indicators
- Control evaluation (pause, cancel, export)

### 4. New Evaluation Wizard

- Step-by-step evaluation setup
- Agent connection testing
- Scenario selection

### 5. Interview Mode

- Direct chat with agents
- Message history
- Session management

### 6. Configuration

- Server settings
- API key management
- Theme selection
- Default preferences

### 7. Scenarios

- Browse and edit scenarios
- Generate new scenarios
- Category management

## Architecture

The TUI is built with a clean, modular architecture:

```
cmd/rogue/              # CLI entry point
internal/
├── api/                # HTTP & WebSocket clients
├── commands/           # Slash command system
├── components/         # Reusable UI components
├── config/             # Configuration management
├── styles/             # Themes and styling
├── tui/                # Main TUI logic
└── util/               # Utility functions
```

## Development

### Building

```bash
go build -o bin/rogue ./cmd/rogue
```

### Testing

```bash
go test ./...
```

### Running in Development

```bash
go run ./cmd/rogue
```

### Adding New Commands

1. Add command definition in `internal/commands/commands.go`
2. Register in `registerBuiltinCommands()`
3. Handle in appropriate screen handlers

### Adding New Screens

1. Add screen constant in `internal/tui/model.go`
2. Add rendering logic in `internal/tui/view.go`
3. Add key handling in `internal/tui/update.go`

## Dependencies

- [Bubble Tea](https://github.com/charmbracelet/bubbletea) - Terminal UI framework
- [Lipgloss](https://github.com/charmbracelet/lipgloss) - Styling and layout
- [Cobra](https://github.com/spf13/cobra) - CLI framework
- [TOML](https://github.com/pelletier/go-toml/v2) - Configuration format
- [WebSocket](https://github.com/gorilla/websocket) - Real-time communication

## Contributing

1. Follow Go conventions and best practices
2. Add tests for new functionality
3. Update documentation
4. Ensure all lints pass

## License

See the root repository LICENSE.md file.
