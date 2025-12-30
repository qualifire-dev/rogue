package evaluations

// FormState contains all data needed to render the evaluation form
type FormState struct {
	// Dimensions
	Width  int
	Height int

	// Form fields
	AgentURL       string
	Protocol       string
	Transport      string
	JudgeModel     string
	DeepTest       bool
	ServerURL      string
	ScenariosCount int
	EvaluationMode string
	ScanType       string // "basic", "full", or "custom" (only shown in Red Team mode)

	// Editing state
	// Policy mode: 0: AgentURL, 1: Protocol, 2: Transport, 3: JudgeModel, 4: DeepTest, 5: EvaluationMode, 6: StartButton
	// Red Team mode: 0: AgentURL, 1: Protocol, 2: Transport, 3: JudgeModel, 4: DeepTest, 5: EvaluationMode, 6: ScanType, 7: Configure, 8: StartButton
	CurrentField int
	CursorPos    int

	// UI state
	EvalSpinnerActive     bool
	HealthSpinnerActive   bool
	HealthSpinnerView     string
	RedTeamConfigSaved    bool   // Shows green banner when red team config is saved
	RedTeamConfigSavedMsg string // Custom message for the banner
}

// DetailState contains all data needed to render the evaluation detail screen
type DetailState struct {
	// Dimensions
	Width  int
	Height int

	// Status
	Status    string
	Progress  float64
	Completed bool

	// Evaluation mode
	EvaluationMode string

	// Focus state
	FocusedViewport int // 0: events, 1: summary

	// Spinner views (pre-rendered strings)
	EvalSpinnerActive    bool
	EvalSpinnerView      string
	SummarySpinnerActive bool
	SummarySpinnerView   string

	// Pre-rendered content from MessageHistoryView components
	EventsContent  string
	SummaryContent string
	HasSummary     bool
}
