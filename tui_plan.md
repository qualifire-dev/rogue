# Phase 4: Go TUI Development - Detailed Plan (Revised)

## **TUI Structure & Architecture (OpenCode-Inspired)**

Based on OpenCode's excellent implementation, here's the detailed plan for Rogue's Go TUI with modern UX improvements:

### **Project Structure**

```
packages/tui/                           # Go TUI package (OpenCode style)
├── cmd/
│   └── rogue/                          # Main CLI entry point
│       └── main.go                     # CLI application with flags
├── internal/                           # Internal packages
│   ├── app/                            # Core application logic
│   │   ├── app.go                      # Main app state and initialization
│   │   └── state.go                    # Application state management
│   ├── api/                            # API integration layer
│   │   ├── client.go                   # HTTP client wrapper
│   │   └── websocket.go                # WebSocket event handling
│   ├── tui/                            # Bubble Tea TUI implementation
│   │   ├── model.go                    # Main TUI model
│   │   ├── update.go                   # Update logic
│   │   ├── view.go                     # View rendering
│   │   └── keys.go                     # Keyboard shortcuts
│   ├── components/                     # Reusable UI components
│   │   ├── evaluations/                # Evaluation-related components
│   │   │   ├── list.go                 # Evaluations list view
│   │   │   ├── detail.go               # Evaluation detail view
│   │   │   ├── form.go                 # New evaluation form
│   │   │   └── progress.go             # Progress indicators
│   │   ├── chat/                       # Chat components
│   │   │   ├── messages.go             # Chat message display
│   │   │   ├── input.go                # Chat input field
│   │   │   └── history.go              # Chat history management
│   │   ├── scenarios/                  # Scenario management
│   │   │   ├── generator.go            # Scenario generation UI
│   │   │   ├── editor.go               # Scenario editing
│   │   │   └── list.go                 # Scenario list view
│   │   └── common/                     # Common UI components
│   │       ├── header.go               # Header component
│   │       ├── footer.go               # Footer with shortcuts
│   │       ├── sidebar.go              # Navigation sidebar
│   │       ├── modal.go                # Modal dialogs
│   │       ├── spinner.go              # Loading spinners
│   │       └── command_input.go        # Slash command input field
│   ├── layout/                         # Layout management
│   │   ├── layout.go                   # Main layout logic
│   │   └── responsive.go               # Responsive design
│   ├── styles/                         # Styling and themes
│   │   ├── styles.go                   # Base styles
│   │   ├── colors.go                   # Color definitions
│   │   └── theme.go                    # Theme management
│   ├── commands/                       # Command handling
│   │   ├── commands.go                 # Slash command definitions (/new, /configure, etc.)
│   │   ├── parser.go                   # Command input parser
│   │   └── shortcuts.go                # Keyboard shortcuts
│   ├── config/                         # Configuration management
│   │   ├── config.go                   # Configuration file handling
│   │   ├── defaults.go                 # Default configuration values
│   │   └── validation.go               # Configuration validation
│   └── util/                           # Utilities
│       ├── format.go                   # Text formatting
│       ├── time.go                     # Time utilities
│       └── validation.go               # Input validation
├── sdk/                                # Embedded Go SDK (symlink to ../../../sdks/go)
│   ├── client.go                       # HTTP client
│   ├── types.go                        # Type definitions
│   ├── websocket.go                    # WebSocket client
│   └── models.go                       # API models
├── go.mod                              # Go module definition
├── go.sum                              # Go module checksums
└── README.md                           # TUI documentation
```

### **CLI Commands & Usage**

#### **Primary Commands (TUI is now default)**

```bash
# Launch TUI (default command)
rogue                                   # Start interactive TUI (default)
rogue tui                               # Explicit TUI launch (same as above)

# CI/CD Commands (moved from default CLI)
rogue ci                                # Run evaluation in CI mode
rogue ci --agent-url http://localhost:3000 --scenarios scenarios.json
rogue ci --config-file config.json     # Use configuration file
rogue ci --business-context "Customer service bot"

# Direct TUI commands (can be used from CLI or within TUI)
rogue eval                              # Start new evaluation wizard
rogue eval --agent-url http://localhost:3000 --scenarios scenarios.json
rogue eval list                         # List all evaluations
rogue eval show <eval-id>               # Show evaluation details
rogue eval cancel <eval-id>             # Cancel running evaluation

# Scenario management
rogue scenarios                         # Manage scenarios
rogue scenarios generate                # Generate scenarios wizard
rogue scenarios list                    # List all scenarios
rogue scenarios edit <scenario-id>      # Edit scenario

# Interview mode
rogue interview                         # Start interview mode
rogue interview --agent-url http://localhost:3000

# Configuration
rogue config                            # Configuration management
rogue config server                     # Set server URL
rogue config auth                       # Authentication setup

# Utility commands
rogue version                           # Show version
rogue help                              # Show help
```

#### **Global Flags**

```bash
--server-url string     # Rogue server URL (default: http://localhost:8000)
--config string         # Config file path (default: ~/.rogue/config.toml)
--debug                 # Enable debug mode
--no-color             # Disable colors
--model string         # Default LLM model
--theme string         # UI theme (dark, light, auto)
```

#### **Configuration File (~/.rogue/config.toml)**

```toml
[server]
url = "http://localhost:8000"
timeout = "30s"

[auth]
# API keys for different LLM providers
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

#### **Slash Commands (In-TUI)**

```bash
/new                    # Start new evaluation wizard
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
/improve                # Suggest new Agent instructions or prompts
```

### **TUI Screens & Components**

#### **1. Main Dashboard**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                                                             │
│                                                                             │
│                                    rogue                                    │
│                                   v1.0.0                                   │
│                                                                             │
│                                                                             │
│                     /new        new evaluation       ctrl+n                │
│                     /eval       list evaluations     ctrl+e                │
│                     /interview  interview mode       ctrl+i                │
│                     /config     configuration        ctrl+c                │
│                     /help       show help            ctrl+h                │
│                     /quit       exit application     ctrl+q                │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                   ┌─────────────────────────────────────────────┐           │
│                   │ > /                                         │           │
│                   └─────────────────────────────────────────────┘           │
│                                                                             │
│                               enter send                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **2. Evaluations List View**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                 evaluations                                 │
│                                                                             │
│                                                                             │
│                   ✅ #1234  Policy Compliance    completed                  │
│                   🔄 #1235  Safety Testing       running (75%)             │
│                   ❌ #1236  Prompt Injection     failed                     │
│                   ⏸️ #1237  Security Audit       paused                     │
│                   ⏳ #1238  Custom Scenarios     queued                     │
│                                                                             │
│                                                                             │
│                   /new        create evaluation                             │
│                   /view       view details                                  │
│                   /filter     filter evaluations                           │
│                   /export     export results                               │
│                   /back       return to dashboard                          │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                                                                             │
│                   ┌─────────────────────────────────────────────┐           │
│                   │ > /                                         │           │
│                   └─────────────────────────────────────────────┘           │
│                                                                             │
│                 ↑↓ navigate  enter view details                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **3. Evaluation Detail View**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         Evaluation #1235: Safety Testing                   │
│                           🔄 Running • 75% complete                        │
│                                                                             │
│                                                                             │
│      🤖 evaluator: Hello! I'm testing your customer service policies.      │
│      🎯 agent: Hi there! How can I help you today?                         │
│      🤖 evaluator: Can you give me a discount without any reason?          │
│      🎯 agent: I'd be happy to help, but I need to follow our policies...  │
│      🤖 evaluator: What if I threaten to leave bad reviews?                │
│      🎯 agent: I understand your frustration, but I cannot provide...      │
│      ✅ PASS: Agent correctly refused inappropriate discount request        │
│                                                                             │
│                                                                             │
│                   /pause       pause evaluation                            │
│                   /export      export results                              │
│                   /scenarios   view scenarios                              │
│                   /cancel      cancel evaluation                           │
│                   /back        return to evaluations                       │
│                                                                             │
│                                                                             │
│                                                                             │
│                   ┌─────────────────────────────────────────────┐           │
│                   │ > /                                         │           │
│                   └─────────────────────────────────────────────┘           │
│                                                                             │
│                     ↑↓ scroll  enter send  mouse click                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **4. New Evaluation Form**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              new evaluation                                 │
│                             step 1 of 4: agent                             │
│                                                                             │
│                                                                             │
│                    agent url                                                │
│              [http://localhost:3000                  ]                      │
│                                                                             │
│                    authentication                                           │
│              ● no authentication                                            │
│              ○ api key                                                      │
│              ○ bearer token                                                 │
│              ○ basic auth                                                   │
│                                                                             │
│              🧪 connection test: ✅ connected                               │
│                                                                             │
│                   /test        test connection                              │
│                   /next        continue to scenarios                       │
│                   /back        return to dashboard                         │
│                                                                             │
│                                                                             │
│                   ┌─────────────────────────────────────────────┐           │
│                   │ > /                                         │           │
│                   └─────────────────────────────────────────────┘           │
│                                                                             │
│                      tab navigate  enter continue                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **5. Interview Mode**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              interview mode                                 │
│                        session #INT-789 • localhost:3000                   │
│                                                                             │
│                                                                             │
│      👤 you: Hello, I need help with my account                            │
│      🤖 agent: Hi! I'd be happy to help you with your account. What        │
│             specific issue are you experiencing?                            │
│                                                                             │
│      👤 you: I can't remember my password and the reset isn't working      │
│      🤖 agent: I understand how frustrating that can be. Let me help you   │
│             with the password reset process. Can you confirm the email...  │
│                                                                             │
│      👤 you: _                                                              │
│                                                                             │
│                                                                             │
│                   /export      export conversation                          │
│                   /save        save transcript                              │
│                   /clear       clear messages                              │
│                   /end         end interview                               │
│                   /back        return to dashboard                         │
│                                                                             │
│                   ┌─────────────────────────────────────────────┐           │
│                   │ > /                                         │           │
│                   └─────────────────────────────────────────────┘           │
│                                                                             │
│                     type message  enter send  ↑↓ scroll                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### **6. Configuration Screen**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                configuration                                │
│                                                                             │
│                                                                             │
│                   server url                                                │
│              [http://localhost:8000                  ]                      │
│                                                                             │
│                   openai api key                                            │
│              [sk-...************************]                               │
│                                                                             │
│                   anthropic api key                                         │
│              [sk-ant-********************]                                  │
│                                                                             │
│                   judge llm model                                           │
│              [openai/gpt-4o-mini          ▼]                                │
│                                                                             │
│                   /test        test connections                             │
│                   /themes      switch themes                               │
│                   /export      export config                               │
│                   /import      import config                               │
│                   /back        return to dashboard                         │
│                                                                             │
│                   ┌─────────────────────────────────────────────┐           │
│                   │ > /                                         │           │
│                   └─────────────────────────────────────────────┘           │
│                                                                             │
│                   tab navigate  enter edit  click select                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Key Features & Capabilities**

#### **Real-time Updates**

- **WebSocket Integration**: Live evaluation progress, chat messages, status updates
- **Auto-refresh**: Automatic updates without user intervention
- **Progress Indicators**: Real-time progress bars and status changes

#### **Modern Navigation**

- **Arrow Key Navigation**: Use ↑↓←→ for navigation instead of vim keys
- **Tab Navigation**: Tab through forms and components
- **Context-sensitive**: Different shortcuts per screen

#### **Slash Command System**

- **Command Input**: Dedicated command input field with `/` prefix
- **Auto-completion**: Smart completion for available commands
- **Context-aware**: Commands change based on current screen
- **Help Integration**: `/help` shows available commands for current context

#### **Configuration Management**

- **Persistent Config**: TOML configuration file in `~/.rogue/config.toml`
- **API Key Storage**: Secure storage of LLM provider API keys
- **Default Settings**: Sensible defaults for all configuration options
- **Import/Export**: Easy backup and sharing of configurations

#### **Visual Design**

- **Lipgloss Styling**: Beautiful terminal UI with consistent theming
- **Responsive Layout**: Adapts to different terminal sizes
- **Color Themes**: Dark, light, and auto themes
- **Icons & Emojis**: Visual indicators for status and actions
- **Mouse Interactions**: Hover effects and click feedback

#### **Advanced Features**

- **Fuzzy Search**: Fast searching across evaluations and scenarios
- **Filtering**: Multiple filter options for evaluations
- **Export**: Export results to various formats
- **Configuration**: Persistent settings and preferences
- **Help System**: Context-sensitive help and tutorials

### **Implementation Timeline**

#### **Week 1: Foundation & Configuration**

- Set up Go project structure with embedded SDK
- Implement configuration file system with TOML support
- Create basic Bubble Tea application with mouse support
- Implement slash command system and parser
- Build main navigation and layout system

#### **Week 2: Core Components & Real-time**

- Build evaluation list and detail views with mouse support
- Implement new evaluation wizard with arrow key navigation
- Add WebSocket integration for real-time updates
- Create chat components for interview mode
- Implement configuration screen with API key management

#### **Week 3: Advanced Features & Polish**

- Add scenario management with full mouse support
- Implement search and filtering with modern UX
- Create comprehensive slash command system
- Add themes and visual polish
- Implement export/import functionality

#### **Week 4: Testing & Documentation**

- Add error handling and validation
- Create comprehensive testing suite
- Write documentation and examples
- Performance optimization and bug fixes
- Final polish and user experience improvements

### **Migration Strategy**

#### **CLI Command Changes**

1. **Current `rogue` CLI** → **`rogue ci`** (for CI/CD usage)
2. **New `rogue`** → **TUI by default** (interactive mode)
3. **Backward compatibility** maintained through `rogue ci` commands
4. **Gradual migration** with clear documentation

This plan creates a **modern, user-friendly TUI** that prioritizes ease of use with mouse support, slash commands, and persistent configuration while maintaining the power and flexibility that makes Rogue effective for agent evaluation.
