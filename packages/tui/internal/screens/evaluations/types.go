package evaluations

// FormField represents the field indices for the evaluation form
// These constants mirror the EvalFormField constants in the tui package
// to avoid import cycles while maintaining consistency
type FormField int

const (
	FormFieldAgentURL FormField = iota
	FormFieldProtocol
	FormFieldTransport
	FormFieldJudgeModel
	FormFieldDeepTest
	FormFieldStartButton
)

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
	CurrentField int // Use FormField* constants for field indices
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
