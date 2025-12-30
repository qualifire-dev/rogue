package tui

import (
	"github.com/charmbracelet/bubbles/v2/table"
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/glamour"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/screens/config"
	"github.com/rogue/tui/internal/screens/redteam"
	"github.com/rogue/tui/internal/screens/scenarios"
)

// AutoRefreshMsg is sent periodically to refresh the evaluation screen
type AutoRefreshMsg struct{}

// HealthCheckResultMsg contains the result of a health check
type HealthCheckResultMsg struct {
	Status string
	Err    error
}

// StartEvaluationMsg signals to start the evaluation
type StartEvaluationMsg struct{}

// SummaryGeneratedMsg contains the result of summary generation
type SummaryGeneratedMsg struct {
	Summary string
	Err     error
}

// RedTeamReportFetchedMsg contains the result of red team report fetch
type RedTeamReportFetchedMsg struct {
	ReportData interface{}
	Err        error
}

// Screen represents different screens in the TUI
type Screen int

const (
	DashboardScreen Screen = iota
	EvaluationsScreen
	EvaluationDetailScreen
	NewEvaluationScreen
	ReportScreen
	InterviewScreen
	ConfigurationScreen
	ScenariosScreen
	HelpScreen
	RedTeamConfigScreen
	RedTeamReportScreen
)

// App represents the main TUI application
type App struct {
	program *tea.Program
}

// Model represents the main application state
type Model struct {
	currentScreen     Screen
	width             int
	height            int
	input             string
	cursor            int
	evaluations       []Evaluation
	scenarios         []Scenario
	config            Config
	version           string
	commandInput      components.CommandInput
	dialog            *components.Dialog
	dialogStack       []components.Dialog
	llmDialog         *components.LLMConfigDialog
	scenarioEditor    scenarios.ScenarioEditor
	detailedBreakdown []table.Row

	// Spinners for loading states
	healthSpinner  components.Spinner
	summarySpinner components.Spinner
	evalSpinner    components.Spinner

	// Viewports for scrollable content
	eventsHistory         *components.MessageHistoryView
	summaryHistory        *components.MessageHistoryView
	reportHistory         *components.MessageHistoryView
	helpViewport          components.Viewport
	redTeamReportViewport components.Viewport
	focusedViewport       int // 0 = events, 1 = summary

	// Markdown renderer with caching
	markdownRenderer    *glamour.TermRenderer
	rendererCachedWidth int
	rendererCachedTheme string

	// Report caching
	cachedReportSummary string // Tracks the summary that was last rendered

	// /eval state
	evalState *EvaluationViewState

	// Configuration state
	configState *ConfigState

	// Red Team Config state
	redTeamConfigState *redteam.RedTeamConfigState

	// Red Team Report state
	redTeamReportData interface{} // Will hold JSON report data from Python
}

// Evaluation represents an evaluation
type Evaluation struct {
	ID     string
	Status string
	Agent  string
}

// Scenario represents a test scenario
type Scenario struct {
	ID          string
	Name        string
	Description string
}

// Type aliases for config package types
type Config = config.Config
type ConfigState = config.ConfigState
type ConfigField = config.ConfigField

// Re-export constants
const (
	ConfigFieldServerURL = config.ConfigFieldServerURL
	ConfigFieldTheme     = config.ConfigFieldTheme
	ConfigFieldQualifire = config.ConfigFieldQualifire
)

// EvalScenario represents a single evaluation scenario
type EvalScenario struct {
	Scenario        string `json:"scenario"`
	ScenarioType    string `json:"scenario_type"`
	ExpectedOutcome string `json:"expected_outcome,omitempty"`
}

// EvaluationEvent represents an event during evaluation
type EvaluationEvent struct {
	Type     string  `json:"type"`
	Status   string  `json:"status,omitempty"`
	Progress float64 `json:"progress,omitempty"`
	Role     string  `json:"role,omitempty"`
	Content  string  `json:"content,omitempty"`
	Message  string  `json:"message,omitempty"`
	JobID    string  `json:"job_id,omitempty"`
	Data     any     `json:"data,omitempty"`
}

// StructuredSummary represents a structured evaluation summary
type StructuredSummary struct {
	OverallSummary    string   `json:"overall_summary"`
	KeyFindings       []string `json:"key_findings"`
	Recommendations   []string `json:"recommendations"`
	DetailedBreakdown []struct {
		Scenario string `json:"scenario"`
		Status   string `json:"status"`
		Outcome  string `json:"outcome"`
	} `json:"detailed_breakdown"`
}

// Note: EvaluationViewState is now defined in eval_types.go with Protocol/Transport fields
