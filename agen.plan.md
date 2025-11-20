<!-- 376e89fc-567a-41e7-8e53-3e4ef89b1656 de0f7188-f7bf-4939-87d9-417a0ac09a75 -->
# Rogue → Agentic Red Teaming Pivot Implementation Plan

## Architecture Principles

✅ **Server-side intelligence**: All red teaming logic lives in `rogue/server/`

✅ **Thin clients**: TUI/CLI/Web UI only handle mode selection and display

✅ **Unified API**: Single `/api/v1/evaluations` endpoint supports both modes

✅ **Backward compatible**: Existing clients work without changes (defaults to policy mode)

✅ **Streaming support**: WebSocket updates work for both modes

✅ **Scenario-driven**: Pre-baked, business-context-aware, multi-step attack scenarios

## Phase 1: Server-Side Attack Library Foundation

### 1.1 Create Red Teaming Module Structure

Create `rogue/server/red_teaming/` with:

- `attacks/` - Port single-turn and multi-turn attacks from deepteam
- `vulnerabilities/` - Port vulnerability detection logic
- `frameworks/owasp/` - OWASP Top 10 categories (start with LLM_01, LLM_06, LLM_07)
- `metrics/` - Red teaming evaluation metrics

**Port from deepteam (independence approach)**:

- `deepteam/attacks/base_attack.py` → `rogue/server/red_teaming/attacks/base_attack.py`
- `deepteam/attacks/single_turn/*.py` → `rogue/server/red_teaming/attacks/single_turn/`
- `deepteam/vulnerabilities/*.py` → `rogue/server/red_teaming/vulnerabilities/`
- `deepteam/frameworks/owasp/*.py` → `rogue/server/red_teaming/frameworks/owasp/`

Remove deepeval dependencies, adapt to use Rogue's LLM infrastructure.

### 1.2 Port Priority Attack Classes

**Single-turn** (for LLM_01, LLM_06, LLM_07):

- PromptInjection, PromptProbing, Base64, ROT13, Leetspeak, Roleplay, GrayBox

**Multi-turn strategies metadata**:

- LinearJailbreaking, CrescendoJailbreaking, TreeJailbreaking patterns
- Convert to natural conversation guidelines (not static prompts)

### 1.3 Port Priority Vulnerabilities

- PromptLeakage, ExcessiveAgency, Robustness, RBAC, BOLA, BFLA

## Phase 2: Server-Side Red Team Agent

### 2.1 Create RedTeamEvaluatorAgent (Scenario-Driven)

Create `rogue/evaluator_agent/red_team_a2a_evaluator_agent.py` and `red_team_mcp_evaluator_agent.py`:

- Extends `A2AEvaluatorAgent` / `MCPEvaluatorAgent`
- New instruction template: `RED_TEAM_AGENT_INSTRUCTIONS` (scenario-driven)
- **Scenario-based execution**: Follows pre-baked multi-step attack scenarios
- **New tools for scenario management**:
  - `get_current_scenario()`: Get active scenario for conversation
  - `get_scenario_steps()`: Get remaining attack steps
  - `mark_step_complete()`: Track step progress and results
  - `apply_attack_technique()`: Apply specific attack class when scenario specifies
- **Scenario tracking**: Tracks current scenario, step progress, and attack results per conversation
- **Removes random attack enhancement**: Replaced with scenario-driven execution
- Focuses on adversarial conversations following structured attack plans

### 2.2 Update Evaluator Factory

Modify `rogue/evaluator_agent/evaluator_agent_factory.py`:

- Route based on `evaluation_mode` parameter
- Load OWASP attacks for selected categories
- Instantiate appropriate agent class

### 2.3 Create Red Team Scenario Generator (Enhanced)

Create `rogue/server/services/red_team_scenario_generator.py`:

- **LLM-based generation**: Uses LLM to generate business-context-aware scenarios
- **Multi-step attack flows**: Each scenario includes structured conversation steps
- **Attack technique specification**: Scenarios specify which attack classes to use
- **Vulnerability indicators**: Define what responses indicate vulnerabilities
- **Escalation paths**: Success/failure paths for multi-step attacks
- Returns enhanced `RedTeamScenario` objects compatible with evaluation pipeline

**Scenario Structure**:
- `attack_steps`: Ordered list of attack steps with descriptions
- `attack_techniques`: List of attack class names (e.g., ["PromptInjection", "Base64"])
- `vulnerability_indicators`: What to look for in responses
- `business_context_applied`: How scenario applies to business context

## Phase 3: Server API & SDK Updates

### 3.1 Update SDK Types

Add to `rogue_sdk/types.py`:

- `EvaluationMode` enum (POLICY, RED_TEAM)
- `AgentConfig.evaluation_mode` field
- `AgentConfig.owasp_categories` field
- `AgentConfig.attacks_per_category` field
- `RedTeamingResult` model
- `EvaluationResults.red_teaming_results` field
- `EvaluationResults.owasp_summary` field

**New Enhanced Scenario Models** (for red teaming):
- `AttackStep` model: Single step in multi-step attack
  - `step_number`, `description`, `attack_technique`, `expected_response_pattern`
  - `escalation_if_successful`, `escalation_if_failed`
- `RedTeamScenario` model (extends `Scenario`):
  - `attack_steps`: List of `AttackStep` objects
  - `attack_techniques`: List of attack class names
  - `vulnerability_indicators`: List of vulnerability patterns
  - `business_context_applied`: How scenario applies to business context
  - `owasp_category`: OWASP category ID

### 3.2 Update ScenarioEvaluationService

Modify `rogue/server/services/scenario_evaluation_service.py`:

- Accept `evaluation_mode` and `owasp_categories` params
- Generate scenarios if red team mode and none provided
- Route to appropriate evaluator agent

### 3.3 Update EvaluationLibrary

Modify `rogue/server/services/evaluation_library.py`:

- Route based on evaluation mode
- Create `RedTeamEvaluationLibrary` for red team path

### 3.4 Verify API Backward Compatibility

Existing endpoint at `rogue/server/api/evaluation.py` works unchanged:

- Just passes new fields through to services
- Defaults to policy mode if not specified

## Phase 4: Client Updates (Thin Layer)

### 4.1 CLI Updates

Update `rogue/run_cli.py`:

- Add `--mode` argument (policy|red-team)
- Add `--owasp-categories` argument
- Build request payload with new fields
- Send to server API (server does all work)

### 4.2 Web UI Updates

Update `rogue/ui/app.py`:

- Add mode selector (Radio: Policy Testing | Red Teaming)
- Show OWASP category checkboxes when red team selected
- Build request with evaluation_mode field
- Display red teaming results differently

### 4.3 TUI Updates (Enhanced Visual Mode Switch)

The Go TUI at `packages/tui/` gets a prominent visual mode switcher with theme changes:

**Main Dashboard Model Updates** (`packages/tui/internal/screens/dashboard/model.go`):

- Add `evaluationMode` field (policy | red_team)
- Add `EvaluationMode` type with constants
- Default to policy mode
- Handle Tab key to toggle mode
- Persist mode in state

**View Updates** (`packages/tui/internal/screens/dashboard/view.go`):

- Add mode indicator badge at top of dashboard
  - Policy Mode: `[🛡️  POLICY TESTING]` in blue/purple
  - Red Team Mode: `[🔴 RED TEAM MODE]` in red
- Pass current theme based on mode
- Update instructions text based on mode
- Apply theme-aware styling throughout

**Theme System** (`packages/tui/internal/theme/`):

- Create `RedTeamTheme()` function returning red-accented theme:
  - Primary: `#DC2626` (red-600)
  - Secondary: `#F97316` (orange-500)
  - Success: `#10B981` (green-500, unchanged)
  - Warning: `#FCA5A5` (red-300)
  - Danger: `#7F1D1D` (red-900)
  - Background: Darker tones
- Keep existing `DefaultTheme()` for policy mode
- Both themes maintain good contrast for readability

**Key Binding Updates**:

- Tab: Toggle between policy and red team modes
- Visual feedback when mode switches
- Mode persists during session

**Config Updates**:

- Add `EvaluationMode` to config struct
- Add `OWASPCategories []string` field
- Save mode preference to config file
- Send mode in HTTP request to server API

**Visual Design**:

```
Policy Mode (Blue theme):
┌────────────────────────────────────┐
│   [🛡️  POLICY TESTING]             │
│                                    │
│        ROGUE LOGO (Blue)           │
│                                    │
└────────────────────────────────────┘

Red Team Mode (Red theme):
┌────────────────────────────────────┐
│   [🔴 RED TEAM MODE]               │
│                                    │
│        ROGUE LOGO (Red)            │
│                                    │
└────────────────────────────────────┘
```

## Phase 5: Scenario-Driven Red Teaming Implementation

### 5.1 Enhanced Scenario Generation

**LLM-Based Scenario Generation** (`rogue/server/services/red_team_scenario_generator.py`):

- Create `RED_TEAM_SCENARIO_GENERATION_PROMPT` template
- Generate business-context-aware scenarios per OWASP category
- Each scenario includes:
  - Multi-step attack flow (3-5 steps)
  - Attack technique specifications
  - Vulnerability indicators
  - Escalation paths (success/failure)
- Use `LLMService` for generation
- Parse LLM output into structured `RedTeamScenario` objects
- Map attack technique names to attack class instances

### 5.2 Scenario Tracking System

**Create `ScenarioTracker` class** (inside red team evaluator agents):

- Track current scenario per conversation context
- Track current step number and progress
- Track completed steps and results
- Track attack techniques used
- Track vulnerability indicators detected

### 5.3 Red Team Agent Tools

**Add new tools to red team evaluator agents**:

1. `get_current_scenario(context_id: str) -> dict`
   - Returns active scenario with all attack steps
   - Includes attack techniques and vulnerability indicators

2. `get_scenario_steps(context_id: str) -> List[dict]`
   - Returns remaining attack steps for current scenario
   - Helps agent know what to do next

3. `mark_step_complete(context_id: str, step_number: int, result: str) -> dict`
   - Marks attack step as complete
   - Records result (success/failure/vulnerability found)
   - Returns next step to execute

4. `apply_attack_technique(message: str, technique: str) -> str`
   - Applies specific attack technique to message
   - Uses attack classes (PromptInjection, Base64, etc.)
   - Returns enhanced message

### 5.4 Update Agent Instructions

**Rewrite `RED_TEAM_AGENT_INSTRUCTIONS`**:

- Emphasize scenario-driven approach
- Guide agents to use `get_current_scenario()` to understand objectives
- Guide agents to use `get_scenario_steps()` to see next steps
- Guide agents to execute steps in order, but adapt naturally
- Guide agents to use `apply_attack_technique()` when scenario specifies
- Guide agents to escalate based on scenario's escalation paths
- Guide agents to log vulnerabilities when indicators are detected

### 5.5 Replace Random Enhancement with Scenario Execution

**Remove random attack enhancement**:

- Remove `_select_and_enhance_attack()` method (70% random probability)
- Create `_execute_scenario_step()` method
- Update `_send_message_to_evaluated_agent()` to use scenario execution
- Implement step-by-step attack flow following scenario structure
- Attack enhancement only happens when scenario specifies it

## Phase 6: Red Teaming Reporting

### 6.1 Create Report Generator

Create `rogue/server/red_teaming/report_generator.py`:

- `OWASPComplianceReport` class for generating compliance reports
- Executive summary with vulnerability counts
- Attack success/failure breakdown per OWASP category
- Reproduction steps per finding (from scenario steps)
- Severity ratings and OWASP compliance scores
- Remediation recommendations
- Markdown report generation

### 6.2 Update Report Formats

Extend existing markdown report generation:

- Add OWASP section with category results
- Include attack method details from scenarios
- Map findings to OWASP categories
- Show scenario-based attack flows
- Include vulnerability indicators detected

## Phase 7: Documentation & Examples

### 7.1 Update README Positioning

Change tagline to emphasize security:

- "Agentic security scanner with automated red teaming"
- Highlight OWASP Top 10 support
- Emphasize agent-vs-agent adversarial testing
- Highlight scenario-driven multi-step attack testing

### 7.2 Create Red Teaming Example

Add `examples/red_team_tshirt_store/`:

- Demonstrate scenario-driven attacks against t-shirt agent
- Show LLM_01, LLM_06, LLM_07 vulnerabilities
- Include multi-step attack scenarios
- Show scenario execution flow
- Include remediation guide

### 7.3 Create OWASP Documentation

Add `docs/OWASP_TOP_10.md`:

- Explain each implemented category
- List available attack methods
- Show example multi-step attack scenarios
- Explain scenario-driven approach
- Roadmap for remaining categories

### 7.4 Create Scenario-Driven Implementation Guide

Add `docs/RED_TEAM_SCENARIO_DRIVEN_PLAN.md`:

- Detailed implementation plan for scenario-driven approach
- Architecture changes and benefits
- Example scenario structures
- Migration notes from random enhancement

## Implementation Todos

Each phase builds on the previous, following the server-first architecture.

### To-dos

**Phase 1: Foundation** ✅
- [x] Port deepteam attack classes (base, single-turn, multi-turn) to rogue/red_teaming/
- [x] Port vulnerability classes (PromptLeakage, ExcessiveAgency, RBAC, etc.)
- [x] Port OWASP framework structure and risk categories for LLM_01, LLM_06, LLM_07

**Phase 2: Red Team Agents** ✅
- [x] Create RedTeamEvaluatorAgent with adversarial instruction template
- [x] Integrate attack strategies into agent conversation flow naturally
- [x] Update evaluator_agent_factory to route between policy/red-team modes

**Phase 3: SDK & API** ✅
- [x] Add EvaluationMode enum and update AgentConfig in SDK types
- [x] Create RedTeamingResult schema and OWASP compliance report generator
- [x] Update scenario evaluation service to support red team mode

**Phase 4: Client Updates** ✅
- [x] Add mode selection to TUI, CLI, and Web UI

**Phase 5: Scenario-Driven Implementation** 🔄
- [ ] Define enhanced scenario models (AttackStep, RedTeamScenario) in SDK types
- [ ] Create LLM scenario generation prompt template
- [ ] Enhance RedTeamScenarioGenerator with LLM-based generation
- [ ] Implement ScenarioTracker class for tracking scenario execution
- [ ] Add new tools to red team agents (get_current_scenario, get_scenario_steps, mark_step_complete, apply_attack_technique)
- [ ] Update RED_TEAM_AGENT_INSTRUCTIONS for scenario-driven approach
- [ ] Replace random attack enhancement with scenario-driven execution
- [ ] Update scenario evaluation flow to use enhanced scenarios

**Phase 6: Reporting** ✅
- [x] Create OWASP compliance report generator
- [ ] Update report formats to include scenario-based attack flows

**Phase 7: Documentation** 🔄
- [ ] Update README positioning and create OWASP documentation
- [ ] Create red teaming example showing scenario-driven attacks against t-shirt store
- [ ] Create scenario-driven implementation guide documentation
