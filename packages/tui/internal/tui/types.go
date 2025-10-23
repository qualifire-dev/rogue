package tui

import (
	"github.com/charmbracelet/bubbles/v2/table"
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/glamour"
	"github.com/rogue/tui/internal/components"
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
	scenarioEditor    ScenarioEditor
	detailedBreakdown []table.Row

	// Spinners for loading states
	healthSpinner  components.Spinner
	summarySpinner components.Spinner
	evalSpinner    components.Spinner

	// Viewports for scrollable content
	eventsHistory   *components.MessageHistoryView
	summaryHistory  *components.MessageHistoryView
	reportHistory   *components.MessageHistoryView
	helpViewport    components.Viewport
	focusedViewport int // 0 = events, 1 = summary

	// Markdown renderer with caching
	markdownRenderer    *glamour.TermRenderer
	rendererCachedWidth int
	rendererCachedTheme string

	// /eval state
	evalState *EvaluationViewState

	// Configuration state
	configState *ConfigState
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

// Config represents application configuration
type Config struct {
	ServerURL               string            `toml:"server_url"`
	Theme                   string            `toml:"theme"`
	APIKeys                 map[string]string `toml:"api_keys"`
	SelectedModel           string            `toml:"selected_model"`
	SelectedProvider        string            `toml:"selected_provider"`
	InterviewModel          string            `toml:"interview_model"`
	InterviewProvider       string            `toml:"interview_provider"`
	QualifireAPIKey         string            `toml:"qualifire_api_key"`
	QualifireEnabled        bool              `toml:"qualifire_enabled"`
	DontShowQualifirePrompt bool              `toml:"dont_show_qualifire_prompt"`
}

// ConfigField represents different configuration fields
type ConfigField int

const (
	ConfigFieldServerURL ConfigField = iota
	ConfigFieldTheme
	ConfigFieldQualifire
)

// ConfigState represents the configuration screen state
type ConfigState struct {
	ActiveField      ConfigField
	ServerURL        string
	CursorPos        int
	ThemeIndex       int
	IsEditing        bool
	HasChanges       bool
	QualifireEnabled bool
}

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

// EvaluationViewState represents the state for evaluation screens
type EvaluationViewState struct {
	ServerURL    string // Used from config, not editable in form
	AgentURL     string
	JudgeModel   string
	ParallelRuns int
	DeepTest     bool
	Scenarios    []EvalScenario

	// Runtime
	Running  bool
	Progress float64
	Status   string
	Events   []EvaluationEvent
	cancelFn func() error

	// Report generation
	Summary           string // Generated markdown summary
	JobID             string // For tracking the evaluation job
	Completed         bool   // Whether evaluation finished successfully
	SummaryGenerated  bool   // Whether summary generation was already attempted
	StructuredSummary StructuredSummary

	// Editing state for New Evaluation
	currentField int // 0: AgentURL, 1: JudgeModel, 2: DeepTest, 3: StartButton
	cursorPos    int // rune index in current text field
}
