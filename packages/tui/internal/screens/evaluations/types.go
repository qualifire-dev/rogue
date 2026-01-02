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
	FormFieldEvaluationMode
	// Policy mode start button / Red Team mode scan type (both at index 6)
	FormFieldStartButtonPolicy
	FormFieldConfigureButton    // 7 - Red Team mode only
	FormFieldStartButtonRedTeam // 8 - Red Team mode only
)

// FormFieldScanType is an alias - in Red Team mode, index 6 is the scan type field
const FormFieldScanType = FormFieldStartButtonPolicy

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
