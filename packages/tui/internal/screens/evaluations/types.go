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

	// Editing state
	CurrentField int // 0: AgentURL, 1: Protocol, 2: Transport, 3: JudgeModel, 4: DeepTest, 5: StartButton
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
