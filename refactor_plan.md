# Rogue Agent Evaluator - Server-Client Architecture Refactor Plan

## Overview

This document outlines the comprehensive plan to refactor the Rogue Agent Evaluator from a monolithic architecture to a server-client architecture with multiple frontend options including CLI, Gradio UI, Go TUI, and pytest plugin.

**Inspiration**: This refactor draws heavily from [OpenCode's architecture](https://github.com/sst/opencode), which successfully implements a similar client-server pattern with multiple frontends and language-specific SDKs.

## Current Architecture Analysis

### Existing Components
- **Monolithic Structure**: All components tightly coupled in single `rogue/` package
- **Direct Integration**: CLI and UI directly invoke evaluation logic
- **ADK Agent**: Embedded within the application flow
- **Limited Frontend Options**: Only CLI and Gradio UI available

### Pain Points
- Difficult to add new frontend types
- Tight coupling between UI and evaluation logic
- No API for third-party integrations
- Limited scalability for concurrent evaluations

## Target Architecture (OpenCode-Inspired)

### High-Level Design
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontends     │    │   Rogue Server  │    │   ADK Agent     │
│                 │    │                 │    │                 │
│ • CLI (Python)  │    │ • HTTP API      │    │ • Evaluation    │
│ • Gradio UI     │◄──►│ • WebSocket     │◄──►│   Logic         │
│ • TUI (Go)      │    │ • Process Mgmt  │    │ • Policy Check  │
│ • Pytest Plugin│    │ • Session Mgmt  │    │ • ADK Framework │
│ • VSCode Ext    │    │ • Bus System    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Packages      │    │   Data Models   │
│                 │    │                 │
│ • Python SDK    │    │ • Scenarios     │
│ • TypeScript SDK│    │ • Results       │
│ • Go SDK        │    │ • Configuration │
│ • Function Pkg  │    │ • Chat History  │
└─────────────────┘    └─────────────────┘
```

## New Folder Structure (OpenCode-Inspired with FastAPI)

```
qualifire-agent-evaluator-1/
├── rogue/                             # Core Python server package
│   ├── server/                        # FastAPI server
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── evaluations.py
│   │   │   ├── scenarios.py
│   │   │   └── config.py
│   │   ├── core/                      # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py        # Evaluation orchestration
│   │   │   ├── session_manager.py     # Session management
│   │   │   ├── agent_invoker.py       # ADK agent process management
│   │   │   └── websocket_manager.py   # WebSocket handling
│   │   └── middleware/                # FastAPI middleware
│   │       ├── __init__.py
│   │       ├── cors.py
│   │       └── auth.py
│   ├── evaluator_agent/               # ADK agent (existing)
│   │   ├── __init__.py
│   │   ├── evaluator_agent.py
│   │   ├── run_evaluator_agent.py
│   │   └── policy_evaluation.py
│   ├── models/                        # Pydantic models
│   ├── services/                      # Business services
│   ├── common/                        # Shared utilities
│   └── tests/                         # Server tests
├── packages/                          # Frontend packages (OpenCode style)
│   ├── sdk/                           # TypeScript/JavaScript SDK
│   │   ├── src/
│   │   │   ├── client.ts              # Main SDK client
│   │   │   ├── types.ts               # Type definitions
│   │   │   └── websocket.ts           # WebSocket client
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── tui/                           # Go TUI package
│   │   ├── cmd/                       # CLI commands
│   │   ├── internal/                  # Internal packages
│   │   ├── sdk/                       # Go SDK (embedded)
│   │   ├── input/                     # Input handling
│   │   ├── go.mod
│   │   └── go.sum
│   └── web/                           # Future web UI
│       ├── src/
│       └── package.json
├── sdks/                              # External SDKs
│   ├── python/                        # Python SDK
│   │   ├── rogue_sdk/
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── vscode/                        # VSCode extension
│   │   ├── src/
│   │   ├── package.json
│   │   └── README.md
│   └── rust/                          # Future Rust SDK
├── cli/                               # Standalone CLI application
├── gradio-ui/                         # Standalone Gradio UI
├── pytest-plugin/                    # Pytest integration
├── examples/                          # Usage examples
├── scripts/                           # Build/deployment scripts
├── .github/                           # CI/CD workflows
├── pyproject.toml                     # Python dependencies for server
├── package.json                       # Frontend package management
├── uv.lock                            # Python lock file
└── README.md
```

## Implementation Phases

### Phase 1: Core Server Infrastructure (Weeks 1-2)

#### 1.1 Hybrid Monorepo Setup
- [ ] Set up root `package.json` for frontend packages workspace
- [ ] Keep `pyproject.toml` for Python server dependencies
- [ ] Create `packages/` directory for TypeScript/Go components
- [ ] Set up shared TypeScript configuration for frontend packages

#### 1.2 FastAPI Server Package
- [ ] Restructure existing `rogue/` as FastAPI server package
- [ ] Implement FastAPI application in `rogue/server/main.py`
- [ ] Set up basic middleware (CORS, auth, logging)
- [ ] Create health check and status endpoints
- [ ] Add WebSocket support for real-time updates

#### 1.2 API Endpoints Design
- [ ] **Evaluation Management**
  - `POST /api/v1/evaluations` - Start new evaluation
  - `GET /api/v1/evaluations/{id}` - Get evaluation status
  - `DELETE /api/v1/evaluations/{id}` - Cancel evaluation
  - `GET /api/v1/evaluations/{id}/results` - Get results
  - `GET /api/v1/evaluations/{id}/report` - Get report

- [ ] **Scenario Management**
  - `GET /api/v1/scenarios` - List scenarios
  - `POST /api/v1/scenarios` - Create/upload scenarios
  - `GET /api/v1/scenarios/{id}` - Get specific scenario
  - `PUT /api/v1/scenarios/{id}` - Update scenario
  - `DELETE /api/v1/scenarios/{id}` - Delete scenario

- [ ] **Configuration**
  - `GET /api/v1/config` - Get server config
  - `POST /api/v1/config/validate` - Validate configuration
  - `GET /api/v1/agents/{url}/info` - Get agent info

#### 1.3 ADK Agent Integration
- [ ] Create `rogue/server/core/agent_invoker.py` for agent orchestration
- [ ] Implement process management for Python ADK agents
- [ ] Design communication protocol (CLI args, file I/O, stdout/stderr)
- [ ] Update existing `rogue/evaluator_agent/run_evaluator_agent.py` for server integration
- [ ] Add progress callback mechanism via HTTP/WebSocket

#### 1.4 WebSocket Support
- [ ] Implement WebSocket manager in `rogue/server/core/websocket_manager.py`
- [ ] Add real-time evaluation updates using FastAPI WebSocket
- [ ] Create chat message streaming
- [ ] Handle client connection management

#### 1.5 Session Management
- [ ] Create `rogue/server/core/session_manager.py`
- [ ] Implement evaluation session tracking
- [ ] Add concurrent evaluation support
- [ ] Create session cleanup mechanisms

### Phase 2: SDK Development (Week 3)

#### 2.1 TypeScript SDK (Primary SDK)
- [ ] Create `packages/sdk/` with TypeScript implementation
- [ ] Implement main `RogueClient` class with proper typing
- [ ] Add WebSocket client for real-time updates
- [ ] Create comprehensive type definitions
- [ ] Follow OpenCode's SDK patterns and structure

#### 2.2 Python SDK (External)
- [ ] Create `sdks/python/rogue_sdk/` package structure
- [ ] Implement main `RogueClient` class
- [ ] Add async client with WebSocket support
- [ ] Create request/response models using Pydantic

#### 2.2 SDK Features
- [ ] HTTP client for REST API calls
- [ ] WebSocket client for real-time updates
- [ ] Error handling and retry logic
- [ ] Authentication support
- [ ] Comprehensive logging

#### 2.3 SDK Testing & Documentation
- [ ] Unit tests for all SDK functionality
- [ ] Integration tests with server
- [ ] API documentation with examples
- [ ] Usage examples and tutorials

### Phase 3: Frontend Migration (Weeks 4-5)

#### 3.1 CLI Refactor
- [ ] Create `cli/` directory structure
- [ ] Refactor existing CLI to use Python SDK
- [ ] Implement Click-based command structure
- [ ] Add real-time progress display
- [ ] Maintain backward compatibility

#### 3.2 Gradio UI Refactor
- [ ] Create `gradio-ui/` directory structure
- [ ] Refactor existing Gradio UI to use Python SDK
- [ ] Update all components to use SDK
- [ ] Add WebSocket integration for real-time updates
- [ ] Maintain existing UI/UX

#### 3.3 Legacy Support
- [ ] Keep existing `rogue/run_cli.py` and `rogue/run_ui.py` working
- [ ] Add deprecation warnings
- [ ] Create migration guide for users

### Phase 4: Go TUI Development (Weeks 6-7)

#### 4.1 Go SDK Implementation
- [ ] Create `sdks/go/` package structure
- [ ] Implement HTTP client for Rogue API
- [ ] Add WebSocket client for real-time updates
- [ ] Create Go structs for API models
- [ ] Add comprehensive error handling

#### 4.2 Bubble Tea TUI (OpenCode Style)
- [ ] Set up Go project in `packages/tui/` directory (following OpenCode structure)
- [ ] Create embedded Go SDK in `packages/tui/sdk/`
- [ ] Design TUI screens and navigation using Bubble Tea
- [ ] Implement core components:
  - [ ] Evaluations list view
  - [ ] Evaluation detail view
  - [ ] New evaluation form
  - [ ] Real-time chat display
  - [ ] Progress indicators
  - [ ] Settings screen
- [ ] Add input handling similar to OpenCode's approach

#### 4.3 TUI Features
- [ ] Beautiful terminal interface with Lipgloss
- [ ] Keyboard navigation and shortcuts
- [ ] Real-time updates via WebSocket
- [ ] Configuration management
- [ ] Error handling and user feedback

### Phase 5: Additional SDKs & Frontends (Weeks 8-9)

#### 5.1 VSCode Extension
- [ ] Create `sdks/vscode/` extension package (following OpenCode pattern)
- [ ] Implement extension using TypeScript SDK from `packages/sdk/`
- [ ] Add evaluation management commands
- [ ] Create webview panels for evaluation results
- [ ] Add syntax highlighting for scenario files

#### 5.2 Pytest Plugin
- [ ] Create `pytest-plugin/` directory structure
- [ ] Implement pytest fixtures for Rogue client
- [ ] Add test helpers and utilities
- [ ] Create plugin packaging for PyPI
- [ ] Add documentation and examples

#### 5.3 Go SDK Completion
- [ ] Complete Go SDK implementation
- [ ] Add comprehensive tests
- [ ] Create Go module for easy import
- [ ] Add documentation and examples

### Phase 6: Testing & Documentation (Week 10)

#### 6.1 Comprehensive Testing
- [ ] Unit tests for all server components
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for complete workflows
- [ ] Performance testing for concurrent evaluations
- [ ] SDK integration tests

#### 6.2 Documentation
- [ ] API documentation with OpenAPI/Swagger
- [ ] SDK documentation for all languages
- [ ] Migration guide from legacy architecture
- [ ] Deployment and configuration guides
- [ ] Architecture decision records (ADRs)

#### 6.3 CI/CD Updates
- [ ] Update GitHub Actions workflows
- [ ] Add multi-language testing
- [ ] Set up SDK publishing pipelines
- [ ] Add Docker containerization
- [ ] Create deployment scripts

## API Specifications

### REST API Endpoints

#### Evaluation Management
```http
POST /api/v1/evaluations
Content-Type: application/json

{
  "agent_url": "http://localhost:3000",
  "auth_type": "no_auth",
  "auth_credentials": null,
  "scenarios": [...],
  "business_context": "...",
  "judge_llm": "openai/gpt-4",
  "judge_llm_api_key": "...",
  "deep_test_mode": false
}

Response: 201 Created
{
  "id": "eval_123",
  "status": "running",
  "created_at": "2024-01-01T00:00:00Z",
  "progress": 0.0
}
```

#### WebSocket Updates
```javascript
// Connect to evaluation updates
ws://localhost:8000/ws/evaluations/eval_123

// Message types
{
  "type": "status",
  "data": {"message": "Starting evaluation..."},
  "timestamp": "2024-01-01T00:00:00Z"
}

{
  "type": "progress", 
  "data": {"progress": 0.25, "current_scenario": "Don't reveal secrets"},
  "timestamp": "2024-01-01T00:00:00Z"
}

{
  "type": "chat",
  "data": {"role": "Evaluator Agent", "content": "Hello, can you help me?"},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## SDK Interfaces

### Python SDK
```python
from rogue_sdk import RogueClient, EvaluationRequest, Scenario

client = RogueClient("http://localhost:8000")

# Start evaluation
request = EvaluationRequest(
    agent_url="http://localhost:3000",
    scenarios=[Scenario(scenario="Don't reveal secrets")],
    business_context="Customer service bot",
    judge_llm="openai/gpt-4"
)

evaluation = await client.start_evaluation(request)

# Stream updates
async for update in client.stream_updates(evaluation.id):
    if update.type == "progress":
        print(f"Progress: {update.data['progress']:.1%}")
    elif update.type == "chat":
        print(f"{update.data['role']}: {update.data['content']}")

# Get results
results = await client.get_results(evaluation.id)
```

### Go SDK
```go
package main

import (
    "context"
    "github.com/your-org/rogue-go-sdk/client"
)

func main() {
    client := client.NewRogueClient("http://localhost:8000")
    
    req := client.EvaluationRequest{
        AgentURL: "http://localhost:3000",
        Scenarios: []client.Scenario{
            {Scenario: "Don't reveal secrets"},
        },
        BusinessContext: "Customer service bot",
        JudgeLLM: "openai/gpt-4",
    }
    
    eval, err := client.StartEvaluation(context.Background(), req)
    if err != nil {
        panic(err)
    }
    
    // Stream updates
    updates, err := client.StreamUpdates(context.Background(), eval.ID)
    for update := range updates {
        if update.Type == "progress" {
            fmt.Printf("Progress: %.1f%%\n", update.Data["progress"].(float64)*100)
        }
    }
}
```

## Migration Strategy

### Backward Compatibility
1. **Phase 1-3**: Keep existing CLI and UI working alongside new server
2. **Phase 4-6**: Add deprecation warnings to legacy components
3. **Post-launch**: Provide 6-month deprecation period before removing legacy code

### Data Migration
- Existing configuration files remain compatible
- Scenario files use same JSON format
- Results format unchanged for backward compatibility

### User Migration Path
1. **Immediate**: Users can continue using existing CLI/UI
2. **Gradual**: Users can opt-in to new server-based architecture
3. **Future**: Legacy components deprecated with clear migration path

## Risk Mitigation

### Technical Risks
- **ADK Agent Integration**: Extensive testing of process communication
- **WebSocket Stability**: Robust connection handling and reconnection logic
- **Concurrent Evaluations**: Thorough testing of resource management

### User Experience Risks
- **Feature Parity**: Ensure all existing features work in new architecture
- **Performance**: Maintain or improve evaluation performance
- **Learning Curve**: Comprehensive documentation and examples

### Deployment Risks
- **Backward Compatibility**: Extensive testing of legacy component compatibility
- **SDK Stability**: Comprehensive testing across all supported languages
- **Documentation**: Clear migration guides and troubleshooting

## Success Metrics

### Technical Metrics
- [ ] All existing functionality preserved
- [ ] API response times < 100ms for non-evaluation endpoints
- [ ] WebSocket connection stability > 99.9%
- [ ] Support for 10+ concurrent evaluations

### User Experience Metrics
- [ ] Zero breaking changes for existing users during transition
- [ ] New TUI provides superior user experience
- [ ] SDK adoption by external developers
- [ ] Reduced time-to-value for new integrations

### Development Metrics
- [ ] 90%+ test coverage across all components
- [ ] Complete API documentation
- [ ] SDK documentation for all languages
- [ ] Successful CI/CD pipeline for all components

## Timeline Summary

| Phase |  Key Deliverables |
|-------|------------------|
| Phase 1 |  FastAPI server, ADK integration, WebSocket support |
| Phase 2 |  Python SDK with full functionality |
| Phase 3 |  Refactored CLI and Gradio UI using SDK |
| Phase 4 |  Go SDK and Bubble Tea TUI |
| Phase 5 |  TypeScript SDK, pytest plugin |
| Phase 6 |  Testing, documentation, CI/CD |


## Next Steps

1. **Approval**: Review and approve this refactor plan
2. **Team Assignment**: Assign developers to each phase
3. **Environment Setup**: Set up development and testing environments
4. **Phase 1 Kickoff**: Begin FastAPI server implementation
5. **Regular Reviews**: Weekly progress reviews and plan adjustments

## Key Insights from OpenCode Architecture

Based on OpenCode's successful implementation, here are key architectural decisions to adopt:

### 1. **Monorepo with Packages**
- Use `packages/` directory for core components
- Each package has its own `package.json` and dependencies
- Shared TypeScript configuration across packages
- Workspace-based dependency management with Bun/npm

### 2. **FastAPI Server with TypeScript Frontends**
- Core server remains in Python with FastAPI (for ADK compatibility)
- TypeScript SDKs and frontends for modern developer experience
- OpenAPI/JSON Schema for automatic type generation
- Python async/await patterns with FastAPI's excellent async support

### 3. **Event Bus Architecture**
- Internal event bus for component communication
- Decoupled architecture with pub/sub patterns
- Better scalability and maintainability
- Real-time updates via WebSocket integration

### 4. **Go TUI with Embedded SDK**
- TUI package includes its own Go SDK in `packages/tui/sdk/`
- Self-contained binary with no external dependencies
- Follows Go best practices for CLI tools
- Input handling and terminal management

### 5. **Multiple SDK Strategies**
- Primary TypeScript SDK in `packages/sdk/`
- Language-specific SDKs in `sdks/` directory
- VSCode extension using primary SDK
- Clear separation between internal and external SDKs

### 6. **Python-First Server with Modern Frontends**
- FastAPI server maintains Python ecosystem compatibility
- Existing Python ADK agent works seamlessly
- Modern TypeScript/Go frontends communicate via HTTP/WebSocket
- Best of both worlds: Python ML/AI ecosystem + modern frontend tooling

### 7. **Hybrid Build Strategy**
- Python server: `uv` for dependency management and packaging
- Frontend packages: Modern JavaScript tooling (Bun, Vite, etc.)
- Go TUI: Standard Go build tools and cross-compilation
- Multiple distribution channels: PyPI (server), npm (SDK), Homebrew (TUI)

---

*This document will be updated as the refactor progresses and requirements evolve.*
