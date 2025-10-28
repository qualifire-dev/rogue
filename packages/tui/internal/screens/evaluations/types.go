package evaluations

// FormState contains all data needed to render the evaluation form
type FormState struct {
	// Dimensions
	Width  int
	Height int

	// Form fields
	AgentURL       string
	JudgeModel     string
	DeepTest       bool
	ServerURL      string
	ScenariosCount int

	// Editing state
	CurrentField int // 0: AgentURL, 1: JudgeModel, 2: DeepTest, 3: StartButton
	CursorPos    int

	// UI state
	EvalSpinnerActive   bool
	HealthSpinnerActive bool
	HealthSpinnerView   string
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
